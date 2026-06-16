"""
为 JSON 文件中的所有对象添加或替换 "year" 键为默认年份列表。
用法：
    python add_year.py input.json [output.json]
如果提供了 output.json，结果写入该文件；否则覆盖 input.json。
"""

import json
import sys
from pathlib import Path

DEFAULT_YEARS = [2026, 2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015]


def add_year_to_objects(data):
    """递归处理数据，为每个字典设置/替换 'year' 键为默认年份列表。"""
    if isinstance(data, dict):
        # 无论是否存在 'year' 键，都直接设置为默认年份列表
        data["year"] = DEFAULT_YEARS
        # 递归处理字典中的所有值
        for value in data.values():
            add_year_to_objects(value)
    elif isinstance(data, list):
        # 递归处理列表中的每个元素
        for item in data:
            add_year_to_objects(item)
    # 其他类型（字符串、数字等）无需处理


def main():
    if len(sys.argv) < 2:
        print("错误：请提供输入文件路径。")
        print(f"用法: {sys.argv[0]} input.json [output.json]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.is_file():
        print(f"错误：文件 '{input_path}' 不存在。")
        sys.exit(1)

    # 读取原始 JSON
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误：JSON 解析失败 - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"错误：读取文件失败 - {e}")
        sys.exit(1)

    # 递归添加/替换 year 字段
    add_year_to_objects(data)

    # 确定输出路径
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path  # 覆盖原文件

    # 写入结果
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"处理完成，结果已保存至: {output_path}")
    except Exception as e:
        print(f"错误：写入文件失败 - {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()