import requests
from bs4 import BeautifulSoup
import os
import shutil
import re
import ipaddress

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

# 函数：合并CIDR
def merge_cidrs(cidrs):
    ip_networks = [ipaddress.ip_network(cidr) for cidr in cidrs]
    merged = ipaddress.collapse_addresses(ip_networks)
    return [str(net) for net in merged]

# 函数：排序CIDR
def sort_cidrs(cidrs):
    ipv4_cidrs = sorted([cidr for cidr in cidrs if ':' not in cidr], key=lambda x: (ipaddress.ip_network(x).network_address, ipaddress.ip_network(x).prefixlen))
    ipv6_cidrs = sorted([cidr for cidr in cidrs if ':' in cidr], key=lambda x: (ipaddress.ip_network(x).network_address, ipaddress.ip_network(x).prefixlen))
    return ipv4_cidrs, ipv6_cidrs

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

    all_ipv4_cidrs = []
    all_ipv6_cidrs = []

    for isp in isps:
        print(f"正在搜索ISP: {isp}")
        asns = get_asns(isp)
        for asn in asns:
            print(f"ASN: {asn}")
            cidrs = get_cidrs(asn, cache_dir)
            ipv4_cidrs, ipv6_cidrs = sort_cidrs(cidrs)
            all_ipv4_cidrs.extend(ipv4_cidrs)
            all_ipv6_cidrs.extend(ipv6_cidrs)

            print(f"{len(cidrs)} 个CIDR已保存至列表。")
        print("-" * 40)
    
    # 合并和排序CIDR
    all_ipv4_cidrs = merge_cidrs(all_ipv4_cidrs)
    all_ipv6_cidrs = merge_cidrs(all_ipv6_cidrs)

    # 保存结果到文件
    with open(output_ipv4_file, mode='w', encoding='utf-8') as ipv4_file:
        ipv4_file.write("\n".join(all_ipv4_cidrs) + "\n")
    with open(output_ipv6_file, mode='w', encoding='utf-8') as ipv6_file:
        ipv6_file.write("\n".join(all_ipv6_cidrs) + "\n")
    
    # 合并CIDR到一个文件
    with open(output_combined_file, mode='w', encoding='utf-8') as combined_file:
        combined_file.write("\n".join(all_ipv4_cidrs) + "\n")
        combined_file.write("\n".join(all_ipv6_cidrs) + "\n")

    clear_cache(cache_dir)

# 输入ISP列表、缓存目录和输出文件路径
isps_to_search = ["cloudflare"]  # 需要搜索的ISP
cache_dir = "cache"  # 缓存目录
output_ipv4_file = "Clash/CloudflareCIDR.txt"  # 输出IPv4 CIDR的txt文件
output_ipv6_file = "Clash/CloudflareCIDR-v6.txt"  # 输出IPv6 CIDR的txt文件
output_combined_file = "Clash/Cloudflare.txt"  # 合并后的文件

if __name__ == "__main__":
    main(isps_to_search, cache_dir, output_ipv4_file, output_ipv6_file, output_combined_file)
