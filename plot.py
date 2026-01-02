import os
import pandas as pd
import openpyxl
import math

def process_subjects():
    input_file = "中国最好学科排名.xlsx"
    output_file = "软科排名可视化.xlsx"
    sheet_name = "中国最好学科排名"

    # 读取所有工作表
    all_sheets = pd.read_excel(input_file, sheet_name=None)
    
    # 初始化结果 DataFrame，预定义列名
    result_df = pd.DataFrame(columns=["院校代码", "院校名称", "前2名", "前3名", "前4名", "前3%", "前7%", "前12%", "前20%", "前30%", "前40%", "前50%", "总得分", "权重"])

    for sheet, data in all_sheets.items():
        data.columns = ["院校代码", "院校名称", "排名", "层次", "得分"]
        num_rows = math.log(len(data) + 1)
        max_score = data.iloc[0, -1]

        # 遍历每一行，统计层次数据
        for _, row in data.iterrows():
            school_code = row["院校代码"]
            school_name = row["院校名称"]
            level = row["层次"]
            score = row["得分"]

            # 如果院校代码和名称不存在，则新增一行
            if not ((result_df["院校代码"] == school_code) & (result_df["院校名称"] == school_name)).any():
                new_row = {"院校代码": school_code, "院校名称": school_name}
                result_df = pd.concat([result_df, pd.DataFrame([new_row])], ignore_index=True)
                result_df.loc[result_df["院校代码"] == school_code, result_df.columns.difference(["院校代码", "院校名称"])] = 0

            result_df.loc[
                (result_df["院校代码"] == school_code) & (result_df["院校名称"] == school_name),
                level
            ] += 1

            result_df.loc[
                (result_df["院校代码"] == school_code) & (result_df["院校名称"] == school_name),
                "总得分"
            ] += score / max_score * num_rows * 1000

            result_df.loc[
                (result_df["院校代码"] == school_code) & (result_df["院校名称"] == school_name),
                "权重"
            ] += num_rows

    # 添加八列，并使用 Excel 公式填充
    result_df["最终得分"] = None
    result_df["最终排名"] = None
    result_df["顶尖学科"] = None
    result_df["一流学科"] = None
    result_df["上榜学科"] = None
    result_df["顶尖比一流"] = None
    result_df["顶尖比上榜"] = None
    result_df["一流比上榜"] = None

    # 保存到 "软科大学可视化.xlsx" 的新工作表
    mode = "a" if os.path.exists(output_file) else "w"
    with pd.ExcelWriter(output_file, engine="openpyxl", mode=mode, if_sheet_exists="replace" if mode == "a" else None) as writer:
        result_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)

        # 打开工作簿和工作表
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # 获取列名对应的 Excel 列字母
        def get_column_letter(column_name):
            return openpyxl.utils.get_column_letter(result_df.columns.get_loc(column_name) + 1)

        # 获取列字母
        final_score_col = get_column_letter("最终得分")
        final_rank_col = get_column_letter("最终排名")
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
            # 最终得分公式
            worksheet[f"{final_score_col}{row}"] = f"=IF({get_column_letter('权重')}{row}=0, 0, {get_column_letter('总得分')}{row}/{get_column_letter('权重')}{row})"
            # 最终排名公式
            worksheet[f"{final_rank_col}{row}"] = f"=RANK({final_score_col}{row}, {final_score_col}${start_row}:{final_score_col}${total_rows}, 0)"
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

def process_majors():
    input_file = "中国大学专业排名.xlsx"
    output_file = "软科排名可视化.xlsx"
    sheet_name = "中国大学专业排名"

    # 读取所有工作表
    all_sheets = pd.read_excel(input_file, sheet_name=None)
    
    # 初始化结果 DataFrame，预定义列名
    result_df = pd.DataFrame(columns=["院校代码", "院校名称", "A+", "A", "B+", "B", "总得分", "权重"])

    for sheet, data in all_sheets.items():
        data.columns = ["院校代码", "院校名称", "排名", "评级", "得分"]
        num_rows = math.log(len(data) + 1)
        max_score = data.iloc[0, -1]

        # 如果评级列有空数据，跳过该工作表
        if data['评级'].isnull().any():
            print(f"工作表 {sheet} 的评级列包含空数据，已跳过。")
            continue

        # 遍历每一行，统计层次数据
        for _, row in data.iterrows():
            school_code = row["院校代码"]
            school_name = row["院校名称"]
            level = row["评级"]
            score = row["得分"]

            # 如果院校代码和名称不存在，则新增一行
            if not ((result_df["院校代码"] == school_code) & (result_df["院校名称"] == school_name)).any():
                new_row = {"院校代码": school_code, "院校名称": school_name}
                result_df = pd.concat([result_df, pd.DataFrame([new_row])], ignore_index=True)
                result_df.loc[result_df["院校代码"] == school_code, result_df.columns.difference(["院校代码", "院校名称"])] = 0

            # 确保该校在该层次列的数据直接加1
            result_df.loc[
                (result_df["院校代码"] == school_code) & (result_df["院校名称"] == school_name),
                level
            ] += 1

            result_df.loc[
                (result_df["院校代码"] == school_code) & (result_df["院校名称"] == school_name),
                "总得分"
            ] += score / max_score * num_rows * 1000

            result_df.loc[
                (result_df["院校代码"] == school_code) & (result_df["院校名称"] == school_name),
                "权重"
            ] += num_rows

    # 添加八列，并使用 Excel 公式填充
    result_df["最终得分"] = None
    result_df["最终排名"] = None
    result_df["A+专业"] = None
    result_df["A类专业"] = None
    result_df["上榜专业"] = None
    result_df["A+比A类"] = None
    result_df["A+比上榜"] = None
    result_df["A类比上榜"] = None

    # 保存到 "软科大学可视化.xlsx" 的新工作表
    mode = "a" if os.path.exists(output_file) else "w"
    with pd.ExcelWriter(output_file, engine="openpyxl", mode=mode, if_sheet_exists="replace" if mode == "a" else None) as writer:
        result_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)

        # 打开工作簿和工作表
        workbook = writer.book
        worksheet = writer.sheets[sheet_name]

        # 获取列名对应的 Excel 列字母
        def get_column_letter(column_name):
            return openpyxl.utils.get_column_letter(result_df.columns.get_loc(column_name) + 1)

        # 获取列字母
        final_score_col = get_column_letter("最终得分")
        final_rank_col = get_column_letter("最终排名")
        top_major_col = get_column_letter("A+专业")
        first_major_col = get_column_letter("A类专业")
        listed_major_col = get_column_letter("上榜专业")
        top_vs_first_col = get_column_letter("A+比A类")
        top_vs_listed_col = get_column_letter("A+比上榜")
        first_vs_listed_col = get_column_letter("A类比上榜")

        # 获取数据起始行和列
        start_row = 2  # 数据从第2行开始（Excel中从1开始计数）
        total_rows = len(result_df) + start_row - 1

        # 填充公式
        for row in range(start_row, total_rows + 1):
            # 最终得分公式
            worksheet[f"{final_score_col}{row}"] = f"=IF({get_column_letter('权重')}{row}=0, 0, {get_column_letter('总得分')}{row}/{get_column_letter('权重')}{row})"
            # 最终排名公式
            worksheet[f"{final_rank_col}{row}"] = f"=RANK({final_score_col}{row}, {final_score_col}${start_row}:{final_score_col}${total_rows}, 0)"
            # A+专业公式
            worksheet[f"{top_major_col}{row}"] = f"=SUM({get_column_letter('A+')}{row})"
            # A类专业公式
            worksheet[f"{first_major_col}{row}"] = f"=SUM({get_column_letter('A+专业')}{row},{get_column_letter('A')}{row})"
            # 上榜专业公式
            worksheet[f"{listed_major_col}{row}"] = f"=SUM({get_column_letter('A类专业')}{row},{get_column_letter('B+')}{row},{get_column_letter('B')}{row})"
            # A+比A类公式
            worksheet[f"{top_vs_first_col}{row}"] = f"=IF({first_major_col}{row}=0, -1, {top_major_col}{row}/{first_major_col}{row})"
            # A+比上榜公式
            worksheet[f"{top_vs_listed_col}{row}"] = f"=IF({listed_major_col}{row}=0, -1, {top_major_col}{row}/{listed_major_col}{row})"
            # A类比上榜公式
            worksheet[f"{first_vs_listed_col}{row}"] = f"=IF({listed_major_col}{row}=0, -1, {first_major_col}{row}/{listed_major_col}{row})"

    print(f"数据已成功保存到 {output_file} 的 {sheet_name} 工作表中。")

if __name__ == "__main__":
    process_subjects()
    # process_majors()