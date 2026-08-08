# -*- coding: utf-8 -*-
"""
将 output.csv 转换为前端可用的 data.js 文件。
生成一个全局变量 UNIV_DATA，包含所有高校数据。
"""
import csv
import json
import re

def clean_text(s):
    """清理文本，去除多余空白"""
    if s is None:
        return ""
    return re.sub(r'\s+', ' ', str(s)).strip()

def clean_tags(s):
    """清理标签字段：null 或空值统一处理为空字符串"""
    cleaned = clean_text(s)
    # 处理 null / None / 空字符串 / 空数组等情况
    if cleaned.lower() in ('null', 'none', '[]', 'nan'):
        return ""
    return cleaned

def main():
    with open('output.csv', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = []
        for r in reader:
            row = {
                'up': clean_text(r.get('up', '')),
                'univCode': clean_text(r.get('univCode', '')),
                'nameCn': clean_text(r.get('nameCn', '')),
                'nameEn': clean_text(r.get('nameEn', '')),
                'tags': clean_tags(r.get('tags', '')),
                'adminType': clean_text(r.get('adminType', '')),
                'provinceShort': clean_text(r.get('provinceShort', '')),
                'cityName': clean_text(r.get('cityName', '')),
                'categoryName': clean_text(r.get('categoryName', '')),
                'level': clean_text(r.get('level', '')),
                'eduLevel': clean_text(r.get('eduLevel', '')),
                'phone': clean_text(r.get('univEnv_consultPhone', '')),
                'email': clean_text(r.get('univEnv_email', '')),
                'publishedAt': clean_text(r.get('univEnv_publishedAt', '')),
                'inds': clean_text(r.get('univEnv_inds', '')),
                'reason': clean_text(r.get('univEnv_reason', '')),
            }
            rows.append(row)

    # 生成 JS 文件
    js_content = "// 高校数据（由 output.csv 自动生成）\n"
    js_content += "var UNIV_DATA = " + json.dumps(rows, ensure_ascii=False) + ";\n"

    with open('data.js', 'w', encoding='utf-8') as f:
        f.write(js_content)

    print(f"已生成 data.js，共 {len(rows)} 条记录")

if __name__ == '__main__':
    main()
