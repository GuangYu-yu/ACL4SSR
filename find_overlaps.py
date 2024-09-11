# find_overlaps.py

import geoip2.database
from netaddr import IPNetwork, IPSet
from collections import defaultdict

# 定义目标国家代码
target_countries = ["HK", "SG", "JP", "KR", "TW"]

# 读取 Cloudflare CIDR
with open("CIDR.txt") as f:
    cloudflare_cidrs = [IPNetwork(line.strip()) for line in f if line.strip()]

# 打开 GeoLite2-ASN.mmdb 数据库
reader = geoip2.database.Reader("GeoLite2-ASN.mmdb")

# 准备存储结果的字典
country_cidr_map = defaultdict(IPSet)

# 遍历 Cloudflare CIDR
for cidr in cloudflare_cidrs:
    try:
        # 获取 ASN 信息并判断所属国家
        response = reader.asn(cidr.network)
        country_code = response.country.iso_code

        # 如果这个 CIDR 属于目标国家之一，保存到对应国家的集合中
        if country_code in target_countries:
            country_cidr_map[country_code].add(cidr)
    except geoip2.errors.AddressNotFoundError:
        pass

# 为每个国家输出 CIDR 结果
for country_code, cidrs in country_cidr_map.items():
    with open(f"outputs/{country_code}.txt", "w") as f:
        for cidr in cidrs.iter_cidrs():
            f.write(f"{cidr}\n")
