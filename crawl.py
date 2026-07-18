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

# JSON 文件路径映射（用于读取层级数据）
json_files = {
    0: "json/bcur.json",
    1: "json/bcsr.json",
    2: "json/bcmr.json",
    3: "json/bcvcr.json",
    5: "json/gras.json",
}


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


def extract_leaf_codes(data, match_code=None):
    """
    从层级 JSON 数据中提取所有叶子节点的 (code, name, years) 列表。
    
    :param data: JSON 数据（列表，每个元素是一个节点）
    :param match_code: 可选，如果提供则只返回该 code 节点下的叶子节点
    :return: list of (code, name, years) 元组
    """
    result = []

    def _find_node(nodes, target_code):
        """在节点列表中查找指定 code 的节点"""
        for node in nodes:
            if node.get("number") == target_code:
                return node
            children = node.get("subfields")
            if children:
                found = _find_node(children, target_code)
                if found:
                    return found
        return None

    def _collect_leaves(node):
        """递归收集一个节点下的所有叶子节点"""
        children = node.get("subfields")
        if children:
            for child in children:
                _collect_leaves(child)
        else:
            # 没有 subfields 的节点就是叶子节点
            code = node.get("number")
            name = node.get("name", "")
            years = node.get("year", [])
            if code:
                result.append((code, name, years))

    if match_code is not None:
        # 查找匹配的节点
        matched = _find_node(data, match_code)
        if matched is None:
            return None  # 未找到
        # 从匹配节点开始收集叶子
        _collect_leaves(matched)
    else:
        # 从顶层开始收集所有叶子
        for node in data:
            _collect_leaves(node)

    return result


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
    # 哪些类型需要 code 参数（索引）：0:bcur,1:bcsr,2:bcmr,3:bcvcr,5:gras
    types_require_code = {0, 1, 2, 3, 5}

    while True:
        print("\n--- 新爬取任务 ---")
        type_arg = int(input("请输入爬取类型 (0-6): "))

        if type_arg in types_require_code:
            # 需要 code 的类型
            code_input = input("请输入子代码（留空则爬取该类型下所有子分类）: ").strip()

            year_input = input("请输入年份（留空则爬取所有可用年份）: ").strip()

            # 解析 code
            if code_input == "":
                # 爬取所有叶子节点
                json_path = json_files.get(type_arg)
                if not json_path or not os.path.exists(json_path):
                    print(f"错误：找不到 {json_path}，无法获取子分类列表")
                    continue
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                leaf_codes = extract_leaf_codes(data)
                if not leaf_codes:
                    print("错误：未找到任何子分类")
                    continue
            else:
                # 严格匹配输入的 code
                json_path = json_files.get(type_arg)
                if not json_path or not os.path.exists(json_path):
                    print(f"错误：找不到 {json_path}，无法查找子分类")
                    continue
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                leaf_codes = extract_leaf_codes(data, match_code=code_input)
                if leaf_codes is None:
                    print(f"输入有误：未找到 code 为 '{code_input}' 的分类")
                    continue

            # 解析年份
            if year_input == "":
                # 收集所有叶子节点的所有年份
                all_years = set()
                for _, _, years in leaf_codes:
                    all_years.update(years)
                years_to_crawl = sorted(all_years, reverse=True)
                # 留空年份时不过滤 code
                filtered_codes = leaf_codes
            else:
                target_year = int(year_input)
                years_to_crawl = [target_year]
                # 只保留包含该年份的 code
                filtered_codes = [(c, n, y) for c, n, y in leaf_codes if target_year in y]
                if not filtered_codes:
                    print(f"警告：没有 code 包含 {target_year} 年的数据，跳过")
                    continue

            # 执行爬取
            for code_val, name_val, code_years in filtered_codes:
                # 只爬取该 code 自身年份列表中的年份
                for year_val in years_to_crawl:
                    if year_val not in code_years:
                        continue
                    try:
                        onecrawl(type_arg, year_val, code_val, name_val)
                    except Exception as e:
                        print(f"爬取出错：类型={rv[type_arg]}, 年份={year_val}, code={code_val}, 错误={e}")

        else:
            # 不需要 code 的类型（arwu=4, grsssd=6），年份必须输入
            year_input = input("请输入年份: ").strip()
            while year_input == "":
                year_input = input("年份不能为空，请重新输入: ").strip()
            years_to_crawl = [int(year_input)]

            for year_val in years_to_crawl:
                try:
                    onecrawl(type_arg, year_val)
                except Exception as e:
                    print(f"爬取出错：类型={rv[type_arg]}, 年份={year_val}, 错误={e}")

        again = input("\n是否继续爬取？(y/n): ").strip().lower()
        if again != 'y':
            print("程序结束。")
            break
