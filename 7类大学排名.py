# 7类大学排名爬取主函数程序

import os
from function import convert,newsave,newsave2

def main():
    while True:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        i = input('请输入你要爬取的表格（按7退出）：')
        # 对于i值，输入0为中国大学排名，输入1为中国最好学科排名，输入2为中国大学专业排名，输入3为中国高职院校排名，
        # 输入4为世界大学学术排名，输入5为世界一流学科排名，输入6为全球体育系院校学术排名，输入7退出循环，输入其它值均无效。
        if convert(i) == 1:
            i = int(i)
            if i != 4 and i != 6:
                newsave(i,current_dir)
            else:
                newsave2(i,current_dir)
        elif convert(i) == 0:
            print('输入有误，请重新输入。')
        else:
            print('下次见！')
            break

if __name__ == "__main__":
    main()