# 中国大学数据爬取主函数程序

import requests
import re
import pandas as pd
import numpy as np
from data import number, finduniv, ry, rr, rv
from function import remove, univdata2, univdata, listname

def rank():
    ranklist = []
    for i in [0, 3]:
        path_url = f'https://www.shanghairanking.cn/_nuxt/static/{number}/rankings/{rv[i]}/{ry[i][-1]}/payload.js'
        text = requests.get(path_url).text
        namelist = listname(i, text)
        finduniv = re.compile(rr[i][3])
        for k, d in enumerate(namelist[0]):
            if '总榜' in namelist[1][k] or '名单' in namelist[1][k]:
                continue
            univ = univdata(ry[i][-1], i, d, finduniv)
            selected_columns = ['univNameCn', 'score']
            new_column_names = ['中文名称', '得分']
            df_selected = univ[selected_columns]
            df_selected.columns = new_column_names
            df_selected['排名类型'] = namelist[1][k]
            ranklist.append(df_selected)
    result = pd.concat(ranklist, ignore_index=True).dropna()
    return result

def classify_subject(level):
    if level in {'前2名', '前3%'}:
        return ('顶尖学科', '一流学科', '上榜学科')
    elif level in {'前2名', '前3名', '前3%', '前7%', '前12%'}:
        return (None, '一流学科', '上榜学科')
    else:
        return (None, None, '上榜学科')

def classify_major(level):
    if level in {'A+'}:
        return ('A+专业', 'A类专业', '上榜专业')
    elif level in {'A+', 'A'}:
        return (None, 'A类专业', '上榜专业')
    elif level in {'A+', 'A', 'B+', 'B'}:
        return (None, None, '上榜专业')
    else:
        return (None, None, None)

def num1():
    numlist = []
    path_url = f'https://www.shanghairanking.cn/_nuxt/static/{number}/rankings/{rv[1]}/{ry[1][-1]}/payload.js'
    text = requests.get(path_url).text
    namelist = listname(1, text)
    finduniv = re.compile(rr[1][3])
    for _, d in enumerate(namelist[0]):
        univ = univdata(ry[1][-1], 1, d, finduniv)
        selected_columns = ['univNameCn', 'rankPctTop']
        new_column_names = ['中文名称', '层次']
        df_selected = univ[selected_columns]
        df_selected.columns = new_column_names
        numlist.append(df_selected)
    universities = set()
    for df in numlist:
        universities.update(df['中文名称'].unique())
    data = pd.DataFrame(
        np.zeros((len(universities), 3), dtype=int),
        index=list(universities),
        columns=['顶尖学科', '一流学科', '上榜学科']
    )
    for df in numlist:
        for _, row in df.iterrows():
            uni = row['中文名称']
            level = row['层次']
            top, first, listed = classify_subject(level)
            if top:
                data.loc[uni, '顶尖学科'] += 1
            if first:
                data.loc[uni, '一流学科'] += 1
            if listed:
                data.loc[uni, '上榜学科'] += 1
    data = data.reset_index()
    data.columns = ['中文名称', '顶尖学科', '一流学科', '上榜学科']
    data = data.replace(0, None)
    return data

def num2():
    numlist = []
    path_url = f'https://www.shanghairanking.cn/_nuxt/static/{number}/rankings/{rv[2]}/{ry[2][-1]}/payload.js'
    text = requests.get(path_url).text
    namelist = listname(2, text)
    finduniv = re.compile(rr[2][3])
    for _, d in enumerate(namelist[0]):
        univ = univdata(ry[2][-1], 2, d, finduniv)
        selected_columns = ['univNameCn', 'grade']
        new_column_names = ['中文名称', '评级']
        df_selected = univ[selected_columns]
        df_selected.columns = new_column_names
        numlist.append(df_selected)
    universities = set()
    for df in numlist:
        universities.update(df['中文名称'].unique())
    data = pd.DataFrame(
        np.zeros((len(universities), 3), dtype=int),
        index=list(universities),
        columns=['A+专业', 'A类专业', '上榜专业']
    )
    for df in numlist:
        for _, row in df.iterrows():
            uni = row['中文名称']
            level = row['评级']
            top, first, listed = classify_major(level)
            if top:
                data.loc[uni, 'A+专业'] += 1
            if first:
                data.loc[uni, 'A类专业'] += 1
            if listed:
                data.loc[uni, '上榜专业'] += 1
    data = data.reset_index()
    data.columns = ['中文名称', 'A+专业', 'A类专业', '上榜专业']
    data = data.replace(0, None)
    return data

def main():
    jsfilepath = f'https://www.shanghairanking.cn/_nuxt/static/{number}/institution/payload.js'
    jsresponse = requests.get(jsfilepath)
    text = jsresponse.text
    univ = re.findall(finduniv, text)[0]
    univdata = remove(7, univdata2(univ, text))
    univdata["办学层次"] = univdata["办学层次"].replace({
        "10": "普通本科",
        "15": "职业本科",
        "20": "高职（专科）"
    })
    merged_df = pd.merge(univdata, rank(), on='中文名称', how='outer')
    merged = pd.merge(merged_df, num1(), on='中文名称', how='outer')
    merged = pd.merge(merged, num2(), on='中文名称', how='outer')
    df_sorted = merged.sort_values(by='院校代码')
    file_path = '中国大学表.xlsx'
    df_sorted.to_excel(file_path, index=False)
    print(f"数据已成功保存到{file_path}文件中。")

if __name__ == "__main__":
    main()