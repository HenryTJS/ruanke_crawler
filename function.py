# 运行中所用的函数

import csv
import re
import requests
import pandas as pd
import os
import json
from data import rr, rn, rv, ry, number, findfunction, findoutput, dropcolumn, replacement

def convert(inp):
    try:
        inp = int(inp)
        if 0 <= inp <= 6:
            return 1
        elif inp == 7:
            return 2
        else:
            return 0
    except ValueError:
        return 0

def newsplit(text):
    return next(csv.reader([text], delimiter=',', quotechar='"'))

def outlist(text):
    functionlist = [item.replace('"', '') for item in newsplit(re.findall(findfunction, text)[0])]
    outputlist = [item.replace('"', '') for item in newsplit(re.findall(findoutput, text)[0])]
    outputlist = ['' if x == 'null' else x for x in outputlist]
    return [functionlist, outputlist]

def newreplace(text, datalist):
    functionlist, outputlist = outlist(text)
    for i, row in enumerate(datalist):
        for j, element in enumerate(row):
            if '"' in datalist[i][j]:
                datalist[i][j] = datalist[i][j].replace('"', '')
            elif element in functionlist:
                datalist[i][j] = outputlist[functionlist.index(element)]
    return datalist

def listname(i, text):
    x, y = [], []
    types = re.findall(re.compile(rr[i][0]), text)
    findid = re.compile(rr[i][1])
    findname = re.compile(rr[i][2])
    for ty in types:
        x.extend(re.findall(findid, ty))
        y.extend(re.findall(findname, ty))
    return newreplace(text, [x, y])

def path(i, j, d):
    urls = [
        f'https://www.shanghairanking.cn/api/pub/v1/bcur?bcur_type={d}&year={j}',
        f'https://www.shanghairanking.cn/api/pub/v1/bcsr/rank?target_yr={j}&subj_code={d}',
        f'https://www.shanghairanking.cn/api/pub/v1/bcmr/rank?year={j}&majorCode={d}',
        f'https://www.shanghairanking.cn/api/pub/v1/bcvcr?bcvcr_type={d}&year={j}',
        f'https://www.shanghairanking.com/api/pub/v1/arwu/rank?version={j}',
        f'https://www.shanghairanking.cn/api/pub/v1/gras/rank?year={j}&subj_code={d}',
        f'https://www.shanghairanking.com/api/pub/v1/grsssd/rank?version={j}'
    ]
    return urls[i] if i < len(urls) else urls[-1]

def remove(i, df):
    df = pd.DataFrame(df)
    columns_to_keep = [col for col in df.columns if col not in dropcolumn[i]]
    df = df[columns_to_keep]
    col_mapping = {old_key: new_key for item in replacement for old_key, new_key in item.items()}
    return df.rename(columns=col_mapping)

def univdata(j, i, d, finduniv):
    eachresponse = requests.get(path(i, j, d))
    eachtext = eachresponse.text
    univ = json.loads(re.findall(finduniv, eachtext)[0])
    return remove(i, univ)

def newsplit2(text):
    a = b = 0
    newtext = ''
    for t in text:
        if t == ';':
            newtext += '^' if a == b else t
        else:
            if t == '[':
                a += 1
            elif t == ']':
                b += 1
            newtext += t
    univdata = newtext.split("^")
    alluniv = {}
    for i in range(2, len(univdata)):
        key, value = univdata[i].split('.', 1)
        alluniv.setdefault(key, []).append(value)
    allun = []
    for values in alluniv.values():
        univ = {}
        for u in values:
            k, v = u.split('=')
            if '"' in v:
                v = v[1:-1]
            elif '[' in v:
                v = v[1:-1].split(',')
            univ[k] = v
        allun.append(univ)
    return allun

def newreplace2(text, datalist):
    functionlist, outputlist = outlist(text)
    for row in datalist:
        for key, value in row.items():
            if value in functionlist:
                row[key] = outputlist[functionlist.index(value)]
            elif isinstance(value, list) and value:
                for idx, item in enumerate(value):
                    if item in functionlist:
                        value[idx] = outputlist[functionlist.index(item)]
                row[key] = '/'.join(value)
    return datalist

def univdata2(univ, text):
    univdata = newsplit2(univ)
    univdata = newreplace2(text, univdata)
    return remove(7, univdata)

def newsave(i, current_dir, years=None):
    years = years if years is not None else ry[i]
    for j in years:
        path_url = f'https://www.shanghairanking.cn/_nuxt/static/{number}/rankings/{rv[i]}/{j}/payload.js'
        text = requests.get(path_url).text
        namelist = listname(i, text)
        finduniv = re.compile(rr[i][3])
        folder = os.path.join(current_dir, f'{rn[i]}')
        os.makedirs(folder, exist_ok=True)
        for k, d in enumerate(namelist[0]):
            univ = univdata(j, i, d, finduniv)
            file_path = os.path.join(folder, f'{j}年{namelist[1][k]}.xlsx')
            univ.to_excel(file_path, sheet_name=f'{j}年{namelist[1][k]}', index=False)
            print(f"数据已成功保存到{file_path}文件中。")

def newsave2(i, current_dir, years=None):
    years = years if years is not None else ry[i]
    finduniv = re.compile(rr[i][3])
    for j in years:
        univ = univdata(j, i, 0, finduniv)
        folder = os.path.join(current_dir, f'{rn[i]}')
        os.makedirs(folder, exist_ok=True)
        file_path = os.path.join(folder, f'{j}年.xlsx')
        univ.to_excel(file_path, sheet_name=f'{j}年', index=False)
        print(f"数据已成功保存到{file_path}文件中。")