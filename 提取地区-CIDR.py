import os
import maxminddb
import ipaddress

# 创建保存结果的目录
os.makedirs('Country', exist_ok=True)

# 打开 GeoLite2-Country.mmdb 数据库文件
db_reader = maxminddb.open_database('Country.mmdb')

# 定义要查找的地区及其名称
regions = {
    'HK': 'Hong Kong',        # 香港特别行政区
    'TW': 'Taiwan',           # 台湾省
    'JP': 'Japan',            # 日本
    'KR': 'South Korea',      # 韩国
    'IN': 'India',            # 印度
    'SG': 'Singapore',        # 新加坡
    'TH': 'Thailand',         # 泰国
    'VN': 'Vietnam',          # 越南
    'PH': 'Philippines',      # 菲律宾
    'MY': 'Malaysia',         # 马来西亚

    # 欧洲
    'FR': 'France',           # 法国
    'DE': 'Germany',          # 德国
    'GB': 'United Kingdom',   # 英国
    'IT': 'Italy',            # 意大利
    'ES': 'Spain',            # 西班牙
    'RU': 'Russia',           # 俄罗斯
    'SE': 'Sweden',           # 瑞典
    'CH': 'Switzerland',      # 瑞士
    'PL': 'Poland',           # 波兰
    'GR': 'Greece',           # 希腊

    # 北美洲
    'US': 'United States',    # 美国
    'CA': 'Canada',           # 加拿大
    'MX': 'Mexico',           # 墨西哥
    'CU': 'Cuba',             # 古巴
    'GT': 'Guatemala',        # 危地马拉
    'DO': 'Dominican Republic', # 多米尼加共和国
    'CR': 'Costa Rica',       # 哥斯达黎加
    'PA': 'Panama',           # 巴拿马
    'HN': 'Honduras',         # 洪都拉斯
    'JM': 'Jamaica',          # 牙买加

    # 南美洲
    'BR': 'Brazil',           # 巴西
    'AR': 'Argentina',        # 阿根廷
    'CL': 'Chile',            # 智利
    'CO': 'Colombia',         # 哥伦比亚
    'PE': 'Peru',             # 秘鲁
    'VE': 'Venezuela',        # 委内瑞拉
    'UY': 'Uruguay',          # 乌拉圭
    'PY': 'Paraguay',         # 巴拉圭
    'BO': 'Bolivia',          # 玻利维亚
    'EC': 'Ecuador',          # 厄瓜多尔

    # 非洲
    'ZA': 'South Africa',     # 南非
    'NG': 'Nigeria',          # 尼日利亚
    'EG': 'Egypt',            # 埃及
    'KE': 'Kenya',            # 肯尼亚
    'DZ': 'Algeria',          # 阿尔及利亚
    'MA': 'Morocco',          # 摩洛哥
    'GH': 'Ghana',            # 加纳
    'ET': 'Ethiopia',         # 埃塞俄比亚
    'TZ': 'Tanzania',         # 坦桑尼亚
    'SN': 'Senegal',          # 塞内加尔

    # 大洋洲
    'AU': 'Australia',        # 澳大利亚
    'NZ': 'New Zealand',      # 新西兰
    'FJ': 'Fiji',             # 斐济
    'PG': 'Papua New Guinea', # 巴布亚新几内亚
    'SB': 'Solomon Islands',  # 所罗门群岛
    'VU': 'Vanuatu',          # 瓦努阿图
    'TO': 'Tonga',            # 汤加
    'WF': 'Wallis and Futuna', # 瓦利斯和富图纳
    'NR': 'Nauru',            # 瑙鲁
    'TV': 'Tuvalu',           # 图瓦卢

    # 中东
    'SA': 'Saudi Arabia',     # 沙特阿拉伯
    'AE': 'United Arab Emirates', # 阿联酋
    'IR': 'Iran',             # 伊朗
    'IQ': 'Iraq',             # 伊拉克
    'IL': 'Israel',           # 以色列
    'JO': 'Jordan',           # 约旦
    'KW': 'Kuwait',           # 科威特
    'QA': 'Qatar'             # 卡塔尔
}

# 文件名映射，保存 CIDR 列表到指定文件
region_files = {region: f'Country/{region}_cidr.txt' for region in regions.keys()}

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
            if data['ipv4']:
                f.write('\n'.join(data['ipv4']) + '\n')  # 写入 IPv4 CIDR 列表
            if data['ipv6']:
                f.write('\n'.join(data['ipv6']) + '\n')  # 写入 IPv6 CIDR 列表

# 关闭数据库
db_reader.close()
