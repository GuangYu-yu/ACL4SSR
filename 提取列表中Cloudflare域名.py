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
            domains.add(line.strip())
    return domains

def check_cloudflare_ip_via_bgp(domain):
    """通过 bgp.he.net 查询域名对应的 IP 地址"""
    try:
        url = f'https://bgp.he.net/dns/{domain}#_ipinfo'
        response = requests.get(url)
        response.raise_for_status()
        ip_matches = re.findall(r'<a href="/ip/([\d\.a-fA-F:]+)" title="[\d\.a-fA-F:]+">', response.text)
        return domain, set(ip_matches)
    except Exception as e:
        print(f"通过bgp.he.net检查 {domain} 时出错: {e}")
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
    all_domains_with_prefix = fetch_domains_with_prefix(URLS_WITH_PREFIX[0])

    # 获取 Cloudflare CIDR 列表
    cloudflare_cidrs_url = 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/refs/heads/main/Clash/Cloudflare.txt'
    response = requests.get(cloudflare_cidrs_url)
    cloudflare_cidrs = [ipaddress.ip_network(cidr.strip()) for cidr in response.text.splitlines() if cidr.strip()]

    matched_domains = set()
    domain_ip_mapping = {}

    # 并发查询所有域名对应的 IP
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_domain, domain.split(',')[1].strip(), cloudflare_cidrs): domain for domain in all_domains_with_prefix}
        for future in concurrent.futures.as_completed(futures):
            domain = futures[future]
            try:
                result = future.result()
                if result:
                    domain, cloudflare_ips = result
                    if cloudflare_ips:
                        matched_domains.add(domain)
                        domain_ip_mapping[domain] = cloudflare_ips
            except Exception as e:
                print(f"处理域名 {domain} 时出错: {e}")

    # 保存匹配的带前缀的域名到文件
    with open('matching_domains.list', 'w', encoding='utf-8') as f:
        for domain in matched_domains:
            f.write(f"{domain}\n")

    print(f"匹配的带前缀的域名已保存到 matching_domains.list 文件中，共 {len(matched_domains)} 个。")

if __name__ == '__main__':
    main()
