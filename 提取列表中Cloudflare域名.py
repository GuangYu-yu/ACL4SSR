import requests
import ipaddress
import time
import random

# 定义文件路径
DOMAIN_LIST_URL = 'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Global/Global.list'
CLOUDFLARE_CIDR_URL = 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/refs/heads/main/Clash/Cloudflare.txt'

# DNS 查询组
DNS_QUERY_GROUPS = [
    [
        'https://dns10.quad9.net:5053/dns-query?name={domain}&type=AAAA',
        'https://dns10.quad9.net:5053/dns-query?name={domain}&type=A'
    ],
    [
        'https://dns.google/resolve?name={domain}&type=AAAA',
        'https://dns.google/resolve?name={domain}&type=A'
    ],
    [
        'https://dns.twnic.tw/dns-query?name={domain}&type=AAAA',
        'https://dns.twnic.tw/dns-query?name={domain}&type=A'
    ]
]

def fetch_domains(url):
    """获取域名列表"""
    response = requests.get(url)
    response.raise_for_status()
    domains = []
    for line in response.text.splitlines():
        if line.startswith('DOMAIN-SUFFIX,') or line.startswith('DOMAIN,'):
            domains.append(line)
    return domains

def fetch_cloudflare_cidrs(url):
    """获取 Cloudflare CIDR 列表"""
    response = requests.get(url)
    response.raise_for_status()
    return set(line.strip() for line in response.text.splitlines() if line.strip())

def query_dns(domain, urls):
    """查询 DNS 并返回 IP 地址"""
    ips = set()
    for url in urls:
        response = requests.get(url.format(domain=domain))
        response.raise_for_status()
        data = response.json()
        if 'Answer' in data:
            ips.update({answer['data'] for answer in data['Answer'] if 'data' in answer})
    return ips

def is_cloudflare_ip(ip, cidr_set):
    """判断 IP 是否属于 Cloudflare"""
    try:
        ip_obj = ipaddress.ip_address(ip)
        return any(ipaddress.ip_address(ip) in ipaddress.ip_network(cidr) for cidr in cidr_set)
    except ValueError:
        return False

def main():
    """主函数，执行查询和结果保存"""
    cloudflare_cidrs = fetch_cloudflare_cidrs(CLOUDFLARE_CIDR_URL)
    domain_lines = fetch_domains(DOMAIN_LIST_URL)

    matching_domain_lines = set()
    matching_domains = set()
    all_cloudflare_ips = set()

    # 初始化 QPS 和使用记录
    qps_limits = [5] * len(DNS_QUERY_GROUPS)  # 初始 QPS
    dns_usage = [0] * len(DNS_QUERY_GROUPS)
    success_counts = [0] * len(DNS_QUERY_GROUPS)  # 记录成功查询次数

    for domain_line in domain_lines:
        # 随机选择 DNS 查询组，但确保均衡使用
        selected_index = min(range(len(DNS_QUERY_GROUPS)), key=lambda i: dns_usage[i])
        urls = DNS_QUERY_GROUPS[selected_index]
        dns_usage[selected_index] += 1  # 更新调用次数

        retries = 0
        while retries < 5:
            try:
                # 查询 IP 地址
                result = query_dns(domain_line.split(',')[1], urls)

                # 判断每个 IP 是否属于 Cloudflare
                for ip in result:
                    if is_cloudflare_ip(ip, cloudflare_cidrs):
                        matching_domain_lines.add(domain_line)
                        matching_domains.add(domain_line.split(',')[1])
                        all_cloudflare_ips.add(ip)

                # 成功查询后，增加成功计数
                success_counts[selected_index] += 1

                # 每成功 50 次增加一次 QPS，且不能超过某个最大值（例如 20）
                if success_counts[selected_index] % 50 == 0:
                    qps_limits[selected_index] = min(qps_limits[selected_index] + 1, 20)

                break  # 查询成功，退出重试循环

            except requests.exceptions.RequestException as e:
                print(f"查询失败: {e}，当前 QPS: {qps_limits[selected_index]}")
                retries += 1
                time.sleep(5)  # 等待重试时间

        # 如果重试失败达到 5 次，终止脚本
        if retries >= 5:
            print("重试次数达到上限，终止脚本。")
            return

        # 等待以确保每组查询速率不超过设置的 QPS
        time.sleep(1 / qps_limits[selected_index])

    # 保存匹配的域名和 Cloudflare IP 地址
    with open('matching_domains.list', 'w', encoding='utf-8') as f:
        for domain_line in sorted(matching_domain_lines):
            f.write(f"{domain_line}\n")

    with open('优选域名.txt', 'w', encoding='utf-8') as f:
        for domain in sorted(matching_domains):
            f.write(f"{domain}\n")

    # 去重、排序并保存 Cloudflare IP 地址
    sorted_unique_ips = sorted(all_cloudflare_ips)
    with open('优选域名ip.txt', 'w', encoding='utf-8') as f:
        for ip in sorted_unique_ips:
            f.write(f"{ip}\n")

    # 打印各个 DNS 的 QPS 值
    for i, qps in enumerate(qps_limits):
        print(f"DNS 查询组 {i + 1} 的 QPS: {qps}")

    print(f"匹配的域名（带前缀）已保存到 matching_domains.list 文件中，共 {len(matching_domain_lines)} 个。")
    print(f"优选域名（不带前缀）已保存到 优选域名.txt 文件中，共 {len(matching_domains)} 个。")
    print(f"提取的 Cloudflare IP 已保存到 优选域名ip.txt 文件中，共 {len(sorted_unique_ips)} 个。")

if __name__ == '__main__':
    main()
