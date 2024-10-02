import requests
from bs4 import BeautifulSoup
import ipaddress
import os

# 添加region_cidr列表
region_cidr = [
    "Hong Kong", "Taiwan", "Japan", "South Korea", "India", "Singapore", "Thailand", "Vietnam", 
    "Philippines", "Malaysia", "France", "Germany", "United Kingdom", "Italy", "Spain", "Russia", 
    "Sweden", "Switzerland", "Poland", "United States", "Canada", "Mexico", "Cuba", "Guatemala", 
    "Dominican Republic", "Costa Rica", "Panama", "Honduras", "Jamaica", "Brazil", "Argentina", 
    "Chile", "Colombia", "Peru", "Venezuela", "Uruguay", "Paraguay", "Bolivia", "Ecuador", 
    "South Africa", "Nigeria", "Egypt", "Kenya", "Algeria", "Morocco", "Ghana", "Ethiopia", 
    "Tanzania", "Senegal", "Australia", "New Zealand", "Fiji", "Papua New Guinea", "Solomon Islands", 
    "Vanuatu", "Tonga", "Wallis and Futuna", "Nauru", "Tuvalu", "Saudi Arabia", "United Arab Emirates", 
    "Iran", "Iraq", "Israel", "Jordan", "Kuwait", "Qatar"
]

isps_to_search = {
    "Cloudflare": ["cloudflare"],
}

def prepare_directories():
    directories = ["CF-Country", "CF"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"{directory}文件夹已创建")
        else:
            print(f"{directory}文件夹已存在")

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
                asn = row.find('a').text.strip()
                name = row.find_all('td')[2].text.strip()
                asns[asn] = name
                print(f"发现 {asn}，名称 {name}")
    return asns

def get_cidr(asn):
    cidrs = {region: [] for region in region_cidr}
    
    for suffix in ["#_prefixes", "#_prefixes6"]:
        asn_page = requests.get(f"https://bgp.he.net/{asn}{suffix}").content
        soup = BeautifulSoup(asn_page, 'html.parser')
        print(f"获取ASN {asn} 的CIDR信息...")
        for row in soup.find_all('tr'):
            cidr_link = row.find('a')
            if cidr_link and 'net' in cidr_link['href']:
                cidr = cidr_link.text.strip()
                flag_img = row.find('img', alt=True, title=True)
                if flag_img and flag_img['title'] in region_cidr:
                    region = flag_img['title']
                    try:
                        ip_network = ipaddress.ip_network(cidr)
                        cidrs[region].append(str(ip_network))
                    except ValueError:
                        print(f"警告：跳过无效的CIDR: {cidr}")
    
    for region, ips in cidrs.items():
        if ips:
            print(f"ASN {asn} 在 {region} 发现 {len(ips)} 个CIDR")
    
    return cidrs

def merge_and_sort_cidrs(cidrs):
    cidr_set = set()
    for cidr in cidrs:
        try:
            cidr_set.add(ipaddress.ip_network(cidr))
        except ValueError:
            print(f"警告：跳过无效的CIDR: {cidr}")
    print(f"开始合并 {len(cidr_set)} CIDR，原始数量: {len(cidrs)}")
    merged = list(ipaddress.collapse_addresses(cidr_set))
    print(f"CIDR合并完成，合并后数量: {len(merged)}")
    return sorted(str(cidr) for cidr in merged)

def main():
    prepare_directories()

    all_cloudflare_cidrs = []

    for isp, keywords in isps_to_search.items():
        print(f"\n正在搜索ISP: {isp}")
        unique_asns = get_unique_asns(keywords)
        
        all_cidrs = {region: [] for region in region_cidr}
        
        for asn, name in unique_asns.items():
            asn_cidrs = get_cidr(asn)
            for region in region_cidr:
                all_cidrs[region].extend(asn_cidrs[region])
                all_cloudflare_cidrs.extend(asn_cidrs[region])
        
        for region, cidrs in all_cidrs.items():
            if cidrs:
                merged_cidrs = merge_and_sort_cidrs(cidrs)
                output_filename = f"CF-Country/Cloudflare-{region.replace(' ', '_')}.txt"
                with open(output_filename, 'w') as f:
                    for cidr in merged_cidrs:
                        f.write(cidr + '\n')
                print(f"已保存 {region} 的CIDR到文件: {output_filename}")

    # 处理所有Cloudflare CIDR
    all_cloudflare_cidrs = merge_and_sort_cidrs(all_cloudflare_cidrs)
    all_cloudflare_ipv4 = []
    all_cloudflare_ipv6 = []

    with open("CF/Cloudflare-All.txt", 'w') as f:
        for cidr in all_cloudflare_cidrs:
            f.write(cidr + '\n')
            if ':' in cidr:
                all_cloudflare_ipv6.append(cidr)
            else:
                all_cloudflare_ipv4.append(cidr)

    # 保存IPv4和IPv6
    with open("CF/Cloudflare-IPv4.txt", 'w') as f:
        for cidr in all_cloudflare_ipv4:
            f.write(cidr + '\n')
    
    with open("CF/Cloudflare-IPv6.txt", 'w') as f:
        for cidr in all_cloudflare_ipv6:
            f.write(cidr + '\n')

    print("所有Cloudflare CIDR已保存到CF/Cloudflare-All.txt")
    print("Cloudflare IPv4 CIDR已保存到CF/Cloudflare-IPv4.txt")
    print("Cloudflare IPv6 CIDR已保存到CF/Cloudflare-IPv6.txt")

if __name__ == "__main__":
    main()
