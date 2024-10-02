import requests
from bs4 import BeautifulSoup
import geoip2.database
import ipaddress
import os

def clear_cache():
    # 清除缓存文件
    if os.path.exists("CF-Country"):
        for file in os.listdir("CF-Country"):
            os.remove(os.path.join("CF-Country", file))
    else:
        os.mkdir("CF-Country")

def cache_asn_page(isp_keyword):
    search_url = f"https://bgp.he.net/search?search%5Bsearch%5D={isp_keyword}&commit=Search"
    print(f"缓存ASN页面: {search_url}")
    response = requests.get(search_url)
    return response.content

def get_unique_asns(isp_keywords):
    asns = {}
    for keyword in isp_keywords:
        page_content = cache_asn_page(keyword)
        soup = BeautifulSoup(page_content, 'html.parser')
        print(f"从关键词 '{keyword}' 获取ASN...")
        for row in soup.find_all('tr'):
            if 'ASN' in row.text:
                if row.find('img') and row.find('img')['title'] == "China":
                    asn = row.find('a').text.strip()
                    name = row.find_all('td')[2].text.strip()
                    asns[asn] = name
                    print(f"发现 {asn}，名称 {name}")
    return asns

def get_cidr(asn):
    cidrs = []
    for suffix in ["#_prefixes", "#_prefixes6"]:
        asn_page = requests.get(f"https://bgp.he.net/{asn}{suffix}").content
        soup = BeautifulSoup(asn_page, 'html.parser')
        print(f"获取ASN {asn} 的CIDR信息...")
        for row in soup.find_all('tr'):
            cidr_link = row.find('a')
            if cidr_link and 'net' in cidr_link['href']:
                cidr = cidr_link.text.strip()
                try:
                    ipaddress.ip_network(cidr)
                    region_img = row.find('div', class_='flag').find('img')
                    region = region_img['title'] if region_img else None
                    cidrs.append((cidr, region))
                    print(f"找到 CIDR: {cidr}, 地区: {region}")
                except ValueError:
                    print(f"警告：跳过无效的CIDR: {cidr}")
    return cidrs

def process_cidrs(all_cidrs):
    for cidr, region in all_cidrs:
        if region is None:
            region = "Unknown"  # 将None替换为"Unknown"
        
        file_path = f"CF-Country/Cloudflare-{region.replace(' ', '_')}.txt"
        with open(file_path, 'a') as f:
            f.write(cidr + '\n')

def main():
    clear_cache()
    isps_to_search = {
        "Cloudflare": ["cloudflare", "cf"]
    }
    
    for isp, keywords in isps_to_search.items():
        print(f"\n正在搜索ISP: {isp}")
        unique_asns = get_unique_asns(keywords)
        all_cidrs = []
        
        for asn in unique_asns.keys():
            all_cidrs.extend(get_cidr(asn))
        
        process_cidrs(all_cidrs)

if __name__ == "__main__":
    main()
