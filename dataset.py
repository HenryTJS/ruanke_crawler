import pandas as pd


def process_excel_file(file_path):
    all_sheets = pd.read_excel(file_path, sheet_name=None)
    main_df = all_sheets["总表"]

    for sheet_name, sheet_data in all_sheets.items():
        if sheet_name == "总表":
            continue

        school_names = sheet_data["学校名称"].dropna().tolist()
        main_df[sheet_name] = main_df["学校名称"].apply(lambda x: 1 if x in school_names else 0)
        print(f"已处理工作表: {sheet_name}")

    # 特殊处理列表
    special_cases = [
        {"学校": "中国石油大学（北京）", "列名": "211", "修改值": 1},
        {"学校": "中国石油大学（华东）", "列名": "211", "修改值": 1},
        {"学校": "中国地质大学（北京）", "列名": "211", "修改值": 1},
        {"学校": "中国地质大学（武汉）", "列名": "211", "修改值": 1},
        {"学校": "中国矿业大学（北京）", "列名": "211", "修改值": 1},
        {"学校": "中国矿业大学（徐州）", "列名": "211", "修改值": 1},
        {"学校": "河北工业大学", "列名": "省市", "修改值": "天津市"},
        {"学校": "西藏民族大学", "列名": "省市", "修改值": "陕西省"},
        {"学校": "昆山杜克大学", "列名": "所在地", "修改值": "苏州市"},
        {"学校": "西昌医学高等专科学校", "列名": "所在地", "修改值": "凉山彝族自治州"},
        {"学校": "临夏现代职业学院", "列名": "所在地", "修改值": "临夏回族自治州"}
    ]

    # 遍历特殊处理列表并修改 main_df
    for case in special_cases:
        school = case["学校"]
        column = case["列名"]
        value = case["修改值"]

        if column in main_df.columns:
            main_df.loc[main_df["学校名称"] == school, column] = value
            print(f"已特殊处理: 学校={school}, 列名={column}, 修改值={value}")
        else:
            print(f"警告: 列名 {column} 不存在，无法处理学校 {school}")

    return main_df


def main():
    file_path = "高绩网数据.xlsx"
    result_df = process_excel_file(file_path)
    excel_path = '中国大学数据集.xlsx'
    result_df.to_excel(excel_path, sheet_name="总表", index=False)


if __name__ == "__main__":
    main()