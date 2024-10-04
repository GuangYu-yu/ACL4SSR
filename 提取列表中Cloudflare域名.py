import requests
import ipaddress
import subprocess
import re

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

# Ping 域名获取IP地址
def get_ip_from_domain(domain, is_ipv6=False):
    try:
        ping_command = ['ping6', '-c', '1', domain] if is_ipv6 else ['ping', '-c', '1', domain]
        output = subprocess.check_output(ping_command, universal_newlines=True)
        ip_regex = r'\(([\d.]+)\)' if not is_ipv6 else r'\(([\da-fA-F:]+)\)'
        ip = re.search(ip_regex, output).group(1)
        return ip
    except subprocess.CalledProcessError:
        return None

# 主函数
def main():
    # 下载域名和CIDR列表
    domain_list, cidr_list = download_lists()
    
    # 提取域名和CIDR
    domains = extract_domains(domain_list)
    cidr_ranges = extract_cidrs(cidr_list)
    
    # 匹配域名和CIDR
    matching_domains = []
    for domain_line in domains:
        domain = domain_line.split(',')[1]
        # 尝试Ping IPv4
        ip = get_ip_from_domain(domain)
        if ip and ip_in_cidr(ip, cidr_ranges):
            matching_domains.append(domain_line)  # 保存原始行，保留DOMAIN-SUFFIX
        else:
            # 尝试Ping IPv6
            ip = get_ip_from_domain(domain, is_ipv6=True)
            if ip and ip_in_cidr(ip, cidr_ranges):
                matching_domains.append(domain_line)  # 保存原始行，保留DOMAIN-SUFFIX
    
    # 保存结果到文件
    with open('matching_domains.txt', 'w') as f:
        for domain_line in matching_domains:
            f.write(domain_line + '\n')
    
    print(f"匹配的域名已保存到 matching_domains.txt 文件中，共 {len(matching_domains)} 个。")

# 脚本执行入口
if __name__ == "__main__":
    main()
