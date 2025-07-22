import asyncio
                                        ips.add(answer['data'])
                                    except ValueError:
                                        continue
            return ips
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(0.5)  # 失败后稍作等待重试
            else:
                print(f"查询失败: {e}")
    return ips

# 使用 dns.sb 查询域名的 IP 地址
async def query_dns_sb(session: aiohttp.ClientSession, domain: str) -> Set[str]:
    return await query_dns_json(session,
        f"https://doh.sb/dns-query?name={domain}&type=A",
        f"https://doh.sb/dns-query?name={domain}&type=AAAA",
        headers=HEADERS['dns.sb'])

# 使用 Google DNS 查询域名的 IP 地址
async def query_dns_google(session: aiohttp.ClientSession, domain: str) -> Set[str]:
    return await query_dns_json(session,
        f"https://dns.google/resolve?name={domain}&type=A",
        f"https://dns.google/resolve?name={domain}&type=AAAA",
        headers=HEADERS['dns.google'])

# 检查IP是否在给定的CIDR列表中
def is_ip_in_cidr(ip: str, cidr_list: List[str]) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip)
        for cidr in cidr_list:
            if '/' in cidr:
                network = ipaddress.ip_network(cidr.strip(), strict=False)
                if ip_obj in network:
                    return True
    except ValueError:
        return False
    return False

# 对一批域名进行查询和IP收集
async def process_domains(session: aiohttp.ClientSession,
                          domains: List[tuple],
                          query_func,
                          rate_limiter: RateLimiter) -> Dict[str, Set[str]]:
    results = defaultdict(set)
    for domain, prefix in domains:
        await rate_limiter.acquire()
        ips = await query_func(session, domain)
        results[domain] = ips
    return results

# 主逻辑：分发查询任务，筛选Cloudflare域名
async def main():
    try:
        print("开始获取域名列表...")
        domains = await fetch_domain_list()
        print(f"获取到 {len(domains)} 个域名")

        print("加载 CIDR 列表...")
        cidr_list = await load_cidr_list()
        print(f"加载了 {len(cidr_list)} 条 CIDR 记录")

        domain_items = list(domains.items())
        total = len(domain_items)
        half = math.ceil(total / 2)

        sb_domains = domain_items[:half]
        google_domains = domain_items[half:]

        sb_limiter = RateLimiter(10)
        google_limiter = RateLimiter(10)

        cf_domains = []  # 最终匹配到Cloudflare IP的域名列表
        async with aiohttp.ClientSession() as session:
            sb_task = asyncio.create_task(
                process_domains(session, sb_domains, query_dns_sb, sb_limiter)
            )
            google_task = asyncio.create_task(
                process_domains(session, google_domains, query_dns_google, google_limiter)
            )

            sb_results, google_results = await asyncio.gather(sb_task, google_task)

            all_results = {**sb_results, **google_results}

            for domain, ips in all_results.items():
                for ip in ips:
                    if is_ip_in_cidr(ip, cidr_list):
                        cf_domains.append((domains[domain], domain))
                        break  # 一个匹配即可

        # 写入匹配到的域名
        with open(MATCHING_DOMAINS_FILE, 'w') as f:
            for prefix, domain in sorted(cf_domains, key=lambda x: x[1]):
                f.write(f"{prefix},{domain}\n")

        print(f"匹配到的Cloudflare域名数量: {len(cf_domains)}")

    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == '__main__':
    asyncio.run(main())
