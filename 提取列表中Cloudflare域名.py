import requests
import concurrent.futures
import os
import re
import ipaddress
import uuid

# 定义文件路径
URLS_WITH_PREFIX = [
    'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Global/Global.list',
]

def fetch_domains_with_prefix(url):
    """获取带前缀的域名列表"""
    response = requests.get(url)
    response.raise_for_status()
    domains = set()
    for line in response.text.splitlines():
        if line.startswith('DOMAIN-SUFFIX,') or line.startswith('DOMAIN,'):
            domain = line.split(',')[1].strip()
            domains.add(domain)
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

def check_cloudflare_ip_via_bgp(domain):
    """通过 bgp.he.net 查询域名对应的 IP 地址"""
    cache_file = None
    try:
        url = f'https://bgp.he.net/dns/{domain}#_ipinfo'
        cache_file = cache_page(url)
        with open(cache_file, 'r', encoding='utf-8') as f:
            content = f.read()
            ip_matches = re.findall(r'<a href="/ip/([\d\.a-fA-F:]+)" title="[\d\.a-fA-F:]+">', content)
        return domain, set(ip_matches)
    except Exception as e:
        print(f"通过bgp.he.net检查 {domain} 时出错: {e}")
    finally:
        if cache_file:
            clear_cache(cache_file)
    return None

def is_ip_in_cloudflare(ip, cloudflare_cidrs):
    """检查 IP 是否在 Cloudflare CIDR 范围内"""
    ip_obj = ipaddress.ip_address(ip)
    return any(ip_obj in cidr for cidr in cloudflare_cidrs)

def process_domain(domain, cloudflare_cidrs):
    """处理每个域名，查询其 IP 并检查是否属于 Cloudflare"""
    result = check_cloudflare_ip_via_bgp(domain)
    if result:
        domain, ips = result
        cloudflare_ips = {ip for ip in ips if is_ip_in_cloudflare(ip, cloudflare_cidrs)}
        return domain, cloudflare_ips if cloudflare_ips else None
    return None

def main():
    """主函数，执行查询和结果保存"""
    all_domains = set()

    # 从带前缀的域名获取
    for url in URLS_WITH_PREFIX:
        all_domains.update(fetch_domains_with_prefix(url))

    # 获取 Cloudflare CIDR 列表
    cloudflare_cidrs_url = 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/refs/heads/main/Clash/Cloudflare.txt'
    try:
        response = requests.get(cloudflare_cidrs_url)
        cloudflare_cidrs = [ipaddress.ip_network(cidr.strip()) for cidr in response.text.splitlines() if cidr.strip()]
    except Exception as e:
        print(f"获取 Cloudflare CIDR 列表时出错: {e}")
        return

    all_cloudflare_ips = set()
    domain_ip_mapping = {}

    # 并发查询所有域名对应的 IP
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_domain, domain, cloudflare_cidrs): domain for domain in all_domains}
        for future in concurrent.futures.as_completed(futures):
            domain = futures[future]
            try:
                result = future.result()
                if result:
                    domain, cloudflare_ips = result
                    if cloudflare_ips:
                        all_cloudflare_ips.update(cloudflare_ips)
                        domain_ip_mapping[domain] = cloudflare_ips
            except Exception as e:
                print(f"处理域名 {domain} 时出错: {e}")

    # 保存匹配的域名（带前缀）到文件
    matching_domain_lines = sorted(domain_ip_mapping.keys())
    with open('matching_domains.list', 'w', encoding='utf-8') as f:
        for line in matching_domain_lines:
            f.write(f"{line}\n")

    print(f"匹配的域名（带前缀）已保存到 matching_domains.list 文件中，共 {len(matching_domain_lines)} 个。")

if __name__ == '__main__':
    main()
