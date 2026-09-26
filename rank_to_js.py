# -*- coding: utf-8 -*-
"""将本地软科排名 CSV 合并为前端可读取的 ranking_data.js。"""
import csv
import glob
import json
import os

OUTPUT_FILE = "output.csv"
FILTER_FILE = "筛选.md"


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def read_filter_tree():
    subject = {}
    major = {}
    with open(FILTER_FILE, encoding="utf-8") as file:
        for line in file:
            parts = line.strip().split(maxsplit=1)
            if len(parts) != 2 or not parts[0].isdigit():
                continue
            code, name = parts
            if len(code) == 2:
                subject[code] = name
                major[code] = name
            elif len(code) == 4:
                major[code] = name
    return {"subject": subject, "major": major}


def rank_value(value):
    value = clean(value)
    return value


def should_skip_file(path):
    filename = os.path.basename(path)
    return "名单" in filename or "总榜" in filename


def read_universities():
    universities = {}
    with open(OUTPUT_FILE, encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            code = clean(row.get("univCode"))
            name = clean(row.get("nameCn"))
            record = {"code": code, "name": name}
            if code:
                universities[("code", code)] = record
            if name:
                universities.setdefault(("name", name), record)
    return universities


def get_record(universities, row, prefer_code=True):
    code = clean(row.get("院校代码"))
    name = clean(row.get("院校名称"))
    if prefer_code and code and ("code", code) in universities:
        return universities[("code", code)]
    if name and ("name", name) in universities:
        return universities[("name", name)]
    if code and ("code", code) in universities:
        return universities[("code", code)]
    return None


def add_record(result, record, field, value):
    if not record:
        return
    key = record["code"] or record["name"]
    result.setdefault(key, {})[field] = value


def read_overall(path, result, field, title, year):
    if should_skip_file(path):
        return
    with open(path, encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            record = get_record(UNIVERSITIES, row, prefer_code=False)
            if not record:
                continue
            add_record(result, record, field, {
                "title": title,
                "year": year,
                "rank": rank_value(row.get("排名")),
                "score": rank_value(row.get("得分")),
                "category": clean(row.get("院校类型")),
            })


def read_overall_files(pattern, result, field):
    for path in sorted(glob.glob(pattern)):
        if should_skip_file(path):
            continue
        stem = os.path.splitext(os.path.basename(path))[0]
        parts = stem.split("_", 3)
        year = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else ""
        title = parts[3] if len(parts) > 3 else field
        read_overall(path, result, field, title, year)


def read_detail_files(pattern, result, field, kind, year):
    for path in sorted(glob.glob(pattern)):
        if should_skip_file(path):
            continue
        filename = os.path.basename(path)
        stem = os.path.splitext(filename)[0]
        parts = stem.split("_", 3)
        code = parts[2] if len(parts) > 2 else ""
        title = parts[3] if len(parts) > 3 else code
        with open(path, encoding="utf-8-sig") as file:
            for row in csv.DictReader(file):
                record = get_record(UNIVERSITIES, row, prefer_code=True)
                if not record:
                    continue
                item = {
                    "kind": kind,
                    "title": title,
                    "code": code,
                    "year": year,
                    "rank": rank_value(row.get("排名")),
                    "score": rank_value(row.get("得分")),
                }
                if kind == "major":
                    item["grade"] = clean(row.get("评级"))
                else:
                    item["level"] = clean(row.get("层次"))
                key = record["code"] or record["name"]
                result.setdefault(key, {}).setdefault(field, []).append(item)


UNIVERSITIES = read_universities()
RANKINGS = {}
FILTER_TREE = read_filter_tree()

read_overall_files("csv/bcur_*.csv", RANKINGS, "bcur")
read_overall_files("csv/bcvcr_*.csv", RANKINGS, "bcvcr")
read_detail_files("csv/bcmr_2026_*.csv", RANKINGS, "bcmr", "major", 2026)
read_detail_files("csv/bcsr_2025_*.csv", RANKINGS, "bcsr", "subject", 2025)

for ranking in RANKINGS.values():
    for item in ranking.get("bcsr", []):
        code = clean(item.get("code"))
        if len(code) == 4 and code not in FILTER_TREE["subject"]:
            FILTER_TREE["subject"][code] = clean(item.get("title"))
    for item in ranking.get("bcmr", []):
        code = clean(item.get("code"))
        # 专业代码可能是 6 位，也可能带 K/T/TK 等后缀（7~9 位），需一并收录
        if len(code) >= 6 and code[:4] in FILTER_TREE["major"] and code not in FILTER_TREE["major"]:
            FILTER_TREE["major"][code] = clean(item.get("title"))

with open("ranking_data.js", "w", encoding="utf-8") as file:
    file.write("// 排名数据（由本地排名 CSV 自动生成）\n")
    file.write("var RANKING_DATA = ")
    json.dump(RANKINGS, file, ensure_ascii=False, separators=(",", ":"))
    file.write(";\n")
    file.write("var RANKING_FILTER_TREE = ")
    json.dump(FILTER_TREE, file, ensure_ascii=False, separators=(",", ":"))
    file.write(";\n")

print(f"已生成 ranking_data.js，共覆盖 {len(RANKINGS)} 所高校")
print(f"bcur: {sum(1 for v in RANKINGS.values() if v.get('bcur'))}")
print(f"bcvcr: {sum(1 for v in RANKINGS.values() if v.get('bcvcr'))}")
print(f"bcmr records: {sum(len(v.get('bcmr', [])) for v in RANKINGS.values())}")
print(f"bcsr records: {sum(len(v.get('bcsr', [])) for v in RANKINGS.values())}")
