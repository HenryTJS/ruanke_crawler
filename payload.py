import requests
import re
import csv
import sys
from io import StringIO

# ---------- 平衡分割函数（不判断双引号，用于分号分割主体数据） ----------
def split_by_balanced(s: str, delimiter: str = ';') -> list[str]:
    """
    按指定分隔符分割字符串，仅当分隔符之前的 {}、[] 完全配对时才作为分隔符。
    不判断双引号（主体数据中引号内可能包含大量分号，这些分号仍需作为分隔符）。
    """
    parts = []
    start = 0
    curly = 0      # 花括号平衡计数
    square = 0     # 方括号平衡计数

    for i, ch in enumerate(s):
        if ch == '{':
            curly += 1
        elif ch == '}':
            curly -= 1
        elif ch == '[':
            square += 1
        elif ch == ']':
            square -= 1
        elif ch == delimiter:
            if curly == 0 and square == 0:
                parts.append(s[start:i])
                start = i + 1
    parts.append(s[start:])
    return parts


# ---------- 平衡分割函数（判断双引号，用于逗号分割 s0/s1） ----------
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
                # 使用平衡分割按逗号拆分（判断双引号，忽略字符串内逗号）
                parts = split_by_balanced_quote(inner, delimiter=',')
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


# ---------- JS 对象字面量解析器（用于解析 univEnv 等嵌套结构） ----------
class JSParser:
    """递归下降解析 JS 对象/数组/字符串/数字/标识符，并用 mapping 替换变量名。"""
    def __init__(self, s, mapping):
        self.s = s
        self.i = 0
        self.n = len(s)
        self.mapping = mapping

    def skip_ws(self):
        while self.i < self.n and self.s[self.i] in ' \t\n\r':
            self.i += 1

    def parse(self):
        self.skip_ws()
        return self.parse_value()

    def parse_value(self):
        self.skip_ws()
        if self.i >= self.n:
            return None
        ch = self.s[self.i]
        if ch == '{':
            return self.parse_object()
        elif ch == '[':
            return self.parse_array()
        elif ch == '"':
            return self.parse_string()
        else:
            return self.parse_ident_or_num()

    def parse_object(self):
        self.i += 1
        obj = {}
        self.skip_ws()
        if self.i < self.n and self.s[self.i] == '}':
            self.i += 1
            return obj
        while True:
            self.skip_ws()
            if self.s[self.i] == '"':
                key = self.parse_string()
            else:
                key = self.parse_ident_or_num()
            self.skip_ws()
            if self.i < self.n and self.s[self.i] == ':':
                self.i += 1
            val = self.parse_value()
            obj[key] = val
            self.skip_ws()
            if self.i < self.n and self.s[self.i] == ',':
                self.i += 1
                continue
            elif self.i < self.n and self.s[self.i] == '}':
                self.i += 1
                break
            else:
                break
        return obj

    def parse_array(self):
        self.i += 1
        arr = []
        self.skip_ws()
        if self.i < self.n and self.s[self.i] == ']':
            self.i += 1
            return arr
        while True:
            val = self.parse_value()
            arr.append(val)
            self.skip_ws()
            if self.i < self.n and self.s[self.i] == ',':
                self.i += 1
                continue
            elif self.i < self.n and self.s[self.i] == ']':
                self.i += 1
                break
            else:
                break
        return arr

    def parse_string(self):
        self.i += 1
        result = []
        while self.i < self.n:
            ch = self.s[self.i]
            if ch == '\\':
                self.i += 1
                if self.i < self.n:
                    esc = self.s[self.i]
                    if esc == 'u':
                        hexs = self.s[self.i+1:self.i+5]
                        try:
                            result.append(chr(int(hexs, 16)))
                            self.i += 5
                        except Exception:
                            result.append('u')
                            self.i += 1
                    elif esc == 'n':
                        result.append('\n'); self.i += 1
                    elif esc == 't':
                        result.append('\t'); self.i += 1
                    elif esc == 'r':
                        result.append('\r'); self.i += 1
                    elif esc == '"':
                        result.append('"'); self.i += 1
                    elif esc == '\\':
                        result.append('\\'); self.i += 1
                    else:
                        result.append(esc); self.i += 1
            elif ch == '"':
                self.i += 1
                break
            else:
                result.append(ch)
                self.i += 1
        return ''.join(result)

    def parse_ident_or_num(self):
        start = self.i
        while self.i < self.n and self.s[self.i] not in ',:{}[]"\n\r\t ':
            self.i += 1
        token = self.s[start:self.i]
        if token in self.mapping:
            return self.mapping[token]
        return token


def parse_js(s, mapping):
    """解析 JS 对象/数组字面量字符串，并递归替换变量名。"""
    return JSParser(s, mapping).parse()


def clean_js_str(v):
    """去掉字符串值外层包裹的引号（如 '"xxx"' -> 'xxx'），并处理 JS 空值。"""
    if v is None:
        return ''
    if isinstance(v, str):
        if v in ('null', 'undefined', 'NaN'):
            return ''
        if len(v) >= 2 and v[0] == '"' and v[-1] == '"':
            return v[1:-1]
    return v


def format_univ_env(env_dict):
    """把解析后的 univEnv 字典格式化为多个列。"""
    cols = {}
    cols['univEnv_consultPhone'] = clean_js_str(env_dict.get('consultPhone', ''))
    cols['univEnv_email'] = clean_js_str(env_dict.get('email', ''))
    cols['univEnv_publishedAt'] = clean_js_str(env_dict.get('publishedAt', ''))

    # 学科/设施列表 inds（嵌套结构：分组 -> children）
    inds = env_dict.get('inds', [])
    inds_parts = []
    for group in inds:
        if not isinstance(group, dict):
            continue
        group_name = clean_js_str(group.get('name', ''))
        children = group.get('children', [])
        child_parts = []
        for ch in children:
            if not isinstance(ch, dict):
                continue
            name = clean_js_str(ch.get('name', ''))
            val = clean_js_str(ch.get('val', ''))
            if name:
                if val:
                    child_parts.append(f"{name}({val})")
                else:
                    child_parts.append(name)
        if child_parts:
            inds_parts.append(f"{group_name}: {', '.join(child_parts)}")
    cols['univEnv_inds'] = '; '.join(inds_parts)

    # 图片列表 pubPicture
    pics = env_dict.get('pubPicture', [])
    pic_urls = [clean_js_str(p.get('imgUrl', '')) for p in pics if isinstance(p, dict)]
    cols['univEnv_pubPicture'] = '|'.join(pic_urls)

    # 推荐理由 reason
    reasons = env_dict.get('reason', [])
    if isinstance(reasons, list):
        cleaned = [clean_js_str(r) for r in reasons]
        cleaned = [r for r in cleaned if r]
        cols['univEnv_reason'] = '|'.join(cleaned)
    else:
        cols['univEnv_reason'] = clean_js_str(reasons)

    return cols


def expand_univ_env(dict_list, mapping):
    """遍历字典列表，将 univEnv 字段解析并拆分为多个列。"""
    new_result = []
    for d in dict_list:
        new_d = dict(d)
        env_raw = new_d.get('univEnv', '')
        if env_raw and env_raw.strip().startswith('{'):
            try:
                env_dict = parse_js(env_raw, mapping)
                if isinstance(env_dict, dict):
                    cols = format_univ_env(env_dict)
                    new_d.update(cols)
            except Exception:
                pass
        new_d.pop('univEnv', None)
        new_result.append(new_d)
    return new_result


# ---------- 清理输出值（去掉 JS 字符串外层引号） ----------
def clean_output_value(v):
    """去掉字符串值外层包裹的双引号，以及数组内部元素的双引号。"""
    if not isinstance(v, str):
        return v
    s = v.strip()
    # 数组格式：[...]，去掉内部每个元素的引号
    if s.startswith('[') and s.endswith(']'):
        inner = s[1:-1]
        if not inner.strip():
            return '[]'
        # 按逗号分割（忽略引号内的逗号）
        parts = split_by_balanced_quote(inner, delimiter=',')
        cleaned = []
        for p in parts:
            p = p.strip()
            if len(p) >= 2 and p[0] == '"' and p[-1] == '"':
                p = p[1:-1]
            cleaned.append(p)
        return '[' + ', '.join(cleaned) + ']'
    # 简单字符串：去掉外层引号
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return s[1:-1]
    return s


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
url = "https://www.shanghairanking.cn/_nuxt/static/1789466132/institution/payload.js"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0",
    "Referer": "https://www.shanghairanking.cn/institution/huazhong-university-of-science-and-technology",
    "Accept": "*/*",
    # 注意：服务器会忽略 Accept-Encoding 并强制返回 br(Brotli) 压缩，
    # 因此需要声明 br 并在下方用 brotli 库手动解压。
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

print(f"正在请求: {url}")
resp = requests.get(url, headers=headers)
resp.raise_for_status()

# 说明：环境已安装 brotli 库，requests 会自动解压 br(Brotli) 编码的响应，
# 因此 resp.content 已是解压后的明文，无需（也不能）再次手动解压。
source_code = resp.content.decode('utf-8', errors='ignore')

# 提取 s0 和 s1（使用平衡分割，分隔符为逗号）
s0_raw = re.findall(r'\(function\((.*?)\)', source_code)[0]
s1_raw = re.findall(r'mutations:\[\]\}\}\((.*?)\)', source_code)[0]

s0_list = [x.strip() for x in split_by_balanced_quote(s0_raw, delimiter=',')]
s1_list = [x.strip() for x in split_by_balanced_quote(s1_raw, delimiter=',')]

# 提取主体数据部分（从第一个学校数据开始，按分号分割）
context = re.findall(r'gW\.code=e;(.*?);return', source_code)[0]
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

# 3. 解析 univEnv 字段，拆分为多个列
result = expand_univ_env(result, mapping)

# 4. 删除不需要的列
DROP_COLUMNS = {'logo', 'inbound', 'liked', 'univLikeCount', 'isVocational', 'charCode', 'cateCode', 'rankBcur'}
result = [{k: v for k, v in d.items() if k not in DROP_COLUMNS} for d in result]

# 5. 清理输出值（去掉 JS 字符串外层引号）
result = [{k: clean_output_value(v) for k, v in d.items()} for d in result]

# 5.1 数据修正：指定学校的城市改为目标城市
CITY_OVERRIDES = {
    '昆山杜克大学': '苏州市',
    '陆军军事交通学院': '天津市',
    '海南东方新丝路职业学院': '东方市',
    '双河职业技术学院': '双河市',
}
for d in result:
    name = d.get('nameCn', '')
    if name in CITY_OVERRIDES:
        d['cityName'] = CITY_OVERRIDES[name]

# 5.2 数据修正：院校类型为空的统一改为"其他"
for d in result:
    if not d.get('categoryName', '').strip():
        d['categoryName'] = '其他'

# 6. 按 univCode 以文本类型从小到大排序
result = sorted(result, key=lambda d: str(d.get('univCode', '')))

# 输出 CSV（可通过命令行参数指定输出文件名，默认 output.csv）
output_file = sys.argv[1] if len(sys.argv) > 1 else "output.csv"
dict_list_to_csv(result, output_file=output_file)
print(f"CSV 已生成：{output_file}")