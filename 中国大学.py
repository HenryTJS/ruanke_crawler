# 中国大学数据爬取主函数程序

import requests
import re
from data import number,finduniv
from function import univdata2

def main():
    jsfilepath = 'https://www.shanghairanking.cn/_nuxt/static/' + number + '/institution/payload.js'
    jsresponse = requests.get(jsfilepath)
    text = jsresponse.text
    univ = re.findall(finduniv,text)[0]
    univdata = univdata2(univ,text)
    univdata["办学层次"] = univdata["办学层次"].replace({
        "10": "普通本科",
        "15": "职业本科",
        "20": "高职（专科）"
    })
    file_path = '中国大学表.xlsx'
    univdata.to_excel(file_path,index=False)
    print(f"数据已成功保存到{file_path}文件中。")

if __name__ == "__main__":
    main()