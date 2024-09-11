import maxminddb
import ipaddress

# 打开 GeoLite2-Country.mmdb 数据库文件
db_reader = maxminddb.open_database('GeoLite2-Country.mmdb')

# 定义要查找的地区及其名称
regions = {
    'HK': 'Hong Kong',       # 香港
    'TW': 'Taiwan',          # 台湾
    'SG': 'Singapore',       # 新加坡
    'JP': 'Japan',           # 日本
    'KR': 'South Korea',     # 韩国
    'US': 'United States',   # 美国
    'GB': 'United Kingdom',  # 英国
    'DE': 'Germany',         # 德国
    'FR': 'France',          # 法国
    'AU': 'Australia',       # 澳大利亚
    'CN': 'China',           # 中国
    'IN': 'India',           # 印度
    'BR': 'Brazil',          # 巴西
    'MX': 'Mexico',          # 墨西哥
    'ZA': 'South Africa',    # 南非
    'RU': 'Russia',          # 俄罗斯
    'IT': 'Italy',           # 意大利
    'ES': 'Spain',           # 西班牙
    'NL': 'Netherlands',     # 荷兰
    'SE': 'Sweden',          # 瑞典
    'CH': 'Switzerland',     # 瑞士
    'BE': 'Belgium',         # 比利时
    'AR': 'Argentina',       # 阿根廷
    'NG': 'Nigeria',         # 尼日利亚
    'PH': 'Philippines'      # 菲律宾
}

# 文件名映射，保存 CIDR 列表到指定文件
region_files = {
    'HK': 'Clash/HK_cidr.txt',
    'TW': 'Clash/TW_cidr.txt',
    'SG': 'Clash/SG_cidr.txt',
    'JP': 'Clash/JP_cidr.txt',
    'KR': 'Clash/KR_cidr.txt',
    'US': 'Clash/US_cidr.txt',
    'GB': 'Clash/GB_cidr.txt',
    'DE': 'Clash/DE_cidr.txt',
    'FR': 'Clash/FR_cidr.txt',
    'AU': 'Clash/AU_cidr.txt',
    'CN': 'Clash/CN_cidr.txt',
    'IN': 'Clash/IN_cidr.txt',
    'BR': 'Clash/BR_cidr.txt',
    'MX': 'Clash/MX_cidr.txt',
    'ZA': 'Clash/ZA_cidr.txt',
    'RU': 'Clash/RU_cidr.txt',
    'IT': 'Clash/IT_cidr.txt',
    'ES': 'Clash/ES_cidr.txt',
    'NL': 'Clash/NL_cidr.txt',
    'SE': 'Clash/SE_cidr.txt',
    'CH': 'Clash/CH_cidr.txt',
    'BE': 'Clash/BE_cidr.txt',
    'AR': 'Clash/AR_cidr.txt',
    'NG': 'Clash/NG_cidr.txt',
    'PH': 'Clash/PH_cidr.txt'
}

# 初始化结果字典，用于保存各地区的 IPv4 和 IPv6 CIDR 列表
result = {region: {'ipv4': [], 'ipv6': []} for region in regions.keys()}

# 遍历数据库中的所有 CIDR 数据
for cidr, info in db_reader:
    country = info.get('country', {}).get('names', {}).get('en', '')

    # 将 CIDR 转换为字符串进行处理
    cidr_str = str(cidr)

    # 检查 CIDR 是否属于目标地区
    for region_code, region_name in regions.items():
        if country == region_name:
            try:
                # 将 CIDR 转换为 ip_network 对象来判断是 IPv4 还是 IPv6
                network = ipaddress.ip_network(cidr_str)
                if network.version == 6:
                    result[region_code]['ipv6'].append(cidr_str)  # 添加到 IPv6 列表
                else:
                    result[region_code]['ipv4'].append(cidr_str)  # 添加到 IPv4 列表
            except ValueError:
                # 如果 CIDR 无法转换为网络对象，则跳过
                continue

# 将结果保存到对应文件中
for region_code, data in result.items():
    if data['ipv4'] or data['ipv6']:  # 仅当有数据时才写入文件
        with open(region_files[region_code], 'w') as f:
            f.write('\n'.join(data['ipv4']) + '\n')  # 写入 IPv4 CIDR 列表
            f.write('\n'.join(data['ipv6']) + '\n')  # 写入 IPv6 CIDR 列表

# 关闭数据库
db_reader.close()
