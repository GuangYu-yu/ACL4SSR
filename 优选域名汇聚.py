import requests
import ipaddress
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# 下载域名列表和CIDR列表
def download_lists():
    # 将多个域名列表的 URL 放在一个列表中，方便后续添加更多
    domain_list_urls = [
        'https://github.com/Potterli20/file/releases/download/dns-hosts-all/dnshosts-all-domain-whitelist_full.txt',
        'https://raw.githubusercontent.com/GuangYu-yu/About-Cloudflare/refs/heads/main/大量优选域名.txt'
    ]
    
    # 下载并合并所有域名列表
    domain_list = []
    for url in domain_list_urls:
        domain_list += requests.get(url).text.splitlines()
    
    # 下载 CIDR 列表
    cidr_list_url = 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/refs/heads/main/Clash/Cloudflare.txt'
    cidr_list = requests.get(cidr_list_url).text.splitlines()
    
    return domain_list, cidr_list

# 提取 CIDR 范围
def extract_cidrs(cidr_list):
    return [line for line in cidr_list if re.match(r'[\d:a-fA-F]+/[0-9]+', line)]

# 检查IP是否在CIDR内
def ip_in_cidr(ip, cidr_list):
    for cidr in cidr_list:
        try:
            if ipaddress.ip_address(ip) in ipaddress.ip_network(cidr, strict=False):
                return True
        except ValueError:
            continue
    return False

# Cloudflare DNS Resolver API 查询
def query_cloudflare_dns(domain, record_type):
    try:
        headers = {
            'Accept': 'application/dns-json',
        }
        response = requests.get(f'https://cloudflare-dns.com/dns-query?name={domain}&type={record_type}', headers=headers)
        data = response.json()
        return [answer['data'] for answer in data.get('Answer', []) if answer['type'] == (1 if record_type == "A" else 28)]
    except Exception as e:
        print(f"Cloudflare DNS API 查询失败: {e}")
        return []

# 查询域名的IP地址
def get_ip_from_domain(domain):
    ipv4_addresses = query_cloudflare_dns(domain, "A")
    ipv6_addresses = query_cloudflare_dns(domain, "AAAA")
    return ipv4_addresses, ipv6_addresses

# 并发处理每个域名
def process_domain(domain, cidr_ranges):
    # 查询IPv4和IPv6
    ipv4_addresses, ipv6_addresses = get_ip_from_domain(domain)
    
    # 检查IPv4地址是否在CIDR范围内
    for ip in ipv4_addresses:
        if ip_in_cidr(ip, cidr_ranges):
            return domain
    
    # 检查IPv6地址是否在CIDR范围内
    for ip in ipv6_addresses:
        if ip_in_cidr(ip, cidr_ranges):
            return domain
    
    return None

# 主函数
def main():
    # 下载域名和CIDR列表
    domain_list, cidr_list = download_lists()
    
    # 提取CIDR
    cidr_ranges = extract_cidrs(cidr_list)
    
    preferred_domains = []

    # 使用线程池并发查询
    with ThreadPoolExecutor(max_workers=35) as executor:
        futures = [executor.submit(process_domain, domain, cidr_ranges) for domain in domain_list]
        for future in as_completed(futures):
            domain = future.result()
            if domain:
                preferred_domains.append(domain)
    
    # 保存提取的优选域名到 优选域名汇聚.txt
    with open('优选域名汇聚.txt', 'w') as f:
        for domain in preferred_domains:
            f.write(domain + '\n')
    
    print(f"优选的域名已保存到 优选域名汇聚.txt 文件中，共 {len(preferred_domains)} 个。")

# 脚本执行入口
if __name__ == "__main__":
    main()
