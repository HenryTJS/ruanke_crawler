import csv
import re
import requests
import pandas as pd
import json
import sqlite3
from data import rr, rn, rv, ry, findfunction, findoutput, dropcolumn, replacement


def convert(inp):
    try:
        inp = int(inp)
        if 0 <= inp <= 6:
            return 1
        elif inp == 7:
            return 2
        return 0
    except ValueError:
        return 0


def newsplit(text):
    return next(csv.reader([text], delimiter=',', quotechar='"'))


def outlist(text):
    functionlist = [item.replace('"', '') for item in newsplit(re.findall(findfunction, text)[0])]
    outputlist = [item.replace('"', '') for item in newsplit(re.findall(findoutput, text)[0])]
    outputlist = ['' if x == '' else x for x in outputlist]
    return functionlist, outputlist


def newreplace(text, datalist):
    functionlist, outputlist = outlist(text)
    for row in datalist:
        for j, element in enumerate(row):
            if isinstance(element, str) and '"' in element:
                row[j] = element.replace('"', '')
            elif element in functionlist:
                row[j] = outputlist[functionlist.index(element)]
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


def get_url(i, j, d):
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
    columns_to_keep = [col for col in df.columns if col not in dropcolumn[i]]
    df = df[columns_to_keep]
    col_mapping = {old_key: new_key for item in replacement for old_key, new_key in item.items()}
    return df.rename(columns=col_mapping)


def univdata(j, i, d, finduniv):
    response = requests.get(get_url(i, j, d))
    text = response.text
    univ_data = json.loads(re.findall(finduniv, text)[0])
    return pd.DataFrame(univ_data)


def newsplit2(text):
    a = b = 0
    newtext = []
    current_part = []
    
    for t in text:
        if t == ';' and a == b:
            newtext.append(''.join(current_part))
            current_part = []
        else:
            if t == '[':
                a += 1
            elif t == ']':
                b += 1
            current_part.append(t)
    
    if current_part:
        newtext.append(''.join(current_part))
    
    alluniv = {}
    for part in newtext[2:]:
        if '.' not in part:
            continue
        key, value = part.split('.', 1)
        alluniv.setdefault(key, []).append(value)
    
    allun = []
    for values in alluniv.values():
        univ = {}
        for u in values:
            if '=' not in u:
                continue
            k, v = u.split('=', 1)
            if '"' in v:
                v = v[1:-1]
            elif '[' in v:
                v = v[1:-1].split(',')
            univ[k] = v
        if univ:
            allun.append(univ)
    
    return allun


def newreplace2(text, datalist):
    functionlist, outputlist = outlist(text)
    
    for row in datalist:
        for key, value in row.items():
            if isinstance(value, list) and value:
                processed_values = []
                for item in value:
                    if item in functionlist:
                        processed_values.append(outputlist[functionlist.index(item)])
                    else:
                        processed_values.append(item)
                row[key] = '/'.join(map(str, processed_values))
            elif value in functionlist:
                row[key] = outputlist[functionlist.index(value)]
    
    return datalist


def univdata2(univ, text):
    univ_data = newsplit2(univ)
    univ_data = newreplace2(text, univ_data)
    return pd.DataFrame(univ_data)


def save_to_database(df, db_path, table_name):
    try:
        with sqlite3.connect(db_path) as conn:
            df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"数据已成功保存到数据库 {db_path} 的表 {table_name} 中。")
    except Exception as e:
        print(f"保存到数据库时出错: {e}")


def read_table_to_dataframe(table_name):
    conn = sqlite3.connect("subfield.db")
    df = pd.read_sql_query(f"SELECT * FROM {table_name};", conn)
    conn.close()
    return df


def newsave1(i, years):
    df = read_table_to_dataframe(rv[i])
    namelist = [df.iloc[:, -2].tolist(), df.iloc[:, -1].tolist()]
    finduniv = re.compile(rr[i][3])
    for k, d in enumerate(namelist[0]):
        univ_df = univdata(years, i, d, finduniv)
        univ_df = remove(i, univ_df)
        db_path = f'{rn[i]}.db'
        save_to_database(univ_df, db_path, f'{years}年{namelist[1][k]}')


def newsave2(i, years):
    finduniv = re.compile(rr[i][3])
    univ_df = univdata(years, i, 0, finduniv)
    univ_df = remove(i, univ_df)
    db_path = f'{rn[i]}.db'
    save_to_database(univ_df, db_path, f'{years}年')


def main():
    while True:
        print("\n请输入你要爬取的表格（按7退出）：")
        print("0: 中国大学排名")
        print("1: 中国最好学科排名")
        print("2: 中国大学专业排名")
        print("3: 中国高职院校排名")
        print("4: 世界大学学术排名")
        print("5: 世界一流学科排名")
        print("6: 全球体育类院系学术排名")
        user_input = input("请选择：")
        
        if convert(user_input) == 1:
            table_index = int(user_input)
            years = ry[table_index]
            
            if table_index in (4, 6):
                newsave2(table_index, years)
            else:
                newsave1(table_index, years)
                
        elif convert(user_input) == 0:
            print("输入有误，请重新输入。")
        else:
            print("下次见！")
            break


if __name__ == "__main__":
    main()