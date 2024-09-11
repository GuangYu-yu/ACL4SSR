import geoip2.database
import netaddr
import os

# Cloudflare 的 ASN 列表
cloudflare_asns = ['209242', '13335', '149648', '132892', '139242', '202623', '203898', '394536', '395747']

# 确保输出目录存在
os.makedirs("outputs", exist_ok=True)

def find_cloudflare_cidrs(asn_database, country_database):
    # 打开 MaxMind ASN 和国家数据库
    asn_reader = geoip2.database.Reader(asn_database)
    country_reader = geoip2.database.Reader(country_database)

    # 用于存储每个国家代码对应的 CIDR 地址段
    country_cidr_map = {}

    # 打开并读取 Cloudflare CIDR 数据（从 ASN 数据库中提取）
    for asn in cloudflare_asns:
        try:
            # 提取 ASN 对应的 CIDR
            print(f"Processing ASN: {asn}")
            response = asn_reader.asn(asn)
            network = netaddr.IPNetwork(response.network)

            # 查找国家代码
            try:
                country_response = country_reader.country(network.ip)
                country_code = country_response.country.iso_code

                # 如果该国家还没有记录，则初始化
                if country_code not in country_cidr_map:
                    country_cidr_map[country_code] = netaddr.IPSet()

                # 将 CIDR 添加到该国家代码的集合中
                country_cidr_map[country_code].add(network)

                print(f"ASN: {asn}, Country: {country_code}, Network: {network}")

            except geoip2.errors.AddressNotFoundError:
                print(f"Network {network} not found in country database")

        except Exception as e:
            print(f"Error processing ASN {asn}: {e}")

    # 输出每个国家的 CIDR 文件
    for country_code, cidrs in country_cidr_map.items():
        with open(f"outputs/{country_code}.txt", "w") as f:
            for cidr in cidrs.iter_cidrs():
                f.write(f"{cidr}\n")
                print(f"Writing CIDR {cidr} to outputs/{country_code}.txt")

if __name__ == "__main__":
    find_cloudflare_cidrs('GeoLite2-ASN.mmdb', 'GeoLite2-Country.mmdb')
