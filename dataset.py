import requests
import re
import pandas as pd
import numpy as np
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


def _classify_levels(level, classification_type):
    if classification_type == 'subject':
        if level in {'前2名', '前3%'}:
            return ('顶尖学科', '一流学科', '上榜学科')
        elif level in {'前2名', '前3名', '前3%', '前7%', '前12%'}:
            return (None, '一流学科', '上榜学科')
        return (None, None, '上榜学科')
    elif classification_type == 'major':
        if level in {'A+'}:
            return ('A+专业', 'A类专业', '上榜专业')
        elif level in {'A+', 'A'}:
            return (None, 'A类专业', '上榜专业')
        elif level in {'A+', 'A', 'B+', 'B'}:
            return (None, None, '上榜专业')
        return (None, None, None)
    return (None, None, None)


def process_classification_data(index, classification_type):
    path_url = f'https://www.shanghairanking.cn/_nuxt/static/{number}/rankings/{rv[index]}/{ry[index][-1]}/payload.js'
    text = requests.get(path_url).text
    namelist = listname(index, text)
    find_univ_pattern = re.compile(rr[index][3])
    
    data_list = []
    for _, d in enumerate(namelist[0]):
        univ = univdata(ry[index][-1], index, d, find_univ_pattern)
        
        if classification_type == 'subject':
            selected_columns = ['univNameCn', 'rankPctTop']
            new_column_names = ['中文名称', '层次']
        else:
            selected_columns = ['univNameCn', 'grade']
            new_column_names = ['中文名称', '评级']
            
        df_selected = univ[selected_columns].rename(columns=dict(zip(selected_columns, new_column_names)))
        data_list.append(df_selected)
    
    all_universities = set()
    for df in data_list:
        all_universities.update(df['中文名称'].unique())
    
    if classification_type == 'subject':
        columns = ['顶尖学科', '一流学科', '上榜学科']
    else:
        columns = ['A+专业', 'A类专业', '上榜专业']
    
    result_df = pd.DataFrame(
        np.zeros((len(all_universities), len(columns)), dtype=int),
        index=list(all_universities),
        columns=columns
    )
    
    for df in data_list:
        for _, row in df.iterrows():
            uni = row['中文名称']
            level = row['层次' if classification_type == 'subject' else '评级']
            classifications = _classify_levels(level, classification_type)
            
            for col, val in zip(columns, classifications):
                if val:
                    result_df.loc[uni, col] += 1
    
    return result_df.reset_index().rename(columns={'index': '中文名称'}).replace(0, None)


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
    merged_df = pd.merge(merged_df, process_classification_data(1, 'subject'), on='中文名称', how='outer')
    merged_df = pd.merge(merged_df, process_classification_data(2, 'major'), on='中文名称', how='outer')
    df_sorted = merged_df.sort_values(by='院校代码')
    
    db_path = '中国大学数据集.db'
    save_to_database(df_sorted, db_path, 'universities')


if __name__ == "__main__":
    main()