import maxminddb
import ipaddress

# 打开 GeoLite2-Country.mmdb 文件
db_reader = maxminddb.open_database('GeoLite2-Country.mmdb')

# 定义要查找的地区
regions = {
    'HK': 'Hong Kong',
    'TW': 'Taiwan',
    'SG': 'Singapore',
    'JP': 'Japan',
    'KR': 'South Korea'
}

# 文件名映射
region_files = {
    'HK': 'HK_cidr.txt',
    'TW': 'TW_cidr.txt',
    'SG': 'SG_cidr.txt',
    'JP': 'JP_cidr.txt',
    'KR': 'KR_cidr.txt'
}

# 用于保存结果的字典
result = {region: {'ipv4': [], 'ipv6': []} for region in regions.keys()}

# 遍历数据库中的所有数据
for cidr, info in db_reader:
    country = info.get('country', {}).get('names', {}).get('en', '')

    # 仅打印匹配的地区
    if country in regions.values():
        print(f"Match found for {country}: CIDR = {cidr}")

    # 将 CIDR 转换为字符串进行处理
    cidr_str = str(cidr)

    # 检查CIDR是否属于目标地区
    for region_code, region_name in regions.items():
        if country == region_name:
            try:
                # 将CIDR转换为ip_network对象来判断是IPv4还是IPv6
                network = ipaddress.ip_network(cidr_str)
                if network.version == 6:
                    result[region_code]['ipv6'].append(cidr_str)
                else:
                    result[region_code]['ipv4'].append(cidr_str)
            except ValueError:
                # 如果 cidr 无法转换为网络对象，跳过
                continue

# 将结果保存到对应文件中
for region_code, data in result.items():
    if data['ipv4'] or data['ipv6']:  # 只在有数据时写入文件
        with open(region_files[region_code], 'w') as f:
            f.write(f"IPv4 CIDR for {regions[region_code]}:\n")
            f.write('\n'.join(data['ipv4']) + '\n\n')
            f.write(f"IPv6 CIDR for {regions[region_code]}:\n")
            f.write('\n'.join(data['ipv6']) + '\n')

# 关闭数据库
db_reader.close()
