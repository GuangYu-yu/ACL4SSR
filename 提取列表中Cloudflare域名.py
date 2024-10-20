import requests
import concurrent.futures
import os
import re
import ipaddress
import uuid
import time
import random

# 定义文件路径和查询渠道
DOMAIN_LIST_URL = 'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Global/Global.list'
n_channels = 4  # 更新为4个查询渠道

def fetch_domains(url):
    """获取域名列表"""
    response = requests.get(url)
    response.raise_for_status()
    domains = []
    for line in response.text.splitlines():
        if line.startswith('DOMAIN-SUFFIX,') or line.startswith('DOMAIN,'):
            domains.append(line)
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

def check_cloudflare_ip_via_bgp(domain_line):
    """通过 bgp.he.net 查询 Cloudflare IP"""
    domain = domain_line.split(',')[1]
    try:
        url = f'https://bgp.he.net/dns/{domain}#_ipinfo'
        cache_file = cache_page(url)
        with open(cache_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'Cloudflare' in content:
                ip_matches = re.findall(r'<a href="/ip/([\d\.a-fA-F:]+)" title="[\d\.a-fA-F:]+">', content)
                clear_cache(cache_file)
                return domain_line, domain, set(ip_matches)
    except Exception as e:
        print(f"通过bgp.he.net检查 {domain} 时出错: {e}")
    clear_cache(cache_file)
    return None

def check_cloudflare_ip_via_ipaddress(domain_line):
    """通过 ipaddress.com 查询 Cloudflare IP"""
    domain = domain_line.split(',')[1]
    try:
        url = f'https://www.ipaddress.com/website/{domain}/'
        cache_file = cache_page(url)
        with open(cache_file, 'r', encoding='utf-8') as f:
            content = f.read()
            ip_matches = re.findall(r'<a href="https://www.ipaddress.com/ipv4/([\d\.]+)">([\d\.]+)</a>', content)
            ipv6_matches = re.findall(r'<a href="https://www.ipaddress.com/ipv6/([\d%3A]+)">([\d:a-fA-F:]+)</a>', content)
            if '<em>Cloudflare</em>' in content:
                clear_cache(cache_file)
                return domain_line, domain, set(ip[1] for ip in ip_matches).union(set(ipv6[1] for ipv6 in ipv6_matches))
    except Exception as e:
        print(f"通过ipaddress.com检查 {domain} 时出错: {e}")
    clear_cache(cache_file)
    return None

def check_cloudflare_ip_via_browserleaks(domain_line):
    """通过 browserleaks.com 查询 Cloudflare IP"""
    domain = domain_line.split(',')[1]
    try:
        url = f'https://browserleaks.com/ip/{domain}'
        cache_file = cache_page(url)
        with open(cache_file, 'r', encoding='utf-8') as f:
            content = f.read()
            ip_matches = re.findall(r'<div class="ip">([\d\.a-fA-F:]+)</div>', content)
            if '<td>Cloudflare, Inc.</td>' in content:
                clear_cache(cache_file)
                return domain_line, domain, set(ip_matches)
    except Exception as e:
        print(f"通过browserleaks.com检查 {domain} 时出错: {e}")
    clear_cache(cache_file)
    return None

def check_cloudflare_ip_via_ipleak(domain_line):
    """通过 ipleak.net 查询 Cloudflare IP"""
    domain = domain_line.split(',')[1]
    try:
        url = f'https://ipleak.net/?q={domain}'
        cache_file = cache_page(url)
        with open(cache_file, 'r', encoding='utf-8') as f:
            content = f.read()
            ip_matches = re.findall(r'<a data-tooltip="Click for more details about this IP" class="ip" rel="nofollow" href="(/[\d\.a-fA-F:]+)">([\d\.a-fA-F:]+)</a>', content)
            if 'CLOUDFLARE' in content:
                clear_cache(cache_file)
                return domain_line, domain, set(ip[1] for ip in ip_matches)
    except Exception as e:
        print(f"通过ipleak.net检查 {domain} 时出错: {e}")
    clear_cache(cache_file)
    return None

def process_domain(domain_line, index):
    """处理每个域名，轮流查询其 Cloudflare IP"""
    if index % n_channels == 0:
        return check_cloudflare_ip_via_bgp(domain_line)
    elif index % n_channels == 1:
        return check_cloudflare_ip_via_ipaddress(domain_line)
    elif index % n_channels == 2:
        return check_cloudflare_ip_via_browserleaks(domain_line)
    else:
        return check_cloudflare_ip_via_ipleak(domain_line)

def main():
    """主函数，执行查询和结果保存"""
    domain_lines = fetch_domains(DOMAIN_LIST_URL)
    matching_domain_lines = set()
    matching_domains = set()
    all_cloudflare_ips = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = {}
        for i, domain_line in enumerate(domain_lines):
            futures[executor.submit(process_domain, domain_line, i)] = domain_line
            time.sleep(random.uniform(0, 2))  # 随机延迟

        for future in concurrent.futures.as_completed(futures):
            domain_line = futures[future]
            try:
                result = future.result()
                if result:
                    matching_domain_lines.add(result[0])
                    matching_domains.add(result[1])
                    all_cloudflare_ips.update(result[2])
            except Exception as e:
                print(f"处理域名 {domain_line} 时出错: {e}")

    # 分离IPv4和IPv6地址
    ipv4_addresses = set()
    ipv6_addresses = set()

    for ip in all_cloudflare_ips:
        try:
            ip_obj = ipaddress.ip_address(ip)
            if ip_obj.version == 4:
                ipv4_addresses.add(ip)
            else:
                ipv6_addresses.add(ip)
        except ValueError:
            print(f"无效的IP地址: {ip}")

    # 分别排序IPv4和IPv6地址
    sorted_ipv4 = sorted(ipv4_addresses, key=lambda ip: ipaddress.IPv4Address(ip))
    sorted_ipv6 = sorted(ipv6_addresses, key=lambda ip: ipaddress.IPv6Address(ip))

    # 保存匹配的域名（带前缀）到文件
    with open('matching_domains.list', 'w', encoding='utf-8') as f:
        for domain_line in sorted(matching_domain_lines):
            f.write(f"{domain_line}\n")

    # 保存优选域名（不带前缀）到文件
    with open('优选域名.txt', 'w', encoding='utf-8') as f:
        for domain in sorted(matching_domains):
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
    print(f"优选域名（不带前缀）已保存到 优选域名.txt 文件中，共 {len(matching_domains)} 个。")
    print(f"提取的 Cloudflare IP 已保存到 优选域名ip.txt 文件中，共 {len(sorted_ipv4) + len(sorted_ipv6)} 个。")
    print(f"其中 IPv4 地址 {len(sorted_ipv4)} 个，IPv6 地址 {len(sorted_ipv6)} 个。")

if __name__ == '__main__':
    main()
