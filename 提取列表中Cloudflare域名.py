import requests
import yaml
from bs4 import BeautifulSoup
import concurrent.futures
import os
import ipaddress
import threading
import random
import time

# 定义常量
DOMAIN_LIST_URL = 'https://raw.githubusercontent.com/GuangYu-yu/About-Cloudflare/refs/heads/main/test.list'
CIDR_URL = 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/refs/heads/main/Clash/Cloudflare.txt'
TEMP_YAML_FILE = 'temp_domains.yaml'
MATCHING_DOMAINS_FILE = 'matching_domains.list'
CACHED_CIDR_FILE = 'cached_cidr.txt'

# 初始化锁
file_lock = threading.Lock()

def fetch_domain_list():
    print("正在获取域名列表...")
    response = requests.get(DOMAIN_LIST_URL)
    response.raise_for_status()
    domains = {}
    for line in response.text.splitlines():
        if line.startswith("DOMAIN") or line.startswith("DOMAIN-SUFFIX"):
            parts = line.split(',')
            if len(parts) == 2:
                prefix, domain = parts
                if domain not in domains:
                    domains[domain] = {'prefix': prefix, 'ips': []}
    return domains

def query_ip_info(domain, index, retries=3):
    for attempt in range(retries):
        try:
            time.sleep(random.uniform(3, 5))  # Delay of 3 to 5 seconds
            query_url = f"https://bgp.he.net/dns/{domain}#_ipinfo"
            response = requests.get(query_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            ip_info_div = soup.find('div', id='ipinfo')
            if ip_info_div:
                ips = [a.get('title') for a in ip_info_div.find_all('a') if a.get('href', '').startswith('/ip/')]
                return list(set(ips))  # 这里确保返回的IP去重
            return []
        except Exception as e:
            if attempt < retries - 1:
                continue  # 继续重试
            else:
                return []  # 返回空列表

def load_cidr_list():
    print("加载 CIDR 列表...")
    response = requests.get(CIDR_URL)
    response.raise_for_status()
    return response.text.splitlines()

def is_ip_in_cidr(ip, cidr_list):
    for cidr in cidr_list:
        if '/' in cidr:
            network = ipaddress.ip_network(cidr.strip())
            if ipaddress.ip_address(ip) in network:
                return True
    return False

def main():
    try:
        print("脚本开始执行...")
        domains = fetch_domain_list()
        
        queried_domains = set()  # 记录已查询的域名
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            future_to_domain = {executor.submit(query_ip_info, domain, index): (domain, index) 
                                for index, domain in enumerate(domains) if domain not in queried_domains}
            for future in concurrent.futures.as_completed(future_to_domain):
                domain, index = future_to_domain[future]
                queried_domains.add(domain)  # 添加到已查询列表
                try:
                    ips = future.result()
                    if ips:
                        domains[domain]['ips'].extend(ips)
                except Exception:
                    continue  # 忽略查询错误

        # 加载并缓存 CIDR 列表
        cidr_list = load_cidr_list()

        cf_domains = []

        # 匹配 IP 地址与 CIDR 列表
        for domain, data in domains.items():
            for ip in data['ips']:
                if is_ip_in_cidr(ip, cidr_list):
                    cf_domains.append(domain)
                    break

        # 排序并处理 CF 域名
        cf_domains = sorted(set(cf_domains))

        # 写入匹配的域名
        with open(MATCHING_DOMAINS_FILE, 'w') as f:
            for domain in cf_domains:
                prefix = domains[domain]['prefix']
                f.write(f"{prefix},{domain}\n")

        # 打印匹配到的域名数量
        print(f"匹配到的域名数量: {len(cf_domains)}")

    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == '__main__':
    main()
