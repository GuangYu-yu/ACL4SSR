import requests
from bs4 import BeautifulSoup
import ipaddress
import os
import yaml

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
    directories = ["CF-Country", "CF", "cache"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
        print(f"{directory}文件夹已准备就绪")

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
    cidrs = []
    for suffix in ["#_prefixes", "#_prefixes6"]:
        url = f"https://bgp.he.net/{asn}{suffix}"
        print(f"获取ASN {asn} 的CIDR信息: {url}")
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', id='table_prefixes')
        if table:
            for row in table.find_all('tr')[1:]:  # 跳过表头
                cidr_link = row.find('a', href=lambda href: href and '/net/' in href)
                if cidr_link:
                    cidr = cidr_link.text.strip()
                    flag_img = row.find('div', class_='flag').find('img')
                    if flag_img and flag_img.get('title') in region_cidr:
                        region = flag_img['title']
                        try:
                            ip_network = ipaddress.ip_network(cidr)
                            cidrs.append({
                                'cidr': str(ip_network),
                                'region': region,
                                'version': 'IPv4' if ip_network.version == 4 else 'IPv6'
                            })
                            print(f"找到 CIDR: {cidr}, 地区: {region}")
                        except ValueError:
                            print(f"警告：跳过无效的CIDR: {cidr}")
    return cidrs
    
def process_cidrs(all_cidrs):
    config = {region: {'IPv4': [], 'IPv6': []} for region in region_cidr}
    all_v4 = set()
    all_v6 = set()

    for cidr_info in all_cidrs:
        cidr = cidr_info['cidr']
        region = cidr_info['region']
        version = cidr_info['version']

        config[region][version].append(cidr)
        if version == 'IPv4':
            all_v4.add(cidr)
        else:
            all_v6.add(cidr)

    # 写入配置文件
    with open("CF/Cloudflare-Config.yaml", 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    # 写入地区文件
    for region, cidrs in config.items():
        if cidrs['IPv4'] or cidrs['IPv6']:
            with open(f"CF-Country/Cloudflare-{region.replace(' ', '_')}.txt", 'w') as f:
                for version in ['IPv4', 'IPv6']:
                    f.write(f"-{version}\n")
                    for cidr in sorted(cidrs[version]):
                        f.write(f"{cidr}\n")

    # 写入全部CIDR文件
    with open("CF/Cloudflare-All.txt", 'w') as f:
        for cidr in sorted(all_v4) + sorted(all_v6):
            f.write(f"{cidr}\n")

    # 写入IPv4文件
    with open("CF/Cloudflare-IPv4.txt", 'w') as f:
        for cidr in sorted(all_v4):
            f.write(f"{cidr}\n")

    # 写入IPv6文件
    with open("CF/Cloudflare-IPv6.txt", 'w') as f:
        for cidr in sorted(all_v6):
            f.write(f"{cidr}\n")

def main():
    prepare_directories()

    all_cidrs = []

    for isp, keywords in isps_to_search.items():
        print(f"\n正在搜索ISP: {isp}")
        unique_asns = get_unique_asns(keywords)
        
        for asn, name in unique_asns.items():
            all_cidrs.extend(get_cidr(asn))

    process_cidrs(all_cidrs)

    print("配置文件已保存到CF/Cloudflare-Config.yaml")
    print("所有Cloudflare CIDR已保存到CF/Cloudflare-All.txt")
    print("Cloudflare IPv4 CIDR已保存到CF/Cloudflare-IPv4.txt")
    print("Cloudflare IPv6 CIDR已保存到CF/Cloudflare-IPv6.txt")
    print("各地区CIDR已保存到CF-Country/目录下的相应文件中")

if __name__ == "__main__":
    main()
