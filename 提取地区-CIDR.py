import maxminddb
import ipaddress
import os

# 打开 GeoLite2-Country.mmdb 数据库文件
db_reader = maxminddb.open_database('GeoLite2-Country.mmdb')

# 初始化结果字典，用于保存各地区的 IPv4 和 IPv6 CIDR 列表
result = {}

# 遍历数据库中的所有 CIDR 数据
for cidr, info in db_reader:
    country = info.get('country', {}).get('names', {}).get('en', '')
    
    if country:
        # 将 CIDR 转换为字符串进行处理
        cidr_str = str(cidr)
        
        # 将区域名称映射到结果字典
        if country not in result:
            result[country] = {'ipv4': [], 'ipv6': []}
        
        try:
            # 将 CIDR 转换为 ip_network 对象来判断是 IPv4 还是 IPv6
            network = ipaddress.ip_network(cidr_str)
            if network.version == 6:
                result[country]['ipv6'].append(cidr_str)  # 添加到 IPv6 列表
            else:
                result[country]['ipv4'].append(cidr_str)  # 添加到 IPv4 列表
        except ValueError:
            # 如果 CIDR 无法转换为网络对象，则跳过
            continue

# 动态生成区域和文件名映射
regions = {country: country for country in result.keys()}
region_files = {country: f'Clash/{country}_cidr.txt' for country in result.keys()}

# 确保保存目录存在
for file_path in region_files.values():
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

# 将结果保存到对应文件中
for region_name, data in result.items():
    if data['ipv4'] or data['ipv6']:  # 仅当有数据时才写入文件
        try:
            with open(region_files[region_name], 'w') as f:
                if data['ipv4']:
                    f.write('\n'.join(data['ipv4']) + '\n')  # 写入 IPv4 CIDR 列表
                if data['ipv6']:
                    f.write('\n'.join(data['ipv6']) + '\n')  # 写入 IPv6 CIDR 列表
        except IOError as e:
            print(f"Error writing file {region_files[region_name]}: {e}")

# 关闭数据库
db_reader.close()
