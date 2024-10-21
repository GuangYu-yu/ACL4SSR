import requests
import concurrent.futures
import re
import ipaddress
import os
import uuid

# 定义文件路径
URL_WITH_PREFIX = 'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Global/Global.list'
CLOUDFLARE_CIDR_URL = 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/refs/heads/main/Clash/Cloudflare.txt'

def fetch_domains_with_prefix(url):
    """获取带前缀的域名列表"""
    response = requests.get(url)
    response.raise_for_status()
    domains_with_prefix = set()
    for line in response.text.splitlines():
        if line.startswith('DOMAIN-SUFFIX,') or line.startswith('DOMAIN,'):
            domains_with_prefix.add(line.strip())
    return domains_with_prefix

def fetch_cloudflare_cidrs(url):
    """获取 Cloudflare 的 CIDR 列表"""
    response = requests.get(url)
    response.raise_for_status()
    cloudflare_cidrs = [ipaddress.ip_network(cidr.strip()) for cidr in response.text.splitlines() if cidr.strip()]
    return cloudflare_cidrs

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

def check_ips_via_bgp(domain):
    """通过 bgp.he.net 查询域名对应的 IP 地址"""
    try:
        url = f'https://bgp.he.net/dns/{domain}#_ipinfo'
        cache_file = cache_page(url)
        with open(cache_file, 'r', encoding='utf-8') as f:
            content = f.read()
            ip_matches = re.findall(r'<a href="/ip/([\d\.a-fA-F:]+)" title="[\d\.a-fA-F:]+">', content)
        clear_cache(cache_file)
        return domain, set(ip_matches)
    except Exception as e:
        print(f"通过bgp.he.net检查 {domain} 时出错: {e}")
    clear_cache(cache_file)
    return None

def process_domain(domain):
    """处理每个域名，查询其 IP"""
    return check_ips_via_bgp(domain.split(',')[1])

def main():
    """主函数，执行查询和结果保存"""
    # 从带前缀的域名获取
    domains_with_prefix = fetch_domains_with_prefix(URL_WITH_PREFIX)

    # 获取 Cloudflare CIDR 列表
    cloudflare_cidrs = fetch_cloudflare_cidrs(CLOUDFLARE_CIDR_URL)

    # 存储每个域名及其对应的 IP
    domain_ip_map = {}

    # 并发查询所有域名对应的 IP
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_domain, domain): domain for domain in domains_with_prefix}
        for future in concurrent.futures.as_completed(futures):
            domain_with_prefix = futures[future]
            try:
                result = future.result()
                if result:
                    domain, ips = result
                    domain_ip_map[domain_with_prefix] = ips
            except Exception as e:
                print(f"处理域名 {domain_with_prefix} 时出错: {e}")

    # 检查 IP 是否命中 Cloudflare CIDR，并保存匹配的域名
    matching_domains = set()
    for domain_with_prefix, ips in domain_ip_map.items():
        cloudflare_ips = {ip for ip in ips if is_ip_in_cloudflare(ip, cloudflare_cidrs)}
        if cloudflare_ips:
            matching_domains.add(domain_with_prefix)

    # 保存匹配的域名（带前缀）到文件
    matching_domain_lines = sorted(matching_domains)
    with open('matching_domains.list', 'w', encoding='utf-8') as f:
        for line in matching_domain_lines:
            f.write(f"{line}\n")

    print(f"匹配的域名（带前缀）已保存到 matching_domains.list 文件中，共 {len(matching_domain_lines)} 个。")

def is_ip_in_cloudflare(ip, cloudflare_cidrs):
    """检查 IP 是否在 Cloudflare CIDR 范围内"""
    ip_obj = ipaddress.ip_address(ip)
    return any(ip_obj in cidr for cidr in cloudflare_cidrs)

if __name__ == '__main__':
    main()
