import requests
import re
import csv
from io import StringIO

# ---------- 通用平衡分割函数（支持自定义分隔符，并忽略引号内分隔符） ----------
def split_by_balanced(s: str, delimiter: str = ';') -> list[str]:
    """
    按指定分隔符分割字符串，但仅当分隔符之前的 {}、[] 完全配对，
    且双引号为偶数（即不在双引号字符串内部）时才作为分隔符。
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

# ---------- 解析条目（a.b=c） ----------
def parse_entries(entries):
    if not entries:
        return []
    result = []
    current_a = None
    current_dict = {}
    for entry in entries:
        a, rest = entry.split('.', 1)
        b, c = rest.split('=', 1)
        if current_a is None:
            current_a = a
            current_dict = {b: c}
        elif a == current_a:
            current_dict[b] = c
        else:
            result.append(current_dict)
            current_a = a
            current_dict = {b: c}
    if current_a is not None:
        result.append(current_dict)
    return result

# ---------- 替换字典中的值（根据 s0 → s1 映射） ----------
def replace_values(dict_list, old_list, new_list):
    """
    根据 old_list -> new_list 的映射，将字典列表中每个字典的值进行替换。
    """
    mapping = {}
    for old, new in zip(old_list, new_list):
        old_stripped = old.strip()
        new_stripped = new.strip()
        if old_stripped:
            mapping[old_stripped] = new_stripped

    new_result = []
    for d in dict_list:
        new_d = {}
        for key, value in d.items():
            new_value = mapping.get(value, value)
            new_d[key] = new_value
        new_result.append(new_d)
    return new_result

# ---------- 处理数组格式的值（替换内部元素） ----------
def process_array_values(dict_list, mapping):
    """
    遍历字典列表，对每个字符串值，若为 '[...]' 格式，
    则分割内部元素，用 mapping 替换每个元素，重新组合。
    """
    for d in dict_list:
        for key, value in d.items():
            if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                # 提取内部内容（去掉首尾方括号）
                inner = value[1:-1]
                # 使用平衡分割按逗号拆分
                parts = split_by_balanced(inner, delimiter=',')
                new_parts = []
                for p in parts:
                    p_stripped = p.strip()
                    # 若匹配映射则替换，否则保留原样（包括空格）
                    if p_stripped in mapping:
                        new_parts.append(mapping[p_stripped])
                    else:
                        new_parts.append(p)  # 保留原始字符串（含空格）
                # 重新组合，用 ', ' 连接（可读性较好）
                d[key] = '[' + ', '.join(new_parts) + ']'
    return dict_list

# ---------- 字典列表转 CSV ----------
def dict_list_to_csv(dict_list, output_file=None, fieldnames=None, delimiter=','):
    if not dict_list:
        if output_file:
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                pass
        return ""
    if fieldnames is None:
        fieldnames = []
        for d in dict_list:
            for key in d.keys():
                if key not in fieldnames:
                    fieldnames.append(key)
    if output_file:
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter, restval='')
            writer.writeheader()
            writer.writerows(dict_list)
    else:
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=delimiter, restval='')
        writer.writeheader()
        writer.writerows(dict_list)
        return output.getvalue()

# ---------- 主流程 ----------
url = "https://www.shanghairanking.cn/_nuxt/static/1784027557/institution/payload.js"
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

# 提取 s0 和 s1（使用平衡分割，分隔符为逗号）
s0_raw = re.findall(r'\(function\((.*?)\)', source_code)[0]
s1_raw = re.findall(r'mutations:\[\]\}\}\((.*?)\)', source_code)[0]

s0_list = [x.strip() for x in split_by_balanced(s0_raw, delimiter=',')]
s1_list = [x.strip() for x in split_by_balanced(s1_raw, delimiter=',')]

# 提取主体数据部分（大括号内，按分号分割）
context = re.findall(r'\{(.*?);return', source_code)[0]
result = split_by_balanced(context, delimiter=';')
result = parse_entries(result)

# 构建映射（用于整体替换和数组内部替换）
mapping = {}
for old, new in zip(s0_list, s1_list):
    old_stripped = old.strip()
    new_stripped = new.strip()
    if old_stripped:
        mapping[old_stripped] = new_stripped

# 1. 整体值替换（如果整个值匹配 s0，则整体替换）
if len(s0_list) == len(s1_list):
    result = replace_values(result, s0_list, s1_list)
else:
    print("警告：s0 和 s1 长度不一致，跳过整体值替换。")

# 2. 处理数组格式的值（内部元素替换）
result = process_array_values(result, mapping)

# 输出 CSV
dict_list_to_csv(result, output_file="output.csv")
print("CSV 已生成：output.csv")