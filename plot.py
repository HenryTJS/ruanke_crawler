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

    # 计算新增列的数值
    # 最终得分
    result_df["最终得分"] = result_df.apply(
        lambda row: 0 if row["权重"] == 0 else row["总得分"] / row["权重"], axis=1
    )
    
    # 顶尖学科
    result_df["顶尖学科"] = result_df["前2名"] + result_df["前3%"]
    
    # 一流学科
    result_df["一流学科"] = (
        result_df["顶尖学科"] + result_df["前7%"] + result_df["前12%"] + 
        result_df["前3名"] + result_df["前4名"]
    )
    
    # 上榜学科
    result_df["上榜学科"] = (
        result_df["一流学科"] + result_df["前20%"] + result_df["前30%"] + 
        result_df["前40%"] + result_df["前50%"]
    )
    
    # 顶尖比一流
    result_df["顶尖比一流"] = result_df.apply(
        lambda row: -1 if row["一流学科"] == 0 else row["顶尖学科"] / row["一流学科"], axis=1
    )
    
    # 顶尖比上榜
    result_df["顶尖比上榜"] = result_df.apply(
        lambda row: -1 if row["上榜学科"] == 0 else row["顶尖学科"] / row["上榜学科"], axis=1
    )
    
    # 一流比上榜
    result_df["一流比上榜"] = result_df.apply(
        lambda row: -1 if row["上榜学科"] == 0 else row["一流学科"] / row["上榜学科"], axis=1
    )
    
    # 最终排名（按最终得分降序排名）
    result_df["最终排名"] = result_df["最终得分"].rank(ascending=False, method="min").astype(int)
    
    # 调整列顺序，将最终得分和最终排名放到最后
    cols = [col for col in result_df.columns if col not in ["最终得分", "最终排名"]]
    cols.extend(["最终得分", "最终排名"])
    result_df = result_df[cols]
    
    # 按最终排名升序排列
    result_df = result_df.sort_values("最终排名", ascending=True).reset_index(drop=True)

    # 保存到 "软科大学可视化.xlsx" 的新工作表
    mode = "a" if os.path.exists(output_file) else "w"
    with pd.ExcelWriter(output_file, engine="openpyxl", mode=mode, if_sheet_exists="replace" if mode == "a" else None) as writer:
        result_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)

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

    # 计算新增列的数值
    # 最终得分
    result_df["最终得分"] = result_df.apply(
        lambda row: 0 if row["权重"] == 0 else row["总得分"] / row["权重"], axis=1
    )
    
    # A+专业
    result_df["A+专业"] = result_df["A+"]
    
    # A类专业
    result_df["A类专业"] = result_df["A+专业"] + result_df["A"]
    
    # 上榜专业
    result_df["上榜专业"] = result_df["A类专业"] + result_df["B+"] + result_df["B"]
    
    # A+比A类
    result_df["A+比A类"] = result_df.apply(
        lambda row: -1 if row["A类专业"] == 0 else row["A+专业"] / row["A类专业"], axis=1
    )
    
    # A+比上榜
    result_df["A+比上榜"] = result_df.apply(
        lambda row: -1 if row["上榜专业"] == 0 else row["A+专业"] / row["上榜专业"], axis=1
    )
    
    # A类比上榜
    result_df["A类比上榜"] = result_df.apply(
        lambda row: -1 if row["上榜专业"] == 0 else row["A类专业"] / row["上榜专业"], axis=1
    )
    
    # 最终排名（按最终得分降序排名）
    result_df["最终排名"] = result_df["最终得分"].rank(ascending=False, method="min").astype(int)
    
    # 调整列顺序，将最终得分和最终排名放到最后
    cols = [col for col in result_df.columns if col not in ["最终得分", "最终排名"]]
    cols.extend(["最终得分", "最终排名"])
    result_df = result_df[cols]
    
    # 按最终排名升序排列
    result_df = result_df.sort_values("最终排名", ascending=True).reset_index(drop=True)

    # 保存到 "软科大学可视化.xlsx" 的新工作表
    mode = "a" if os.path.exists(output_file) else "w"
    with pd.ExcelWriter(output_file, engine="openpyxl", mode=mode, if_sheet_exists="replace" if mode == "a" else None) as writer:
        result_df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=0)

    print(f"数据已成功保存到 {output_file} 的 {sheet_name} 工作表中。")

if __name__ == "__main__":
    # process_subjects()
    process_majors()