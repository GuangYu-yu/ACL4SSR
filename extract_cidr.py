import maxminddb
import ipaddress

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
    # 遍历 IPv4 地址范围
    for ip in ipaddress.IPv4Network("0.0.0.0/0").hosts():
        country_data = reader.get(str(ip))
        if country_data and 'country' in country_data:
            country_name = country_data['country']['names']['en']
            for code, name in target_countries.items():
                if country_name == name:
                    cidr = f"{ip}/32"
                    country_cidrs[code].append(cidr)
    
    # 遍历 IPv6 地址范围
    for ip in ipaddress.IPv6Network("::/0").hosts():
        country_data = reader.get(str(ip))
        if country_data and 'country' in country_data:
            country_name = country_data['country']['names']['en']
            for code, name in target_countries.items():
                if country_name == name:
                    cidr = f"{ip}/128"
                    country_cidrs[code].append(cidr)

# 确保将结果写入到 /Clash 目录中
for code, cidrs in country_cidrs.items():
    if cidrs:
        with open(f'Clash/{code}_cidr.txt', 'w') as file:
            file.write('\n'.join(cidrs))
