import requests
import ipaddress
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pythonping import ping

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

# DNS 查询
def query_dns(domain, record_type):
    try:
        headers = {'Accept': 'application/dns-json'}
        dns_url = f'https://cloudflare-dns.com/dns-query?name={domain}&type={record_type}'
        
        response = requests.get(dns_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return [answer['data'] for answer in data.get('Answer', []) if answer['type'] == (1 if record_type == "A" else 28)]
        else:
            print(f"DNS 查询失败: 状态码 {response.status_code}，域名: {domain}")
            return []
    except Exception as e:
        print(f"DNS 查询失败: {e}，域名: {domain}")
        return []

# 查询域名的IP地址
def get_ip_from_domain(domain):
    ipv4_addresses = query_dns(domain, "A")
    ipv6_addresses = query_dns(domain, "AAAA")
    return ipv4_addresses, ipv6_addresses

# 并发处理每个域名
def process_domain(domain_line, cidr_ranges):
    domain = domain_line.split(',')[1]
    
    # 查询IPv4和IPv6
    ipv4_addresses, ipv6_addresses = get_ip_from_domain(domain)
    matched = False

    # 检查IPv4和IPv6地址是否在CIDR范围内
    for ip in ipv4_addresses + ipv6_addresses:
        if ip_in_cidr(ip, cidr_ranges):
            matched = True
            return domain_line, domain, matched  # 返回原始行和提取出来的纯域名
    
    return domain_line, domain, matched  # 确保总是返回三个值

# 主函数
def main():
    # 下载域名和CIDR列表
    domain_list, cidr_list = download_lists()
    
    # 提取域名和CIDR
    domains = extract_domains(domain_list)
    cidr_ranges = extract_cidrs(cidr_list)
    
    matching_domains = []
    unmatched_domains = []

    # 使用线程池并发查询
    with ThreadPoolExecutor(max_workers=35) as executor:
        futures = [executor.submit(process_domain, domain_line, cidr_ranges) for domain_line in domains]
        for future in as_completed(futures):
            domain_line, pure_domain, matched = future.result()
            if matched:
                matching_domains.append(domain_line)
            else:
                unmatched_domains.append(domain_line)

    # TCP Ping 检查未匹配的域名
    successful_tcp_matches = 0  # 计数成功匹配的域名

    def tcp_ping_domain(domain_line):
        domain = domain_line.split(',')[1]
        ipv4_addresses, ipv6_addresses = get_ip_from_domain(domain)

        # 获取 IP 地址，不论 TCP Ping 是否成功
        for ip in ipv4_addresses + ipv6_addresses:
            # TCP Ping 获取 IP 地址
            ping(ip, count=1, timeout=1)  # 执行 TCP Ping，但不需要捕获结果
            
            # 检查 IP 地址是否在 CIDR 范围内
            if ip_in_cidr(ip, cidr_ranges):
                return domain_line  # 返回匹配的域名行
        return None  # 返回 None 如果没有匹配

    # 使用线程池并发执行 TCP Ping
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(tcp_ping_domain, domain_line) for domain_line in unmatched_domains]
        for future in as_completed(futures):
            result = future.result()
            if result:
                matching_domains.append(result)
                successful_tcp_matches += 1  # 增加计数

    # 打印 TCP Ping 匹配的数量
    print(f"通过 TCP Ping 成功匹配到 {successful_tcp_matches} 个域名。")

    # 排序结果并保存到文件
    matching_domains.sort()
    with open('matching_domains.list', 'w') as f:
        for domain_line in matching_domains:
            f.write(domain_line + '\n')
    
    preferred_domains = [line.split(',')[1] for line in matching_domains]
    preferred_domains = sorted(set(preferred_domains))  # 去重并排序
    with open('优选域名.txt', 'w') as f:
        for domain in preferred_domains:
            f.write(domain + '\n')

    print(f"匹配的域名已保存到 matching_domains.list 文件中，共 {len(matching_domains)} 个。")
    print(f"提取的纯域名已保存到 优选域名.txt 文件中，共 {len(preferred_domains)} 个。")

# 脚本执行入口
if __name__ == "__main__":
    main()
