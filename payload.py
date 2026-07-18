import requests
import re

url = "https://www.shanghairanking.cn/_nuxt/static/1784027557/institution/payload.js"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36 Edg/150.0.0.0",
    "Referer": "https://www.shanghairanking.cn/institution/huazhong-university-of-science-and-technology",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",  # 可带可不带，不影响
    "Accept-Language": "zh-CN,zh;q=0.9",
}

print(f"正在请求: {url}")
resp = requests.get(url, headers=headers)
resp.raise_for_status()

# 直接对原始字节进行 UTF-8 解码（忽略无效字符，实际上都是有效字符）
source_code = resp.content.decode('utf-8', errors='ignore')

s0 = re.findall(r'\(function\((.*?)\)', source_code)[0]
s1 = re.findall(r'mutations:\[\]\}\}\((.*?)\)', source_code)[0]
use = [s0.split(','), s1.split(',')]
print(use)