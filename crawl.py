import requests
import json
import re
import pandas as pd
import jsonpgsql


rv = ['bcur', 'bcsr', 'bcmr', 'bcvcr', 'arwu', 'gras', 'grsssd']

rr = [
    r'"rankings":(.*?),"inds"', r'"rankings":(.*?),"pctTops"',
    r'"rankings":(.*?),"region"', r'"rankings":(.*?),"inds"',
    r'"rankings":(.*?),"inds"', r'"rankings":(.*?),"inds"',
    r'"rankings":(.*?),"inds"'
]

keep_column = [
    ['univNameCn', 'univCategory', 'province', 'score', 'ranking'],
    ['univCode', 'univNameCn', 'ranking', 'rankPctTop', 'score'],
    ['univCode', 'univNameCn', 'ranking', 'grade', 'score'],
    ['univNameCn', 'univCategory', 'province', 'score', 'ranking'],
    ['ranking', 'univNameCn', 'region', 'regionRanking', 'score'],
    ['ranking', 'univCode', 'univNameCn', 'region', 'score'],
    ['ranking', 'univNameCn', 'region', 'score', 'unitNameCn']
]

replacement = [
    {'univCode': '院校代码'},
    {'univNameCn': '院校名称'},
    {'univCategory': '院校类型'},
    {'province': '所在省份'},
    {'score': '得分'},
    {'ranking': '排名'},
    {'grade': '评级'},
    {'rankPctTop': '层次'},
    {'region': '地区'},
    {'regionRanking': '地区排名'},
    {'unitNameCn': '院系名称'}
]


def get_url(i, j, d):
    urls = [
        f'https://www.shanghairanking.cn/api/pub/v1/bcur?bcur_type={d}&year={j}',
        f'https://www.shanghairanking.cn/api/pub/v1/bcsr/rank?target_yr={j}&subj_code={d}',
        f'https://www.shanghairanking.cn/api/pub/v1/bcmr/rank?year={j}&majorCode={d}',
        f'https://www.shanghairanking.cn/api/pub/v1/bcvcr?bcvcr_type={d}&year={j}',
        f'https://www.shanghairanking.cn/api/pub/v1/arwu/rank?year={j}',
        f'https://www.shanghairanking.cn/api/pub/v1/gras/rank?year={j}&subj_code={d}',
        f'https://www.shanghairanking.cn/api/pub/v1/grsssd/rank?year={j}'
    ]
    return urls[i] if i < len(urls) else urls[-1]


def onecrawl(type, year, code=None):
    """
    爬取指定 type 和 year 的数据。
    对于某些 type（例如 arwu, grsssd）不需要 code 参数；对于需要 code 的 type，如果未提供将报错。
    """
    # 哪些类型需要 code 参数（索引）：0:bcur,1:bcsr,2:bcmr,3:bcvcr,5:gras
    types_require_code = {0, 1, 2, 3, 5}
    if type in types_require_code and code is None:
        raise ValueError(f"类型 {rv[type]} 需要提供 code 参数")

    finduniv = re.compile(rr[type])
    response = requests.get(get_url(type, year, code))
    text = response.text
    univ_data = json.loads(re.findall(finduniv, text)[0])
    univ_data = pd.DataFrame(univ_data)
    columns_to_keep = [col for col in univ_data.columns if col in keep_column[type]]
    univ_data = univ_data[columns_to_keep]
    col_mapping = {old_key: new_key for item in replacement for old_key, new_key in item.items()}
    univ_data = univ_data.rename(columns=col_mapping)
    # 显示简要信息
    print(f"抓取类型: {rv[type]} 年份: {year}，记录数: {len(univ_data)}")
    print(univ_data.head(10))

    # 尝试写入数据库（表名按 type_year）
    try:
        jsonpgsql.save_dataframe_to_db(univ_data, rv[type], year, code)
    except Exception as e:
        print("写入数据库时出错：", e)


if __name__ == "__main__":
    onecrawl(6, 2025, 0)