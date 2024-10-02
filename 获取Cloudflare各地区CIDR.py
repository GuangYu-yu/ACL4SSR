import requests
from bs4 import BeautifulSoup
import ipaddress
import os
import yaml
import geoip2.database

isps_to_search = {
    "Cloudflare": ["cloudflare"],
}

# 下载并加载GeoLite2-Country.mmdb
def load_geoip_database():
    db_path = "GeoLite2-Country.mmdb"
    if not os.path.exists(db_path):
        print("正在下载 GeoLite2-Country.mmdb...")
        response = requests.get("https://github.com/P3TERX/GeoLite.mmdb/raw/download/GeoLite2-Country.mmdb")
        with open(db_path, 'wb') as f:
            f.write(response.content)
    return geoip2.database.Reader(db_path)

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

def get_cidr(asn, geoip_reader):
    cidrs = []
    
    for suffix in ["#_prefixes", "#_prefixes6"]:
        url = f"https://bgp.he.net/{asn}{suffix}"
        print(f"获取ASN {asn} 的CIDR信息: {url}")
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"正在解析 ASN {asn} 的页面...")
        for row in soup.find_all('tr')[1:]:  # 跳过表头
            cidr_link = row.find('a', href=lambda href: href and '/net/' in href)
            if cidr_link:
                cidr = cidr_link.text.strip()
                try:
                    ip_network = ipaddress.ip_network(cidr)  # 验证CIDR
                    # 使用GeoIP数据库获取地区
                    region = '未知'
                    for ip in ip_network:
                        try:
                            response = geoip_reader.country(str(ip))
                            region = response.country.name
                            break  # 只需找到一个有效的地区即可
                        except Exception as e:
                            print(f"无法获取地区信息: {e}")
                    
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
    config = {}
    all_v4 = set()
    all_v6 = set()

    for cidr_info in all_cidrs:
        cidr = cidr_info['cidr']
        region = cidr_info['region'] if cidr_info['region'] is not None else 'None'
        version = cidr_info['version']

        if region not in config:
            config[region] = {'IPv4': [], 'IPv6': []}

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
    geoip_reader = load_geoip_database()

    all_cidrs = []

    for isp, keywords in isps_to_search.items():
        print(f"\n正在搜索ISP: {isp}")
        unique_asns = get_unique_asns(keywords)
        
        for asn, name in unique_asns.items():
            all_cidrs.extend(get_cidr(asn, geoip_reader))

    process_cidrs(all_cidrs)

    geoip_reader.close()
    print("配置文件已保存到CF/Cloudflare-Config.yaml")
    print("所有Cloudflare CIDR已保存到CF/Cloudflare-All.txt")
    print("Cloudflare IPv4 CIDR已保存到CF/Cloudflare-IPv4.txt")
    print("Cloudflare IPv6 CIDR已保存到CF/Cloudflare-IPv6.txt")
    print("各地区CIDR已保存到CF-Country/目录下的相应文件中")

if __name__ == "__main__":
    main()
