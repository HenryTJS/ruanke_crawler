import requests
import re
import pandas as pd
from data import number, finduniv, ry, rr, rv, change
from function import remove, univdata2, univdata, listname, save_to_database


def _fetch_rank_data(index):
    path_url = f'https://www.shanghairanking.cn/_nuxt/static/{number}/rankings/{rv[index]}/{ry[index][-1]}/payload.js'
    text = requests.get(path_url).text
    namelist = listname(index, text)
    find_univ_pattern = re.compile(rr[index][3])
    
    rank_list = []
    for k, d in enumerate(namelist[0]):
        if '总榜' in namelist[1][k] or '名单' in namelist[1][k]:
            continue
            
        univ = univdata(ry[index][-1], index, d, find_univ_pattern)
        df_selected = univ[['univNameCn', 'score', 'ranking']].rename(
            columns={'univNameCn': '中文名称', 'score': '得分', 'ranking': '排名'}
        )
        df_selected['排名类型'] = namelist[1][k]
        rank_list.append(df_selected)
    
    return pd.concat(rank_list, ignore_index=True).dropna()


def rank():
    rank_data = [_fetch_rank_data(i) for i in [0, 3]]
    return pd.concat(rank_data, ignore_index=True)


def main():
    jsfilepath = f'https://www.shanghairanking.cn/_nuxt/static/{number}/institution/payload.js'
    text = requests.get(jsfilepath).text
    univ = re.findall(finduniv, text)[0]
    univ_data = remove(7, univdata2(univ, text))
    univ_data = univ_data.applymap(
        lambda v: pd.NA if isinstance(v, str) and (v.strip() == '' or v.strip().lower() == 'null') else v
    )
    
    univ_data["办学层次"] = univ_data["办学层次"].replace({
        "10": "普通本科",
        "15": "职业本科",
        "20": "高职（专科）"
    })
    
    merged_df = pd.merge(univ_data, rank(), on='中文名称', how='outer')
    df_sorted = merged_df.sort_values(by='院校代码')
    
    # 从最后一行开始处理院校代码为空的行
    indices_to_drop = []
    for idx in df_sorted.index[::-1]:  # 从最后一行开始
        row = df_sorted.loc[idx]
        
        # 检查院校代码是否为空
        if pd.isna(row['院校代码']) or row['院校代码'] == '':
            old_name = row['中文名称']
            
            # 直接查找其中文名称在change数组中对应更名后的大学名
            new_name = change.get(old_name)
            
            if new_name:
                # 查找新名称对应的行（应该有院校代码）
                new_name_rows = df_sorted[df_sorted['中文名称'] == new_name]
                
                if not new_name_rows.empty:
                    # 找到新名称对应的行（优先选择有院校代码的行）
                    new_name_row_idx = new_name_rows.index[0]
                    new_name_row = df_sorted.loc[new_name_row_idx]
                    
                    # 合并数据：优先使用新名称行的数据，但确保中文名称是新名称
                    for col in df_sorted.columns:
                        if col == '中文名称':
                            df_sorted.loc[new_name_row_idx, col] = new_name
                        elif pd.isna(df_sorted.loc[new_name_row_idx, col]) or df_sorted.loc[new_name_row_idx, col] == '':
                            # 如果新名称行的该列为空，使用旧名称行的值
                            if pd.notna(row[col]) and row[col] != '':
                                df_sorted.loc[new_name_row_idx, col] = row[col]
                    
                    # 标记旧名称行需要删除
                    indices_to_drop.append(idx)
    
    # 删除已合并的旧名称行
    if indices_to_drop:
        df_sorted = df_sorted.drop(indices_to_drop)
        df_sorted = df_sorted.reset_index(drop=True)
    
    db_path = '中国大学数据集.db'
    save_to_database(df_sorted, db_path, 'universities')


if __name__ == "__main__":
    main()