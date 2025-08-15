# 运行中所用的函数

import csv
import re
from data import rr,rn,rv,ry,number,findfunction,findoutput,dropcolumn,replacement
import requests
import pandas as pd
import os
import json

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
    reader = csv.reader([text],delimiter=',',quotechar='"')
    result = next(reader)
    return result

def outlist(text):
    function = re.findall(findfunction,text)[0]
    functionlist = newsplit(function)
    output = re.findall(findoutput,text)[0]
    outputlist = newsplit(output)
    functionlist = [item.replace('"','') for item in functionlist]
    outputlist = [item.replace('"','') for item in outputlist]
    outputlist = ['' if x == 'null' else x for x in outputlist]
    return [functionlist,outputlist]
    
def newreplace(text,datalist):
    functionlist,outputlist = outlist(text)[0],outlist(text)[1]
    for i,row in enumerate(datalist):
        for j,element in enumerate(row):
            if '"' in datalist[i][j]:
                datalist[i][j] = datalist[i][j].replace('"','')
            elif element in functionlist:
                a = functionlist.index(element)
                datalist[i][j] = outputlist[a]
    return datalist

def listname(i,text):
    namelist = []
    x = []
    y = []
    findtypes = re.compile(rr[i][0])
    types = re.findall(findtypes,text)
    findid = re.compile(rr[i][1])
    findname = re.compile(rr[i][2])
    for ty in types:
        ids = re.findall(findid,ty)
        for ii in ids:
            x.append(ii)
        names = re.findall(findname,ty)
        for nn in names:
            y.append(nn)
        namelist = newreplace(text,[x,y])
    return namelist

def path(i,j,d):
    if i == 0:
        path = 'https://www.shanghairanking.cn/api/pub/v1/bcur?bcur_type=' + d + '&year=' + str(j)
    elif i == 1:
        path = 'https://www.shanghairanking.cn/api/pub/v1/bcsr/rank?target_yr=' + str(j) + '&subj_code=' + d
    elif i == 2:
        path = 'https://www.shanghairanking.cn/api/pub/v1/bcmr/rank?year=' + str(j) + '&majorCode=' + d
    elif i == 3:
        path = 'https://www.shanghairanking.cn/api/pub/v1/bcvcr?bcvcr_type=' + d + '&year=' + str(j)
    elif i == 4:
        path = 'https://www.shanghairanking.com/api/pub/v1/arwu/rank?version=' + str(j)
    elif i == 5:
        path = 'https://www.shanghairanking.cn/api/pub/v1/gras/rank?year=' + str(j) + '&subj_code=' + d
    else:
        path = 'https://www.shanghairanking.com/api/pub/v1/grsssd/rank?version=' + str(j)
    return path

def remove(i,df):
    df = pd.DataFrame(df)
    columns_to_keep = [col for col in df.columns if col not in dropcolumn[i]]
    df = df[columns_to_keep]
    col_mapping = {}
    for item in replacement:
        for old_key, new_key in item.items():
            col_mapping[old_key] = new_key
    df = df.rename(columns=col_mapping)
    return df

def univdata(j,i,d,finduniv):
    eachpath = path(i,j,d)
    eachresponse = requests.get(eachpath)
    eachtext = eachresponse.text
    univ = re.findall(finduniv,eachtext)[0]
    univ = json.loads(univ)
    univ = remove(i,univ)
    return univ

def newsplit2(text):
    a = 0
    b = 0
    newtext = ''
    for t in text:
        if t == ';':
            if a == b:
                newtext += '^'
            else:
                newtext += t
        else:
            if t == '[':
                a += 1
            elif t == ']':
                b += 1
            newtext += t
    univdata = newtext.split("^")
    alluniv = {}
    allun = []
    for i in range(2,len(univdata)):
        univdata[i] = univdata[i].split('.',1)
        if univdata[i][0] not in alluniv:
            alluniv[univdata[i][0]] = []
        alluniv[univdata[i][0]].append(univdata[i][1])
    for key in alluniv:
        allun.append(alluniv[key])
    alluniv = []
    for un in allun:
        univ = {}
        for u in un:
            u = u.split('=')
            if '"' in u[1]:
                u[1] = u[1][1:-1]
            elif '[' in u[1]:
                u[1] = u[1][1:-1].split(',')
            univ[u[0]] = u[1]
        alluniv.append(univ)
    return alluniv

def newreplace2(text,datalist):
    functionlist,outputlist = outlist(text)[0],outlist(text)[1]
    for i,row in enumerate(datalist):
        for key,value in datalist[i].items():
            if datalist[i][key] in functionlist:
                a = functionlist.index(datalist[i][key])
                datalist[i][key] = outputlist[a]
            elif type(datalist[i][key]) == list:
                if datalist[i][key]:
                    for item in range(0,len(datalist[i][key])):
                        if datalist[i][key][item] in functionlist:
                            a = functionlist.index(datalist[i][key][item])
                            datalist[i][key][item] = outputlist[a]
                datalist[i][key] = '/'.join(datalist[i][key])
    return datalist

def univdata2(univ,text):
    univdata = newsplit2(univ)
    univdata = newreplace2(text,univdata)
    univdata = remove(7,univdata)
    return univdata

def newsave(i,current_dir):
    for j in ry[i]:
        path = 'https://www.shanghairanking.cn/_nuxt/static/' + number + '/rankings/' + rv[i] + '/' + str(j) + '/payload.js'
        allresponse = requests.get(path)
        text = allresponse.text
        namelist = listname(i,text)
        finduniv = re.compile(rr[i][3])
        for k in range(0,len(namelist[0])):
            d = namelist[0][k]
            univ = univdata(j,i,d,finduniv)
            new_folder_name = f'{rn[i]}'
            new_folder_path = os.path.join(current_dir,new_folder_name)
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path)
            file_name = f'{j}年{namelist[1][k]}.xlsx'
            file_path = os.path.join(new_folder_path,file_name)
            univ.to_excel(file_path,sheet_name=f'{j}年{namelist[1][k]}',index=False)
            print(f"数据已成功保存到{file_path}文件中。")
            
def newsave2(i,current_dir):
    finduniv = re.compile(rr[i][3])
    for j in ry[i]:
        univ = univdata(j,i,0,finduniv)
        new_folder_name = f'{rn[i]}'
        new_folder_path = os.path.join(current_dir,new_folder_name)
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)
        file_name = f'{j}年.xlsx'
        file_path = os.path.join(new_folder_path,file_name)
        univ.to_excel(file_path,sheet_name=f'{j}年',index=False)
        print(f"数据已成功保存到{file_path}文件中。")