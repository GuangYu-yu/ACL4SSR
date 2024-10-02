import requests
from bs4 import BeautifulSoup
import os
import shutil
import re

# 函数：从指定的ASN页面获取CIDR（支持缓存）
def get_cidrs(asn, cache_dir):
    cache_file = os.path.join(cache_dir, f"{asn}_prefixes.html")
    
    if not os.path.exists(cache_file):
        print(f"正在下载并缓存ASN {asn} 的prefixes网页...")
        asn_url = f"https://bgp.he.net/{asn}#_prefixes"
        response = requests.get(asn_url)
        with open(cache_file, "w", encoding="utf-8") as file:
            file.write(response.text)
    else:
        print(f"使用缓存的ASN {asn} 的prefixes网页...")

    with open(cache_file, "r", encoding="utf-8") as file:
        content = file.read()

    soup = BeautifulSoup(content, "html.parser")
    cidrs = []
    
    for row in soup.find_all('tr'):
        cidr = row.find('a')
        if cidr and '/net/' in cidr['href']:
            cidr_text = cidr.text
            if re.match(r'^\d{1,3}(\.\d{1,3}){3}(\/\d{1,2})?$|^[0-9a-fA-F:]+(\/\d{1,3})?$', cidr_text):
                cidrs.append(cidr_text)

    return cidrs

# 函数：从搜索页面提取ASN编号
def get_asns(isp_name):
    search_url = f"https://bgp.he.net/search?search%5Bsearch%5D={isp_name}&commit=Search"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.content, "html.parser")
    
    asns = []
    for row in soup.find_all('tr'):
        asn_link = row.find('a')
        if asn_link and 'AS' in asn_link.text:
            asns.append(asn_link.text)
    
    return asns

# 清空缓存目录
def clear_cache(cache_dir):
    if os.path.exists(cache_dir):
        print(f"清空缓存目录 {cache_dir}...")
        shutil.rmtree(cache_dir)
    os.makedirs(cache_dir)

# 函数：主流程，遍历ISP，获取ASN和CIDR并保存到两个txt文件
def main(isps, cache_dir, output_ipv4_file, output_ipv6_file, output_combined_file):
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    with open(output_ipv4_file, mode='w', encoding='utf-8') as ipv4_file, \
         open(output_ipv6_file, mode='w', encoding='utf-8') as ipv6_file:
        
        for isp in isps:
            print(f"正在搜索ISP: {isp}")
            asns = get_asns(isp)
            for asn in asns:
                print(f"ASN: {asn}")
                cidrs = get_cidrs(asn, cache_dir)
                
                for cidr in cidrs:
                    if ':' in cidr:
                        ipv6_file.write(f"{cidr}\n")
                    else:
                        ipv4_file.write(f"{cidr}\n")
                    
                print(f"{len(cidrs)} 个CIDR已保存至文件。")
            print("-" * 40)
    
    clear_cache(cache_dir)

    # 合并CIDR到一个文件
    with open(output_combined_file, mode='w', encoding='utf-8') as combined_file:
        with open(output_ipv4_file, mode='r', encoding='utf-8') as ipv4_file:
            combined_file.writelines(ipv4_file.readlines())
        with open(output_ipv6_file, mode='r', encoding='utf-8') as ipv6_file:
            combined_file.writelines(ipv6_file.readlines())

# 输入ISP列表、缓存目录和输出文件路径
isps_to_search = ["cloudflare"]  # 需要搜索的ISP
cache_dir = "cache"  # 缓存目录
output_ipv4_file = "Clash/CloudflareCIDR.txt"  # 输出IPv4 CIDR的txt文件
output_ipv6_file = "Clash/CloudflareCIDR-v6.txt"  # 输出IPv6 CIDR的txt文件
output_combined_file = "Clash/Cloudflare.txt"  # 合并后的文件

if __name__ == "__main__":
    main(isps_to_search, cache_dir, output_ipv4_file, output_ipv6_file, output_combined_file)
