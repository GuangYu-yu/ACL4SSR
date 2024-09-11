import maxminddb

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

    # 检查CIDR是否属于目标地区
    for region_code, region_name in regions.items():
        if country == region_name:
            if ':' in cidr:  # IPv6 地址
                result[region_code]['ipv6'].append(cidr)
            else:  # IPv4 地址
                result[region_code]['ipv4'].append(cidr)

# 将结果保存到对应文件中
for region_code, data in result.items():
    with open(region_files[region_code], 'w') as f:
        f.write(f"IPv4 CIDR for {regions[region_code]}:\n")
        f.write('\n'.join(data['ipv4']) + '\n\n')
        f.write(f"IPv6 CIDR for {regions[region_code]}:\n")
        f.write('\n'.join(data['ipv6']) + '\n')

# 关闭数据库
db_reader.close()
