import requests
import ipaddress
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

# 下载域名列表和CIDR列表
def download_lists():
    domain_list_url = 'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Global/Global.list'
    cidr_list_url = 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/refs/heads/main/Clash/Cloudflare.txt'
    
    domain_list = requests.get(domain_list_url).text.splitlines()
    cidr_list = requests.get(cidr_list_url).text.splitlines()
    
    return domain_list, cidr_list

# 提取 DOMAIN 和 DOMAIN-SUFFIX 后的域名
def extract_domains(domain_list):
    return [line for line in domain_list if line.startswith('DOMAIN')]

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

# 使用 nslookup 查询域名的IP地址
def query_nslookup(domain):
    try:
        result = subprocess.run(['nslookup', domain], capture_output=True, text=True)
        output = result.stdout
        
        # 提取IP地址
        ips = re.findall(r'Address:\s+(\d+\.\d+\.\d+\.\d+)', output)
        return ips
    except Exception as e:
        print(f"NSLookup 查询失败: {e}，域名: {domain}")
        return []

# 并发处理每个域名
def process_domain(domain_line, cidr_ranges):
    domain = domain_line.split(',')[1]
    
    # 查询IP地址
    ip_addresses = query_nslookup(domain)
    matched = False

    # 检查IP地址是否在CIDR范围内
    for ip in ip_addresses:
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

    # 打印匹配的数量
    print(f"通过 NSLookup 成功匹配到 {len(matching_domains)} 个域名。")

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
