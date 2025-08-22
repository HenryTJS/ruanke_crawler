import re
import requests
import pandas as pd
import json
from function import listname
from data import number, rv, rr, rn, ry

sc = ['ranking', 'rankPctTop', 'grade', 'ranking']

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

def univdata(j, i, d, finduniv):
    eachresponse = requests.get(path(i, j, d))
    eachtext = eachresponse.text
    univ = json.loads(re.findall(finduniv, eachtext)[0])
    return pd.DataFrame(univ)

for i in range(4):
    path_url = f'https://www.shanghairanking.cn/_nuxt/static/{number}/rankings/{rv[i]}/{ry[i][-1]}/payload.js'
    text = requests.get(path_url).text
    namelist = listname(i, text)
    finduniv = re.compile(rr[i][3])
    ranklist = []
    for k, d in enumerate(namelist[0]):
        if '总榜' in namelist[1][k] or '名单' in namelist[1][k]:
            continue
        univ = univdata(ry[i][-1], i, d, finduniv)
        selected_columns = ['univNameCn', sc[i]]
        new_column_names = ['院校名称', namelist[1][k]]
        df_selected = univ[selected_columns]
        df_selected.columns = new_column_names
        ranklist.append(df_selected)
    result_df = ranklist[0]
    for df in ranklist[1:]:
        result_df = pd.merge(
            result_df,
            df,
            on='院校名称',
            how='outer'
        )
    file_path = f'{rn[i]}.xlsx'
    result_df.to_excel(file_path, sheet_name=f'{rn[i]}', index=False)
    print(f"数据已成功保存到{file_path}文件中。")