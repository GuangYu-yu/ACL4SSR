import dns.resolver
import ipaddress
from typing import List, Dict, Set
from collections import defaultdict
import math
import time

# 下载域名列表和Cloudflare IP CIDR列表的URL
DOMAIN_LIST_URL = 'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Global/Global.list'
CIDR_URL = 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/refs/heads/main/Clash/Cloudflare.txt'
MATCHING_DOMAINS_FILE = 'cloudflare_domains.list'

# 简单速率限制器
class RateLimiter:
    def __init__(self, rate_limit):
        self.rate_limit = rate_limit
        self.tokens = rate_limit
        self.last_update = time.monotonic()
        self.lock = False

    def acquire(self):
        now = time.monotonic()
        self.tokens = min(self.rate_limit, self.tokens + (now - self.last_update) * self.rate_limit)
        self.last_update = now
        if self.tokens < 1:
            wait_time = (1 - self.tokens) / self.rate_limit
            time.sleep(wait_time)
            self.tokens = 0
        else:
            self.tokens -= 1

# 获取域名列表
def fetch_domain_list() -> Dict[str, str]:
    import requests
    response = requests.get(DOMAIN_LIST_URL)
    response.raise_for_status()
    text = response.text
    domains = {}
    for line in text.splitlines():
        if not line or line.startswith('#'):
            continue
        if any(line.startswith(prefix) for prefix in ['DOMAIN-SUFFIX,', 'DOMAIN,']):
            try:
                prefix, domain = [x.strip() for x in line.split(',', 1)]
                domains[domain] = prefix
            except ValueError:
                continue
    return domains

# 加载CIDR列表
def load_cidr_list() -> List[str]:
    import requests
    response = requests.get(CIDR_URL)
    response.raise_for_status()
    return [line.strip() for line in response.text.splitlines() if line.strip()]

# 判断IP是否在CIDR列表
def is_ip_in_cidr(ip: str, cidr_list: List[str]) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
        for cidr in cidr_list:
            if '/' in cidr:
                if ip_obj in ipaddress.ip_network(cidr, strict=False):
                    return True
    except ValueError:
        return False
    return False

# 使用1.1.1.1查询IPv4
def query_dns_ipv4(domain: str) -> Set[str]:
    resolver = dns.resolver.Resolver()
    resolver.nameservers = ['1.1.1.1']  # 使用 Cloudflare 公共 DNS
    ips = set()
    try:
        answers = resolver.resolve(domain, 'A', lifetime=3)
        for r in answers:
            ips.add(str(r))
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
        pass
    except Exception as e:
        print(f"查询 {domain} 出错: {e}")
    return ips

# 对域名列表进行处理
def process_domains(domains: List[tuple], rate_limiter: RateLimiter) -> Dict[str, Set[str]]:
    results = defaultdict(set)
    for domain, prefix in domains:
        rate_limiter.acquire()
        ips = query_dns_ipv4(domain)
        results[domain] = ips
    return results

# 主逻辑
def main():
    try:
        print("开始获取域名列表...")
        domains = fetch_domain_list()
        print(f"获取到 {len(domains)} 个域名")

        print("加载CIDR列表...")
        cidr_list = load_cidr_list()
        print(f"加载了 {len(cidr_list)} 条 CIDR 记录")

        domain_items = list(domains.items())
        total = len(domain_items)
        half = math.ceil(total / 2)

        first_half = domain_items[:half]
        second_half = domain_items[half:]

        limiter = RateLimiter(20)  # 每秒20次查询

        cf_domains = []

        # 分批处理
        results1 = process_domains(first_half, limiter)
        results2 = process_domains(second_half, limiter)
        all_results = {**results1, **results2}

        for domain, ips in all_results.items():
            if any(is_ip_in_cidr(ip, cidr_list) for ip in ips):
                cf_domains.append((domains[domain], domain))

        with open(MATCHING_DOMAINS_FILE, 'w') as f:
            for prefix, domain in sorted(cf_domains, key=lambda x: x[1]):
                f.write(f"{prefix},{domain}\n")

        print(f"匹配到的Cloudflare域名数量: {len(cf_domains)}")

    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == '__main__':
    main()
