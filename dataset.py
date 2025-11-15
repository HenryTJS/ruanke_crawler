import re
import pandas as pd
import os
from data import finduniv, ry, rr, rv, change, base_dir
from function import remove, univdata2, univdata, listname, save_to_database


def rank():
    rank_data = []
    for index in [0, 3]:
        path_url = os.path.join(base_dir, 'rankings', str(rv[index]), str(ry[index]), 'payload.js')
        with open(path_url, 'r', encoding='utf-8') as file:
            text = file.read()
        namelist = listname(index, text)
        find_univ_pattern = re.compile(rr[index][3])
        
        rank_list = []
        for k, d in enumerate(namelist[0]):
            if '总榜' in namelist[1][k] or '名单' in namelist[1][k]:
                continue
                
            univ = univdata(ry[index], index, d, find_univ_pattern)
            df_selected = univ[['univNameCn', 'score', 'ranking']].rename(
                columns={'univNameCn': '中文名称', 'score': '得分', 'ranking': '排名'}
            )
            df_selected['排名类型'] = namelist[1][k]
            rank_list.append(df_selected)
        
        rank_data.append(pd.concat(rank_list, ignore_index=True).dropna())
    
    return pd.concat(rank_data, ignore_index=True)

def subject():
    index = 1
    path_url = os.path.join(base_dir, 'rankings', str(rv[index]), str(ry[index]), 'payload.js')
    with open(path_url, 'r', encoding='utf-8') as file:
        text = file.read()
    namelist = listname(index, text)
    find_univ_pattern = re.compile(rr[index][3])
    
    subject_list = []
    for k, d in enumerate(namelist[0]):
        univ = univdata(ry[index], index, d, find_univ_pattern)
        df_selected = univ[['univNameCn', 'score', 'rankPctTop']].rename(
            columns={'univNameCn': '中文名称', 'score': '得分', 'rankPctTop': '层次'}
        )
        df_selected['学科'] = namelist[1][k]
        subject_list.append(df_selected)
    
    return pd.concat(subject_list, ignore_index=True).dropna()

def major():
    index = 2
    path_url = os.path.join(base_dir, 'rankings', str(rv[index]), str(ry[index]), 'payload.js')
    with open(path_url, 'r', encoding='utf-8') as file:
        text = file.read()
    namelist = listname(index, text)
    find_univ_pattern = re.compile(rr[index][3])

    major_list = []
    for k, d in enumerate(namelist[0]):
        univ = univdata(ry[index], index, d, find_univ_pattern)
        df_selected = univ[['univNameCn', 'score', 'grade']].rename(
            columns={'univNameCn': '中文名称', 'score': '得分', 'grade': '评级'}
        )
        df_selected['专业'] = namelist[1][k]
        major_list.append(df_selected)
    
    return pd.concat(major_list, ignore_index=True).dropna()


def main():
    jsfilepath = os.path.join(base_dir, 'institution', 'payload.js')
    with open(jsfilepath, 'r', encoding='utf-8') as file:
        text = file.read()
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
    
    indices_to_drop = []
    for idx in df_sorted.index[::-1]:
        row = df_sorted.loc[idx]
        
        if pd.isna(row['院校代码']) or row['院校代码'] == '':
            old_name = row['中文名称']
            
            new_name = change.get(old_name)
            new_name_rows = df_sorted[df_sorted['中文名称'] == new_name]
            new_name_row_idx = new_name_rows.index[0]
            
            for col in df_sorted.columns:
                if col == '中文名称':
                    df_sorted.loc[new_name_row_idx, col] = new_name
                elif pd.isna(df_sorted.loc[new_name_row_idx, col]) or df_sorted.loc[new_name_row_idx, col] == '':
                    if pd.notna(row[col]) and row[col] != '':
                        df_sorted.loc[new_name_row_idx, col] = row[col]
            
            indices_to_drop.append(idx)
    
    if indices_to_drop:
        df_sorted = df_sorted.drop(indices_to_drop)
        df_sorted = df_sorted.reset_index(drop=True)
    
    db_path = '中国大学数据集.db'
    save_to_database(df_sorted, db_path, 'universities')
    save_to_database(subject(), db_path,'subjects')
    save_to_database(major(), db_path,'majors')


if __name__ == "__main__":
    main()