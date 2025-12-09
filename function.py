import re
import requests
import pandas as pd
import json
import sqlite3

rv = ['bcur', 'bcsr', 'bcmr', 'bcvcr', 'arwu', 'gras', 'grsssd']

rr = [
    r'"rankings":(.*?),"inds"', r'"rankings":(.*?),"pctTops"',
    r'"rankings":(.*?),"region"', r'"rankings":(.*?),"inds"',
    r'"rankings":(.*?),"inds"', r'"rankings":(.*?),"inds"',
    r'"rankings":(.*?),"inds"'
]

ry = [2025, 2025, 2025, 2025, 2025, 2025, 2024]

rn = [
    '中国大学排名', '中国最好学科排名', '中国大学专业排名', '中国高职院校排名',
    '世界大学学术排名', '世界一流学科排名', '全球体育类院系学术排名'
]

dropcolumn = [
    ['univUp', 'univLogo', 'liked', 'inbound', 'univLikeCount', 'univTags', 'indData', 'univNameRemark', 'univNameEn', 'rankChange', 'rankOverall'],
    ['univUp', 'univLogo', 'liked', 'inbound', 'univLikeCount', 'doctoralDegree', 'focusSubj', 'contrastRanking', 'rankPctTopNum'],
    ['univUp', 'univLogo', 'city', 'liked', 'inbound', 'univLikeCount', 'univTags', 'indGrades', 'province'],
    ['univUp', 'isVocational', 'univLogo', 'liked', 'univLikeCount', 'univTags', 'indData', 'outdated', 'univNameEn', 'rankOverall'],
    ['univUp', 'univUpEn', 'univLogo', 'inbound', 'univLikeCount', 'liked', 'indData', 'univCode'],
    ['univUp', 'univUpEn', 'univLogo', 'inbound', 'univLikeCount', 'liked', 'indData', 'regionRanking'],
    ['univUp', 'univUpEn', 'univLogo', 'inbound', 'univLikeCount', 'liked', 'indData', 'univCode']
]

replacement = [
    {'univCode': '院校代码'},
    {'nameCn': '中文名称'},
    {'nameEn': '英文名称'},
    {'tags': '院校特色'},
    {'adminType': '院校归属'},
    {'provinceShort': '所在省份'},
    {'cityName': '所在城市'},
    {'categoryName': '院校类型'},
    {'eduLevel': '办学层次'},
    {'univNameCn': '院校名称'},
    {'univCategory': '院校类型'},
    {'province': '所在省份'},
    {'score': '得分'},
    {'ranking': '排名'},
    {'grade': '评级'},
    {'rankPctTop': '层次'},
    {'univNameEn': '英文名称'},
    {'region': '地区'},
    {'regionRanking': '地区排名'},
    {'unitNameCn': '院系名称'}
]

change = {
    '常熟理工学院': '苏州工学院',
    '南昌工程学院': '江西水利电力大学',
    '西藏农牧学院': '西藏农牧大学',
    '吉林化工学院': '吉林化工大学',
    '天水师范学院': '天水师范大学',
    '新乡医学院': '河南医药大学',
    '桂林医学院': '桂林医科大学',
    '北京师范大学-香港浸会大学联合国际学院': '北师香港浸会大学',
    '广州番禺职业技术学院': '广州职业技术大学',
    '宁波职业技术学院': '宁波职业技术大学',
    '杭州职业技术学院': '杭州职业技术大学',
    '顺德职业技术学院': '顺德职业技术大学',
    '宁夏职业技术学院': '宁夏职业技术大学',
    '扬州市职业大学': '扬州职业技术大学',
    '铜仁职业技术学院': '铜仁职业技术大学',
    '武威职业学院': '武威职业技术大学',
    '呼和浩特职业学院': '呼和浩特职业技术大学',
    '深圳信息职业技术学院': '深圳信息职业技术大学',
    '陕西工业职业技术学院': '陕西工业职业技术大学',
    '重庆工业职业技术学院': '重庆工业职业技术大学',
    '无锡职业技术学院': '无锡职业技术大学',
    '芜湖职业技术学院': '芜湖职业技术大学',
    '成都航空职业技术学院': '成都航空职业技术大学',
    '安徽职业技术学院': '安徽职业技术大学',
    '贵州轻工职业技术学院': '贵州轻工职业大学',
    '苏州市职业大学': '苏州职业技术大学',
    '内蒙古建筑职业技术学院': '内蒙古建筑职业技术大学',
    '杨凌职业技术学院': '陕西农林职业技术大学',
    '安徽医学高等专科学校': '安徽第二医学院',
    '曲靖医学高等专科学校': '曲靖健康医学院',
    '宁夏工商职业技术学院': '宁夏工商职业技术大学',
    '太原旅游职业学院': '山西文化旅游职业大学',
    '天津公安警官职业学院': '天津警察学院',
    '共青科技职业学院': '九江科技职业大学',
}

def convert(inp):
    try:
        inp = int(inp)
        if 0 <= inp <= 6:
            return 1
        elif inp == 7:
            return 2
        return 0
    except ValueError:
        return 0


def get_url(i, j, d):
    urls = [
        f'https://www.shanghairanking.cn/api/pub/v1/bcur?bcur_type={d}&year={j}',
        f'https://www.shanghairanking.cn/api/pub/v1/bcsr/rank?target_yr={j}&subj_code={d}',
        f'https://www.shanghairanking.cn/api/pub/v1/bcmr/rank?year={j}&majorCode={d}',
        f'https://www.shanghairanking.cn/api/pub/v1/bcvcr?bcvcr_type={d}&year={j}',
        f'https://www.shanghairanking.cn/api/pub/v1/arwu/rank?year={j}',
        f'https://www.shanghairanking.cn/api/pub/v1/gras/rank?year={j}&subj_code={d}',
        f'https://www.shanghairanking.cn/api/pub/v1/grsssd/rank?year={j}'
    ]
    return urls[i] if i < len(urls) else urls[-1]


def remove(i, df):
    columns_to_keep = [col for col in df.columns if col not in dropcolumn[i]]
    df = df[columns_to_keep]
    col_mapping = {old_key: new_key for item in replacement for old_key, new_key in item.items()}
    return df.rename(columns=col_mapping)


def univdata(j, i, d, finduniv):
    response = requests.get(get_url(i, j, d))
    text = response.text
    univ_data = json.loads(re.findall(finduniv, text)[0])
    return pd.DataFrame(univ_data)


def save_to_excel(df, excel_file, sheet_name):
    """保存数据到Excel文件"""
    try:
        # 使用pandas的ExcelWriter，如果文件已存在则追加新工作表
        with pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"数据已成功保存到Excel文件 {excel_file} 的工作表 {sheet_name} 中。")
    except FileNotFoundError:
        # 如果文件不存在，创建新文件
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        print(f"数据已成功保存到Excel文件 {excel_file} 的工作表 {sheet_name} 中。")
    except Exception as e:
        print(f"保存到Excel文件时出错: {e}")


def read_table_to_dataframe(table_name):
    conn = sqlite3.connect("中国大学数据集.db")
    df = pd.read_sql_query(f"SELECT * FROM {table_name};", conn)
    conn.close()
    return df


def newsave(i, years):
    finduniv = re.compile(rr[i])
    if i == 4 or i == 6:
        univ_df = univdata(years, i, 0, finduniv)
        univ_df = remove(i, univ_df)
        excel_file = f'{rn[i]}.xlsx'
        sheet_name = f'{years}年'
        save_to_excel(univ_df, excel_file, sheet_name)
    else:
        df = read_table_to_dataframe(rv[i])
        namelist = [df.iloc[:, -2].tolist(), df.iloc[:, -1].tolist()]
        for k, d in enumerate(namelist[0]):
            univ_df = univdata(years, i, d, finduniv)
            univ_df = remove(i, univ_df)
            excel_file = f'{rn[i]}.xlsx'
            sheet_name = f'{years}年{namelist[1][k]}'
            save_to_excel(univ_df, excel_file, sheet_name)


def main():
    while True:
        print("\n请输入你要爬取的表格（按7退出）：")
        print("0: 中国大学排名")
        print("1: 中国最好学科排名")
        print("2: 中国大学专业排名")
        print("3: 中国高职院校排名")
        print("4: 世界大学学术排名")
        print("5: 世界一流学科排名")
        print("6: 全球体育类院系学术排名")
        user_input = input("请选择：")
        
        if convert(user_input) == 1:
            table_index = int(user_input)
            years = ry[table_index]
            newsave(table_index, years)
        elif convert(user_input) == 0:
            print("输入有误，请重新输入。")
        else:
            print("下次见！")
            break


if __name__ == "__main__":
    main()