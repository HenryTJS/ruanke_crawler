import os
import pandas as pd
import openpyxl

def process_subjects():
    input_file = "中国最好学科排名.xlsx"
    output_file = "软科排名可视化.xlsx"
    sheet_name = "中国最好学科排名"

    # 读取所有工作表
    all_sheets = pd.read_excel(input_file, sheet_name=None)
    
    # 初始化结果 DataFrame，预定义列名
    result_df = pd.DataFrame(columns=["院校代码", "院校名称"])

    for sheet, data in all_sheets.items():
        # 确保工作表有五列：院校代码、院校名称、排名、层次、得分
        if data.shape[1] < 5:
            print(f"工作表 {sheet} 数据格式不正确，跳过处理。")
            continue

        # 只保留需要的列
        data = data.iloc[:, :5]
        data.columns = ["院校代码", "院校名称", "排名", "层次", "得分"]

        # 遍历每一行，统计层次数据
        for _, row in data.iterrows():
            school_code = row["院校代码"]
            school_name = row["院校名称"]
            level = row["层次"]

            # 如果院校代码和名称不存在，则新增一行
            if not ((result_df["院校代码"] == school_code) & (result_df["院校名称"] == school_name)).any():
                new_row = {"院校代码": school_code, "院校名称": school_name}
                result_df = pd.concat([result_df, pd.DataFrame([new_row])], ignore_index=True)

            # 确保层次列存在，如果不存在则初始化为0
            if level not in result_df.columns:
                result_df[level] = 0

            # 确保该校在该层次列的数据被初始化为0
            result_df.loc[
                (result_df["院校代码"] == school_code) & (result_df["院校名称"] == school_name),
                level
            ] = result_df.loc[
                (result_df["院校代码"] == school_code) & (result_df["院校名称"] == school_name),
                level
            ].fillna(0)

            # 更新层次统计数据
            result_df.loc[
                (result_df["院校代码"] == school_code) & (result_df["院校名称"] == school_name),
                level
            ] += 1

    # 确保所有空值填充为0
    result_df = result_df.fillna(0)

    # 添加六列，并使用 Excel 公式填充
    result_df["顶尖学科"] = None
    result_df["一流学科"] = None
    result_df["上榜学科"] = None
    result_df["顶尖比一流"] = None
    result_df["顶尖比上榜"] = None
    result_df["一流比上榜"] = None

    # 保存到 "软科大学可视化.xlsx" 的新工作表
    with pd.ExcelWriter(output_file, engine="openpyxl", mode="a" if os.path.exists(output_file) else "w", if_sheet_exists="replace") as writer:
        result_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)

        # 打开工作簿和工作表
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # 获取列名对应的 Excel 列字母
        def get_column_letter(column_name):
            return openpyxl.utils.get_column_letter(result_df.columns.get_loc(column_name) + 1)

        # 获取列字母
        top_subject_col = get_column_letter("顶尖学科")
        first_subject_col = get_column_letter("一流学科")
        listed_subject_col = get_column_letter("上榜学科")
        top_vs_first_col = get_column_letter("顶尖比一流")
        top_vs_listed_col = get_column_letter("顶尖比上榜")
        first_vs_listed_col = get_column_letter("一流比上榜")

        # 获取数据起始行和列
        start_row = 2  # 数据从第2行开始（Excel中从1开始计数）
        total_rows = len(result_df) + start_row - 1

        # 填充公式
        for row in range(start_row, total_rows + 1):
            # 顶尖学科公式
            worksheet[f"{top_subject_col}{row}"] = f"=SUM({get_column_letter('前2名')}{row},{get_column_letter('前3%')}{row})"
            # 一流学科公式
            worksheet[f"{first_subject_col}{row}"] = f"=SUM({get_column_letter('顶尖学科')}{row},{get_column_letter('前7%')}{row},{get_column_letter('前12%')}{row},{get_column_letter('前3名')}{row},{get_column_letter('前4名')}{row})"
            # 上榜学科公式
            worksheet[f"{listed_subject_col}{row}"] = f"=SUM({get_column_letter('一流学科')}{row},{get_column_letter('前20%')}{row},{get_column_letter('前30%')}{row},{get_column_letter('前40%')}{row},{get_column_letter('前50%')}{row})"
            # 顶尖比一流公式
            worksheet[f"{top_vs_first_col}{row}"] = f"=IF({first_subject_col}{row}=0, -1, {top_subject_col}{row}/{first_subject_col}{row})"
            # 顶尖比上榜公式
            worksheet[f"{top_vs_listed_col}{row}"] = f"=IF({listed_subject_col}{row}=0, -1, {top_subject_col}{row}/{listed_subject_col}{row})"
            # 一流比上榜公式
            worksheet[f"{first_vs_listed_col}{row}"] = f"=IF({listed_subject_col}{row}=0, -1, {first_subject_col}{row}/{listed_subject_col}{row})"

    print(f"数据已成功保存到 {output_file} 的 {sheet_name} 工作表中。")

if __name__ == "__main__":
    process_subjects()