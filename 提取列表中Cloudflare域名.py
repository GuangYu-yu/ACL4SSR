import requests
import concurrent.futures
import os
import re
import ipaddress
import uuid

# 定义文件路径
GLOBAL_LIST_URL = 'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Global/Global.list'
DOMAIN_LIST_URLS = [
    'https://github.com/Potterli20/file/releases/download/dns-hosts-all/dnshosts-all-domain-whitelist_full.txt',
    'https://raw.githubusercontent.com/GuangYu-yu/About-Cloudflare/refs/heads/main/大量优选域名.txt'
]

def fetch_domains(url):
    """获取域名列表"""
    response = requests.get(url)
    response.raise_for_status()
    domains = set()
    for line in response.text.splitlines():
        if line.startswith('DOMAIN-SUFFIX,') or line.startswith('DOMAIN,'):
            domains.add(line)
    return domains

def fetch_additional_domains(urls):
    """获取额外的域名列表"""
    domains = set()
    for url in urls:
        response = requests.get(url)
        response.raise_for_status()
        domains.update(response.text.splitlines())
    return domains

def cache_page(url):
    """缓存网页内容到本地文件"""
    response = requests.get(url)
    response.raise_for_status()
    cache_file = f'cache_{uuid.uuid4()}.html'
    with open(cache_file, 'w', encoding='utf-8') as f:
        f.write(response.text)
    return cache_file

def clear_cache(cache_file):
    """删除缓存文件"""
    if os.path.exists(cache_file):
        os.remove(cache_file)

def check_cloudflare_ip_via_nslookup(domain):
    """通过 nslookup 查询 Cloudflare IP"""
    try:
        url = f'https://www.nslookup.io/domains/{domain}/dns-records/'
        cache_file = cache_page(url)
        with open(cache_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'Hosted by Cloudflare, Inc.' in content:
                ip_matches = re.findall(r'<span>([\d\.a-fA-F:]+)</span>', content)
                clear_cache(cache_file)
                return domain, set(ip_matches)
    except Exception as e:
        print(f"通过nslookup检查 {domain} 时出错: {e}")
    clear_cache(cache_file)
    return None

def check_cloudflare_ip_via_bgp(domain):
    """通过 bgp.he.net 查询 Cloudflare IP"""
    try:
        url = f'https://bgp.he.net/dns/{domain}#_ipinfo'
        cache_file = cache_page(url)
        with open(cache_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'Cloudflare' in content:
                ip_matches = re.findall(r'<a href="/ip/([\d\.a-fA-F:]+)" title="[\d\.a-fA-F:]+">', content)
                clear_cache(cache_file)
                return domain, set(ip_matches)
    except Exception as e:
        print(f"通过bgp.he.net检查 {domain} 时出错: {e}")
    clear_cache(cache_file)
    return None

def process_domain(domain, index):
    """处理每个域名，轮流查询其 Cloudflare IP"""
    if index % 2 == 0:
        return check_cloudflare_ip_via_nslookup(domain)
    else:
        return check_cloudflare_ip_via_bgp(domain)

def main():
    """主函数，执行查询和结果保存"""
    global_domains = fetch_domains(GLOBAL_LIST_URL)
    additional_domains = fetch_additional_domains(DOMAIN_LIST_URLS)
    
    all_domains = list(global_domains.union(additional_domains))
    matching_domain_lines = set()
    matching_domains = set()
    all_cloudflare_ips = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_domain, domain.split(',')[-1], i): domain for i, domain in enumerate(all_domains)}
        for future in concurrent.futures.as_completed(futures):
            domain = futures[future]
            try:
                result = future.result()
                if result:
                    if domain in global_domains:
                        matching_domain_lines.add(domain)
                    matching_domains.add(result[0])
                    all_cloudflare_ips.update(result[1])
            except Exception as e:
                print(f"处理域名 {domain} 时出错: {e}")

    # 读取现有的优选域名
    existing_domains = set()
    if os.path.exists('优选域名.txt'):
        with open('优选域名.txt', 'r') as f:
            existing_domains = set(f.read().splitlines())

    # 合并并去重域名
    all_matching_domains = matching_domains.union(existing_domains)

    # 读取现有的 IP 地址
    existing_ipv4 = set()
    existing_ipv6 = set()
    if os.path.exists('优选域名ip.txt'):
        with open('优选域名ip.txt', 'r') as f:
            current_section = None
            for line in f:
                line = line.strip()
                if line == "# IPv4 地址":
                    current_section = "ipv4"
                elif line == "# IPv6 地址":
                    current_section = "ipv6"
                elif line and not line.startswith('#'):
                    if current_section == "ipv4":
                        existing_ipv4.add(line)
                    elif current_section == "ipv6":
                        existing_ipv6.add(line.lower())

    # 分离IPv4和IPv6地址
    ipv4_addresses = set()
    ipv6_addresses = set()

    for ip in all_cloudflare_ips:
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.version == 4:
                ipv4_addresses.add(str(ip_obj))
            else:
                ipv6_addresses.add(str(ip_obj).lower())
        except ValueError:
            print(f"无效的IP地址: {ip}")

    # 合并 IP 地址
    all_ipv4 = ipv4_addresses.union(existing_ipv4)
    all_ipv6 = ipv6_addresses.union(existing_ipv6)

    # 排序 IP 地址
    sorted_ipv4 = sorted(all_ipv4, key=lambda ip: ipaddress.IPv4Address(ip))
    sorted_ipv6 = sorted(all_ipv6, key=lambda ip: ipaddress.IPv6Address(ip))

    # 保存匹配的域名（带前缀）到文件
    with open('matching_domains.list', 'w', encoding='utf-8') as f:
        for domain_line in sorted(matching_domain_lines):
            f.write(f"{domain_line}\n")

    # 保存优选域名（不带前缀）到文件
    with open('优选域名.txt', 'w', encoding='utf-8') as f:
        for domain in sorted(all_matching_domains):
            f.write(f"{domain}\n")

    # 保存所有 Cloudflare IP 地址到文件
    with open('优选域名ip.txt', 'w', encoding='utf-8') as f:
        f.write("# IPv4 地址\n")
        for ip in sorted_ipv4:
            f.write(f"{ip}\n")
        f.write("\n# IPv6 地址\n")
        for ip in sorted_ipv6:
            f.write(f"{ip}\n")

    print(f"匹配的域名（带前缀）已保存到 matching_domains.list 文件中，共 {len(matching_domain_lines)} 个。")
    print(f"优选域名（不带前缀）已保存到 优选域名.txt 文件中，共 {len(all_matching_domains)} 个。")
    print(f"提取的 Cloudflare IP 已保存到 优选域名ip.txt 文件中，共 {len(sorted_ipv4) + len(sorted_ipv6)} 个。")
    print(f"其中 IPv4 地址 {len(sorted_ipv4)} 个，IPv6 地址 {len(sorted_ipv6)} 个。")

if __name__ == '__main__':
    main()
