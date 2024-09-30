import requests
from bs4 import BeautifulSoup
import os

# 确保输出目录存在
os.makedirs("Clash", exist_ok=True)

# 需要搜索的ISP
isps_to_search = ["cloudflare"]

ipv4_results = []
ipv6_results = []

for isp in isps_to_search:
    # 进行搜索请求
    search_url = f"https://bgp.he.net/search?search%5Bsearch%5D={isp}&commit=Search"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 获取ASN号码
    asn_tags = soup.select('td a[href^="/AS"]')
    asns = [tag.text for tag in asn_tags]

    for asn in asns:
        # 获取对应的CIDR列表
        prefixes_url = f"https://bgp.he.net/{asn}#_prefixes"
        response = requests.get(prefixes_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 解析IPv4和IPv6 CIDR
        for row in soup.select('tr'):
            cidr_tag = row.select_one('td a')
            if cidr_tag:
                cidr = cidr_tag.text
                if ':' in cidr:  # 判断IPv6
                    ipv6_results.append(cidr)
                else:  # IPv4
                    ipv4_results.append(cidr)

# 保存结果到文件
with open("Clash/CloudflareCIDR.txt", "w") as ipv4_file:
    ipv4_file.write("\n".join(ipv4_results))

with open("Clash/CloudflareCIDR-v6.txt", "w") as ipv6_file:
    ipv6_file.write("\n".join(ipv6_results))

print("CIDR 结果已保存。")
