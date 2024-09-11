import geoip2.database
from netaddr import IPNetwork, IPSet
import requests
from collections import defaultdict
import os

# Cloudflare 的 ASN 列表
cloudflare_asns = {'209242', '13335', '149648', '132892', '139242', '202623', '203898', '394536', '395747'}

# 打开 GeoLite2 数据库
asn_reader = geoip2.database.Reader("GeoLite2-ASN.mmdb")
country_reader = geoip2.database.Reader("GeoLite2-Country.mmdb")

# 存储结果的字典：以国家代码为键，存储对应 CIDR
country_cidr_map = defaultdict(IPSet)

# 遍历所有 ASN，找出 Cloudflare 的 ASN
for asn in cloudflare_asns:
    try:
        # 查找 ASN 对应的 IP 段
        for ip_range in asn_reader.asn(asn).prefixes:
            cidr = IPNetwork(ip_range)
            
            # 获取该 IP 段对应的国家代码
            try:
                country_response = country_reader.asn(cidr.network)
                country_code = country_response.country.iso_code

                # 存储 IP CIDR 段到对应的国家代码列表中
                country_cidr_map[country_code].add(cidr)
            except geoip2.errors.AddressNotFoundError:
                pass

    except geoip2.errors.AddressNotFoundError:
        pass

# 为每个国家代码生成 CIDR 输出文件
if not os.path.exists('outputs'):
    os.makedirs('outputs')

for country_code, cidrs in country_cidr_map.items():
    file_path = f"outputs/{country_code}.txt"
    with open(file_path, "w") as f:
        for cidr in cidrs.iter_cidrs():
            f.write(f"{cidr}\n")

print("Files have been created in the 'outputs' directory.")
