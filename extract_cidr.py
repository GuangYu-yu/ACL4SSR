import maxminddb

# 定义目标地区的ISO代码
target_countries = {
    'HK': 'Hong Kong',
    'JP': 'Japan',
    'KR': 'South Korea',
    'SG': 'Singapore',
    'TW': 'Taiwan'
}

# 初始化一个字典来存储每个国家的 CIDR
country_cidrs = {country_code: [] for country_code in target_countries}

# 读取 GeoLite2 数据库
with maxminddb.open_database('GeoLite2-Country.mmdb') as reader:
    for ip in reader:
        country_data = reader.get(ip)
        if country_data and 'country' in country_data:
            country_name = country_data['country']['names']['en']
            for code, name in target_countries.items():
                if country_name == name:
                    cidr = ip  # 获取对应的 CIDR
                    if ':' in cidr:  # 区分 IPv6
                        country_cidrs[code].append(cidr)

# 确保将结果写入到 /Clash 目录中
for code, cidrs in country_cidrs.items():
    if cidrs:
        with open(f'Clash/{code}_cidr.txt', 'w') as file:
            file.write('\n'.join(cidrs))
