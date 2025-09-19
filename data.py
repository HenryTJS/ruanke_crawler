# 一些运行中使用到的数据

import re

number = '1758088267'  # number每隔几天网站更新会更换一次，README.md文件内有获取此数字的方法。

rv = [
    'bcur', 'bcsr', 'bcmr', 'bcvcr', 'arwu', 'gras', 'grsssd'
]

rr = [
    [r'bcurTypes:\[(.*?)\]', r'id:(.*?),', r'nameCn:(.*?),', r'"rankings":(.*?),"inds"'],
    [r'subjs:\[(.*?)\}\]\},', r'code:(.*?),', r'nameCn:(.*?),', r'"rankings":(.*?),"pctTops"'],
    [r'\{(.*?)return', r'code=(.*?);', r'name=(.*?);', r'"rankings":(.*?),"region"'],
    [r'bcvcrTypes:\[(.*?)\]', r'id:(.*?),', r'nameCn:(.*?),', r'"rankings":(.*?),"inds"'],
    ['', '', '', r'"rankings":(.*?),"indicators"'],
    [r'subjs:\[(.*?)\}\]\},', r'code:(.*?),', r'nameCn:(.*?),', r'"rankings":(.*?),"inds"'],
    ['', '', '', r'"rankings":(.*?),"indicators"']
]

ry = [
    [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
    [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
    [2021, 2022, 2023, 2024, 2025],
    [2023, 2024, 2025],
    [2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
    [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024],
    [2016, 2017, 2018, 2020, 2021, 2022, 2023, 2024]
]  # 分别代表每一个排名对应存在的年份，如果有出新的年份对应排名则在列表后面补上即可。

rn = [
    '中国大学排名', '中国最好学科排名', '中国大学专业排名', '中国高职院校排名',
    '世界大学学术排名', '世界一流学科排名', '全球体育类院系学术排名'
]

findfunction = re.compile(r'\(function\((.*?)\)')
findoutput = re.compile(r'\[]}}\((.*?)\)\)\)')
finduniv = re.compile(r'\{(.*?);return')

dropcolumn = [
    ['univUp', 'univLogo', 'liked', 'inbound', 'univLikeCount', 'univTags', 'indData', 'univNameRemark', 'univNameEn', 'rankChange', 'rankOverall'],
    ['univCode', 'univUp', 'univLogo', 'liked', 'inbound', 'univLikeCount', 'doctoralDegree', 'focusSubj', 'contrastRanking', 'rankPctTopNum'],
    ['univCode', 'univUp', 'univLogo', 'city', 'liked', 'inbound', 'univLikeCount', 'univTags', 'indGrades', 'province'],
    ['univUp', 'isVocational', 'univLogo', 'liked', 'univLikeCount', 'univTags', 'indData', 'outdated', 'univNameEn', 'rankOverall'],
    ['univUp', 'univLogo', 'regionLogo', 'indData'],
    ['univUp', 'univUpEn', 'univLogo', 'inbound', 'univLikeCount', 'liked', 'indData', 'regionRanking', 'univCode'],
    ['univUp', 'unitNameEn', 'univLogo', 'regionLogo', 'indData', 'regionRanking'],
    ['univEnv', 'logo', 'isVocational', 'rankBcur', 'liked', 'inbound', 'cateCode', 'charCode', 'level', 'univLikeCount', 'up'],
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
    {'regionRanking': '地区排名'}
]