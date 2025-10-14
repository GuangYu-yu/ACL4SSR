import dns.resolver
import asyncio
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
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            self.tokens = min(self.rate_limit, self.tokens + (now - self.last_update) * self.rate_limit)
            self.last_update = now
            if self.tokens < 1:
                await asyncio.sleep((1 - self.tokens) / self.rate_limit)
                self.tokens = 0
            else:
                self.tokens -= 1

# 获取域名列表
async def fetch_domain_list() -> Dict[str, str]:
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(DOMAIN_LIST_URL) as response:
            text = await response.text()
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
async def load_cidr_list() -> List[str]:
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.get(CIDR_URL) as response:
            return [line.strip() for line in (await response.text()).splitlines() if line.strip()]

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

# 传统DNS查询A和AAAA记录
def query_dns(domain: str) -> Set[str]:
    resolver = dns.resolver.Resolver()
    ips = set()
    try:
        for rtype in ['A', 'AAAA']:
            try:
                answers = resolver.resolve(domain, rtype, lifetime=3)
                for r in answers:
                    ips.add(str(r))
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
                continue
    except Exception as e:
        print(f"查询 {domain} 出错: {e}")
    return ips

# 异步包装传统DNS查询
async def query_dns_async(domain: str) -> Set[str]:
    return await asyncio.to_thread(query_dns, domain)

# 对域名列表进行处理
async def process_domains(domains: List[tuple], rate_limiter: RateLimiter) -> Dict[str, Set[str]]:
    results = defaultdict(set)
    for domain, prefix in domains:
        await rate_limiter.acquire()
        ips = await query_dns_async(domain)
        results[domain] = ips
    return results

# 主逻辑
async def main():
    try:
        print("开始获取域名列表...")
        domains = await fetch_domain_list()
        print(f"获取到 {len(domains)} 个域名")

        print("加载CIDR列表...")
        cidr_list = await load_cidr_list()
        print(f"加载了 {len(cidr_list)} 条 CIDR 记录")

        domain_items = list(domains.items())
        total = len(domain_items)
        half = math.ceil(total / 2)

        first_half = domain_items[:half]
        second_half = domain_items[half:]

        limiter = RateLimiter(20)  # 每秒20次查询

        cf_domains = []

        # 并行处理两批域名
        task1 = asyncio.create_task(process_domains(first_half, limiter))
        task2 = asyncio.create_task(process_domains(second_half, limiter))

        results1, results2 = await asyncio.gather(task1, task2)
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
    asyncio.run(main())
