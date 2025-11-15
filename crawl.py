from function import convert, newsave1, newsave2
from data import ry


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
            
            if table_index in (4, 6):
                newsave2(table_index, years)
            else:
                newsave1(table_index, years)
                
        elif convert(user_input) == 0:
            print("输入有误，请重新输入。")
        else:
            print("下次见！")
            break


if __name__ == "__main__":
    main()