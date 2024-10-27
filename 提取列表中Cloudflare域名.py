import asyncio
import aiohttp
import ipaddress
from typing import List, Dict, Set
import time
from collections import defaultdict
import math

# 定义常量
DOMAIN_LIST_URL = 'https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Global/Global.list'
CIDR_URL = 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/refs/heads/main/Clash/Cloudflare.txt'
MATCHING_DOMAINS_FILE = 'matching_domains.list'

# 请求头
HEADERS = {
    'dns.sb': {
        'accept': 'application/dns-json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    },
    'dns.google': {
        'accept': 'application/dns-json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
}

class RateLimiter:
    def __init__(self, rate_limit):
        self.rate_limit = rate_limit
        self.tokens = rate_limit
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.monotonic()
            time_passed = now - self.last_update
            self.tokens = min(self.rate_limit, self.tokens + time_passed * self.rate_limit)
            self.last_update = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate_limit
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1

async def fetch_domain_list() -> Dict[str, str]:
    async with aiohttp.ClientSession() as session:
        async with session.get(DOMAIN_LIST_URL) as response:
            text = await response.text()
            domains = {}
            for line in text.splitlines():
                if line.startswith(("DOMAIN", "DOMAIN-SUFFIX")):
                    prefix, domain = line.split(',')
                    domains[domain] = prefix
            return domains

async def load_cidr_list() -> List[str]:
    async with aiohttp.ClientSession() as session:
        async with session.get(CIDR_URL) as response:
            return (await response.text()).splitlines()

async def query_dns_json(session: aiohttp.ClientSession, *urls: str, headers: dict) -> Set[str]:
    while True:  # 无限重试直到成功
        ips = set()
        try:
            for url in urls:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'Answer' in data:
                            for answer in data['Answer']:
                                if answer.get('data'):
                                    try:
                                        ipaddress.ip_address(answer['data'])
                                        ips.add(answer['data'])
                                    except ValueError:
                                        continue
            return ips  # 只有成功获取到结果才返回
        except Exception as e:
            print(f"查询出错: {e}，3秒后重试...")
            await asyncio.sleep(3)  # 失败后等待3秒重试

async def query_dns_sb(session: aiohttp.ClientSession, domain: str) -> Set[str]:
    return await query_dns_json(session, 
        f"https://doh.sb/dns-query?name={domain}&type=A",
        f"https://doh.sb/dns-query?name={domain}&type=AAAA",
        headers=HEADERS['dns.sb'])

async def query_dns_google(session: aiohttp.ClientSession, domain: str) -> Set[str]:
    return await query_dns_json(session, 
        f"https://dns.google/resolve?name={domain}&type=A",
        f"https://dns.google/resolve?name={domain}&type=AAAA",
        headers=HEADERS['dns.google'])

def is_ip_in_cidr(ip: str, cidr_list: List[str]) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
        for cidr in cidr_list:
            if '/' in cidr:
                network = ipaddress.ip_network(cidr.strip())
                if ip_obj in network:
                    return True
    except ValueError:
        return False
    return False

async def process_domain_batch(session: aiohttp.ClientSession, 
                             domains: List[tuple], 
                             query_func, 
                             rate_limiter: RateLimiter,
                             cidr_list: List[str]) -> Dict[str, Set[str]]:
    results = defaultdict(set)
    total = len(domains)
    for idx, (domain, prefix) in enumerate(domains, 1):
        await rate_limiter.acquire()
        ips = await query_func(session, domain)
        results[domain] = ips
        print(f"进度: {idx}/{total} - 域名 {domain} 查询完成")
    return results

async def main():
    try:
        print("开始获取域名列表...")
        domains = await fetch_domain_list()
        print(f"获取到 {len(domains)} 个域名")

        print("加载 CIDR 列表...")
        cidr_list = await load_cidr_list()
        print(f"加载了 {len(cidr_list)} 条 CIDR 记录")

        # 将域名分成两组
        domain_items = list(domains.items())
        mid = math.ceil(len(domain_items) / 2)
        sb_domains = domain_items[:mid]
        google_domains = domain_items[mid:]

        # 创建限速器
        sb_limiter = RateLimiter(10)
        google_limiter = RateLimiter(10)

        cf_domains = []
        async with aiohttp.ClientSession() as session:
            # 并行处理两组域名
            sb_task = process_domain_batch(session, sb_domains, query_dns_sb, sb_limiter, cidr_list)
            google_task = process_domain_batch(session, google_domains, query_dns_google, google_limiter, cidr_list)
            
            results = await asyncio.gather(sb_task, google_task)
            
            # 合并结果
            all_results = {**results[0], **results[1]}

            # 检查IP是否在Cloudflare CIDR范围内
            for domain, ips in all_results.items():
                for ip in ips:
                    if is_ip_in_cidr(ip, cidr_list):
                        cf_domains.append((domains[domain], domain))
                        break

        # 写入结果
        with open(MATCHING_DOMAINS_FILE, 'w') as f:
            for prefix, domain in sorted(cf_domains, key=lambda x: x[1]):
                f.write(f"{prefix},{domain}\n")

        print(f"匹配到的Cloudflare域名数量: {len(cf_domains)}")

    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == '__main__':
    asyncio.run(main())
