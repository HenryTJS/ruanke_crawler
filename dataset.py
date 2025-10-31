import requests
import re
import pandas as pd
from data import number, finduniv, ry, rr, rv
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
        df_selected = univ[['univNameCn', 'score']].rename(
            columns={'univNameCn': '中文名称', 'score': '得分'}
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
    
    univ_data["办学层次"] = univ_data["办学层次"].replace({
        "10": "普通本科",
        "15": "职业本科",
        "20": "高职（专科）"
    })
    
    merged_df = pd.merge(univ_data, rank(), on='中文名称', how='outer')
    df_sorted = merged_df.sort_values(by='院校代码')
    
    db_path = '中国大学数据集.db'
    save_to_database(df_sorted, db_path, 'universities')


if __name__ == "__main__":
    main()