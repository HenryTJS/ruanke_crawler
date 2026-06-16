"""
为 JSON 文件中已有 year 列表的对象添加前置年份。
规则：如果对象的 year 列表包含某个给定年份，则在列表最前面插入另一组给定的年份列表。
用法：
    python prepend_years.py input.json [output.json]
"""

import json
import sys
from pathlib import Path

# ========== 可配置参数 ==========
TRIGGER_YEAR = 2025          # 触发条件：year 列表中包含此年份
YEARS_TO_PREPEND = [2026]  # 满足条件时添加到列表最前面的年份
# ===============================


def process_year(data):
    """递归处理数据，修改符合条件的字典中的 year 列表。"""
    if isinstance(data, dict):
        # 检查是否存在 year 字段且为列表
        years = data.get("year")
        if isinstance(years, list):
            if TRIGGER_YEAR in years:
                # 在列表最前面插入 YEARS_TO_PREPEND，生成新列表
                data["year"] = YEARS_TO_PREPEND + years
        # 无论是否修改，继续递归处理嵌套结构
        for value in data.values():
            process_year(value)
    elif isinstance(data, list):
        for item in data:
            process_year(item)


def main():
    if len(sys.argv) < 2:
        print("错误：请提供输入文件路径。")
        print(f"用法: {sys.argv[0]} input.json [output.json]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.is_file():
        print(f"错误：文件 '{input_path}' 不存在。")
        sys.exit(1)

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误：JSON 解析失败 - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"错误：读取文件失败 - {e}")
        sys.exit(1)

    process_year(data)

    output_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else input_path
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"处理完成，结果已保存至: {output_path}")
    except Exception as e:
        print(f"错误：写入文件失败 - {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()