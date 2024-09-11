import geoip2.database
from netaddr import IPNetwork, IPSet
from collections import defaultdict

# 打开 GeoLite2 数据库
asn_reader = geoip2.database.Reader("GeoLite2-ASN.mmdb")
country_reader = geoip2.database.Reader("GeoLite2-Country.mmdb")

# 读取 Cloudflare CIDR 列表
with open("CIDR.txt") as f:
    cloudflare_cidrs = [IPNetwork(line.strip()) for line in f if line.strip()]

# 存储结果的字典：以国家代码为键，存储对应 CIDR
country_cidr_map = defaultdict(IPSet)

# 遍历每个 Cloudflare 的 CIDR，获取对应的 ASN 和国家代码
for cidr in cloudflare_cidrs:
    try:
        # 从 ASN 数据库获取 ASN 信息
        asn_response = asn_reader.asn(cidr.network)
        asn = asn_response.autonomous_system_number

        # 从国家数据库获取国家代码
        country_response = country_reader.asn(cidr.network)
        country_code = country_response.country.iso_code

        # 存储 IP CIDR 段到对应的国家代码列表中
        country_cidr_map[country_code].add(cidr)

    except geoip2.errors.AddressNotFoundError:
        # 处理无法找到地址的错误
        pass

# 为每个国家代码生成 CIDR 输出文件
for country_code, cidrs in country_cidr_map.items():
    with open(f"outputs/{country_code}.txt", "w") as f:
        for cidr in cidrs.iter_cidrs():
            f.write(f"{cidr}\n")
