# 一些运行中使用到的数据

import re

number = '1762223212'  # number每隔几天网站更新会更换一次，README.md文件内有获取此数字的方法。

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
    [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
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