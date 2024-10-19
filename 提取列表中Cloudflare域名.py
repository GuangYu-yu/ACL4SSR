import requests
import concurrent.futures
import os
import re

# 定义文件路径
DOMAIN_LIST_URL = 'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Global/Global.list'

def fetch_domains(url):
    """获取域名列表"""
    response = requests.get(url)
    response.raise_for_status()
    return response.text.splitlines()

def cache_page(url):
    """缓存网页内容到本地文件"""
    response = requests.get(url)
    response.raise_for_status()
    cache_file = 'cache.html'
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
                ip_matches = re.findall(r'<span>([\d\.]+)</span>', content)
                clear_cache(cache_file)
                return domain, set(ip_matches)
    except Exception as e:
        print(f"Error checking {domain} via nslookup: {e}")
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
                ip_matches = re.findall(r'<a href="/ip/([\d\.]+)" title="[\d\.]+">', content)
                clear_cache(cache_file)
                return domain, set(ip_matches)
    except Exception as e:
        print(f"Error checking {domain} via bgp.he.net: {e}")
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
    domains = fetch_domains(DOMAIN_LIST_URL)
    matching_domains = set()
    all_cloudflare_ips = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=70) as executor:
        futures = {executor.submit(process_domain, domain, i): domain for i, domain in enumerate(domains)}
        for future in concurrent.futures.as_completed(futures):
            domain = futures[future]
            try:
                result = future.result()
                if result:
                    matching_domains.add(result[0])
                    all_cloudflare_ips.update(result[1])
            except Exception as e:
                print(f"Error processing domain {domain}: {e}")

    # 保存匹配的域名到文件
    with open('matching_domains.list', 'w', encoding='utf-8') as f:
        for domain in matching_domains:
            f.write(f"{domain}\n")

    # 保存纯域名到文件，不包含 DOMAIN 和 DOMAIN-SUFFIX
    with open('优选域名.txt', 'w', encoding='utf-8') as f:
        for domain in matching_domains:
            if not domain.startswith(('DOMAIN', 'DOMAIN-SUFFIX')):
                f.write(f"{domain}\n")

    # 保存所有 Cloudflare IP 地址到文件
    with open('优选域名ip.txt', 'w', encoding='utf-8') as f:
        for ip in sorted(all_cloudflare_ips):
            f.write(f"{ip}\n")

    print(f"匹配的域名已保存到 matching_domains.list 文件中，共 {len(matching_domains)} 个。")
    print(f"提取的纯域名已保存到 优选域名.txt 文件中，共 {len(matching_domains)} 个。")
    print(f"提取的 Cloudflare IP 已保存到 优选域名ip.txt 文件中，共 {len(all_cloudflare_ips)} 个。")

if __name__ == '__main__':
    main()
