import requests
import json
import re
import pandas as pd
import os


rv = ['bcur', 'bcsr', 'bcmr', 'bcvcr', 'arwu', 'gras', 'grsssd']

rr = [
    r'"rankings":(.*?),"inds"', r'"rankings":(.*?),"pctTops"',
    r'"rankings":(.*?),"region"', r'"rankings":(.*?),"inds"',
    r'"rankings":(.*?),"inds"', r'"rankings":(.*?),"inds"',
    r'"rankings":(.*?),"inds"'
]

ry = [
    [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
    [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
    [2021, 2022, 2023, 2024, 2025, 2026],
    [2023, 2024, 2025, 2026],
    [2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
    [2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
    [2016, 2017, 2018, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
]

rc = [r'data:\[(.*?)\],', r'data:\[(.*?)\],', r'\{(.*?)return', r'data:\[(.*?)\],', None,  r'data:\[(.*?)\],', None]

rm = [[r'id:(.*?),', r'nameCn:(.*?),'],
      [r'code:(.*?),', r'nameCn:(.*?),'],
      [r'code=(.*?);', r'name=(.*?);'],
      [r'id:(.*?),', r'nameCn:(.*?),'],
      [],
      [r'code:(.*?),', r'nameCn:(.*?),'],
      []]

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

def split_by_balanced_quote(s: str, delimiter: str = ',') -> list[str]:
    """
    按指定分隔符分割字符串，仅当分隔符之前的 {}、[] 完全配对，
    且双引号为偶数（即不在双引号字符串内部）时才作为分隔符。
    用于分割 s0/s1，忽略字符串值内部的逗号。
    """
    parts = []
    start = 0
    curly = 0      # 花括号平衡计数
    square = 0     # 方括号平衡计数
    quote = 0      # 双引号计数（偶数表示不在引号内）

    for i, ch in enumerate(s):
        if ch == '{':
            curly += 1
        elif ch == '}':
            curly -= 1
        elif ch == '[':
            square += 1
        elif ch == ']':
            square -= 1
        elif ch == '"':
            quote += 1
        elif ch == delimiter:
            if curly == 0 and square == 0 and quote % 2 == 0:
                parts.append(s[start:i])
                start = i + 1
    parts.append(s[start:])
    return parts


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


def onecrawl(type, year, code=None, name=""):
    """
    爬取指定 type 和 year 的数据，保存为 CSV 文件。
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

    # 保存为 CSV 文件（无数据时不保存）
    if len(univ_data) == 0:
        print(f"抓取结果为空，跳过保存")
        return
    os.makedirs("csv", exist_ok=True)
    if code is not None:
        csv_filename = f"csv/{rv[type]}_{year}_{code}_{name}.csv"
    else:
        csv_filename = f"csv/{rv[type]}_{year}.csv"
    univ_data.to_csv(csv_filename, index=False, encoding="utf-8-sig")
    print(f"CSV 文件已保存: {csv_filename}")


if __name__ == "__main__":
    print("=== 软科排名爬虫 ===")
    print("类型说明：0=bcur, 1=bcsr, 2=bcmr, 3=bcvcr, 4=arwu, 5=gras, 6=grsssd")
    types_require_code = {0, 1, 2, 3, 5}

    while True:
        print("\n--- 新爬取任务 ---")
        type_arg = int(input("请输入爬取类型 (0-6): "))

        if type_arg in types_require_code:
            year_input = int(input("请输入年份: "))

            if year_input not in ry[type_arg]:
                print(f"错误：年份 {year_input} 不在可用年份列表中: {ry[type_arg]}")
                continue
            else:
                url = "https://www.shanghairanking.cn/_nuxt/static/1789466132/rankings/" + rv[type_arg] + f"/{year_input}/payload.js"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0",
                    "Referer": "https://www.shanghairanking.cn/institution/huazhong-university-of-science-and-technology",
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                }
                print(f"正在请求: {url}")
                resp = requests.get(url, headers=headers)
                resp.raise_for_status()
                source_code = resp.content.decode('utf-8', errors='ignore')

                s0_raw = re.findall(r'\(function\((.*?)\)', source_code)[0]
                s1_raw = re.findall(r'mutations:\[\]\}\}\((.*?)\)', source_code)[0]

                s0_list = [x.strip() for x in split_by_balanced_quote(s0_raw, delimiter=',')]
                s1_list = [x.strip() for x in split_by_balanced_quote(s1_raw, delimiter=',')]

                context = re.findall(rc[type_arg], source_code)[0]
                print(context)
                code_list = re.findall(rm[type_arg][0], context)
                print(code_list)
                name_list = re.findall(rm[type_arg][1], context)
                print(name_list)
                for i in range(len(code_list)):
                    code = code_list[i]
                    name = name_list[i]
                    for j in range(len(s0_list)):
                        if code in s0_list[j]:
                            code = s1_list[j]
                            break
                    for j in range(len(s0_list)):
                        if name in s0_list[j]:
                            name = s1_list[j]
                            break
                    if name.startswith('"') and name.endswith('"'):
                        name = name[1:-1]
                    if code.startswith('"') and code.endswith('"'):
                        code = code[1:-1]
                    print(f"正在爬取子分类: {name} (code: {code})")
                    onecrawl(type_arg, year_input, code, name)