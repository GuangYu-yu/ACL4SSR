import geoip2.database
import netaddr
import os

# 确保 outputs 目录存在
os.makedirs("outputs", exist_ok=True)

def find_overlaps(asn_database, country_database, cidr_file):
    # 打开 MaxMind ASN 和国家数据库
    asn_reader = geoip2.database.Reader(asn_database)
    country_reader = geoip2.database.Reader(country_database)

    # 用于存储每个国家代码对应的 CIDR 地址段
    country_cidr_map = {}

    # 打开并读取 CIDR 文件
    with open(cidr_file, "r") as f:
        for line in f:
            try:
                # 解析每一行的 CIDR
                cidr = netaddr.IPNetwork(line.strip())
                
                # 使用 ASN 数据库查找该 CIDR 的 ASN 信息
                asn = asn_reader.asn(cidr.network)
                
                # 使用国家数据库查找该 CIDR 的国家代码
                country_code = country_reader.country(cidr.network).iso_code

                # 打印调试信息
                print(f"Processing CIDR: {cidr}, ASN: {asn.autonomous_system_number}, Country: {country_code}")

                # 如果这个国家代码还没有记录，则初始化
                if country_code not in country_cidr_map:
                    country_cidr_map[country_code] = netaddr.IPSet()

                # 添加 CIDR 到对应国家代码的集合中
                country_cidr_map[country_code].add(cidr)

            except Exception as e:
                # 捕捉异常并打印出错的 CIDR 信息
                print(f"Error processing {line.strip()}: {e}")

    # 为每个国家代码生成 CIDR 输出文件
    for country_code, cidrs in country_cidr_map.items():
        with open(f"outputs/{country_code}.txt", "w") as f:
            for cidr in cidrs.iter_cidrs():
                # 将 CIDR 写入文件
                f.write(f"{cidr}\n")
                print(f"Writing CIDR {cidr} to outputs/{country_code}.txt")

if __name__ == "__main__":
    # 执行查找重叠的功能
    find_overlaps('GeoLite2-ASN.mmdb', 'GeoLite2-Country.mmdb', 'CIDR.txt')
