from function import convert, newsave1, newsave2
from data import ry


def parse_years(year_input, valid_years):
    years = set()
    normalized_input = year_input.replace('，', ',').replace('－', '-')
    
    for part in normalized_input.split(','):
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
            try:
                table_index = int(user_input)
                valid_years = ry[table_index]
                year_input = input(f"请输入要爬取的年份（可用','分隔或'-'表示区间，支持年份范围：{valid_years}）：")
                
                years = parse_years(year_input, valid_years)
                if not years:
                    print("没有有效年份，返回主菜单。")
                    continue
                
                if table_index in (4, 6):
                    newsave2(table_index, years)
                else:
                    newsave1(table_index, years)
                    
            except (ValueError, IndexError):
                print("输入有误，请重新输入。")
                
        elif convert(user_input) == 0:
            print("输入有误，请重新输入。")
        else:
            print("下次见！")
            break


if __name__ == "__main__":
    main()