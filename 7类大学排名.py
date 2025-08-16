# 7类大学排名爬取主函数程序

import os
from function import convert, newsave, newsave2
from data import ry

def parse_years(year_input, valid_years):
    years = set()
    year_input = year_input.replace('，', ',').replace('－', '-')
    for part in year_input.split(','):
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                years.update(range(start, end + 1))
            except ValueError:
                print(f"年份区间输入有误：{part}")
        else:
            try:
                years.add(int(part))
            except ValueError:
                print(f"年份输入有误：{part}")
    valid = [y for y in years if y in valid_years]
    invalid = [y for y in years if y not in valid_years]
    if invalid:
        print(f"以下年份无效或不在可选范围内，将跳过：{invalid}")
    return valid

def main():
    while True:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        i = input('请输入你要爬取的表格（按7退出）：')
        if convert(i) == 1:
            i = int(i)
            valid_years = ry[i]
            year_input = input(f"请输入要爬取的年份（可用','分隔或'-'表示区间，支持年份范围：{valid_years}）：")
            years = parse_years(year_input, valid_years)
            if not years:
                print("没有有效年份，返回主菜单。")
                continue
            if i != 4 and i != 6:
                newsave(i, current_dir, years)
            else:
                newsave2(i, current_dir, years)
        elif convert(i) == 0:
            print('输入有误，请重新输入。')
        else:
            print('下次见！')
            break

if __name__ == "__main__":
    main()