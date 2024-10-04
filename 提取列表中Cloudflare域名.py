import requests
import ipaddress
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# 下载域名列表和CIDR列表
def download_lists():
    domain_list_url = 'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Global/Global.list'
    cidr_list_url = 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/refs/heads/main/Clash/Cloudflare.txt'
    
    domain_list = requests.get(domain_list_url).text.splitlines()
    cidr_list = requests.get(cidr_list_url).text.splitlines()
    
    return domain_list, cidr_list

# 提取 DOMAIN-SUFFIX 后的域名
def extract_domains(domain_list):
    return [line for line in domain_list if line.startswith('DOMAIN-SUFFIX')]

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

# Google DNS API 查询
def query_google_dns(domain, record_type):
    try:
        response = requests.get(f'https://dns.google/resolve?name={domain}&type={record_type}')
        data = response.json()
        return [answer['data'] for answer in data.get('Answer', []) if answer['type'] == (1 if record_type == "A" else 28)]
    except Exception as e:
        print(f"Google DNS API 查询失败: {e}")
        return []

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

# IPinfo API 查询
def query_ipinfo(domain):
    try:
        response = requests.get(f'https://ipinfo.io/{domain}/json')
        data = response.json()
        if 'bogon' not in data:  # 排除内部网络
            return [data['ip']] if 'ip' in data else []
        return []
    except Exception as e:
        print(f"IPinfo API 查询失败: {e}")
        return []

# 随机选择API查询IP
def get_ip_from_domain(domain):
    record_types = ["A", "AAAA"]
    api_functions = [
        lambda d, t: query_google_dns(d, t),  # Google DNS API
        lambda d, t: query_cloudflare_dns(d, t),  # Cloudflare DNS API
        lambda d, _: query_ipinfo(d)  # IPinfo API 不区分A或AAAA记录
    ]
    
    ipv4_addresses, ipv6_addresses = [], []
    for record_type in record_types:
        api_function = random.choice(api_functions)  # 随机选择API
        if record_type == "A":
            ipv4_addresses = api_function(domain, record_type)
        elif record_type == "AAAA":
            ipv6_addresses = api_function(domain, record_type)
    
    return ipv4_addresses, ipv6_addresses

# 并发处理每个域名
def process_domain(domain_line, cidr_ranges):
    domain = domain_line.split(',')[1]
    
    # 查询IPv4和IPv6
    ipv4_addresses, ipv6_addresses = get_ip_from_domain(domain)
    
    # 检查IPv4地址是否在CIDR范围内
    for ip in ipv4_addresses:
        if ip_in_cidr(ip, cidr_ranges):
            return domain_line  # 返回原始行，保留DOMAIN-SUFFIX
    
    # 检查IPv6地址是否在CIDR范围内
    for ip in ipv6_addresses:
        if ip_in_cidr(ip, cidr_ranges):
            return domain_line  # 返回原始行，保留DOMAIN-SUFFIX
    
    return None

# 主函数
def main():
    # 下载域名和CIDR列表
    domain_list, cidr_list = download_lists()
    
    # 提取域名和CIDR
    domains = extract_domains(domain_list)
    cidr_ranges = extract_cidrs(cidr_list)
    
    matching_domains = []

    # 使用线程池并发查询
    with ThreadPoolExecutor(max_workers=35) as executor:
        futures = [executor.submit(process_domain, domain_line, cidr_ranges) for domain_line in domains]
        for future in as_completed(futures):
            result = future.result()
            if result:
                matching_domains.append(result)
    
    # 保存结果到文件
    with open('matching_domains.list', 'w') as f:
        for domain_line in matching_domains:
            f.write(domain_line + '\n')
    
    print(f"匹配的域名已保存到 matching_domains.list 文件中，共 {len(matching_domains)} 个。")

# 脚本执行入口
if __name__ == "__main__":
    main()
