import os
import shutil
import zipfile
import requests
import ipaddress

# 下载 zip 文件
url = "https://github.com/ipverse/asn-ip/archive/refs/heads/master.zip"
r = requests.get(url)
with open("master.zip", "wb") as code:
    code.write(r.content)

# 解压 zip 文件
with zipfile.ZipFile("master.zip", 'r') as zip_ref:
    zip_ref.extractall(".")

# 将 IPv4 和 IPv6 地址结果存储在两个列表中
ipv4_addresses = []
ipv6_addresses = []
included_asns = ['209242', '13335', '149648', '132892', '139242', '202623', '203898', '394536', '395747']

# 遍历 as 文件夹
for root, dirs, files in os.walk("asn-ip-master/as"):
    asn = root.split('/')[-1]  # 提取 ASN
    if asn in included_asns:
        # 处理 IPv4 地址
        if 'ipv4-aggregated.txt' in files:
            with open(os.path.join(root, 'ipv4-aggregated.txt'), 'r') as file:
                ipv4s = file.read().splitlines()
                for ip in ipv4s:
                    # 忽略包含井号的行
                    if not ip.startswith('#'):
                        ipv4_addresses.append(ip)
        
        # 处理 IPv6 地址
        if 'ipv6-aggregated.txt' in files:
            with open(os.path.join(root, 'ipv6-aggregated.txt'), 'r') as file:
                ipv6s = file.read().splitlines()
                for ip in ipv6s:
                    # 忽略包含井号的行
                    if not ip.startswith('#'):
                        ipv6_addresses.append(ip)

# 将字符串转换为 IPv4/IPv6 网络对象
ipv4_networks = [ipaddress.IPv4Network(ip, strict=False) for ip in ipv4_addresses]
ipv6_networks = [ipaddress.IPv6Network(ip, strict=False) for ip in ipv6_addresses]

def calculate_and_merge_networks(networks):
    # 计算网络的开始和结束地址，并排序
    ranges = []
    for net in networks:
        start_ip = net.network_address
        end_ip = net.broadcast_address
        ranges.append((start_ip, end_ip))

    # 排序
    ranges.sort()

    # 合并相邻的范围
    merged_ranges = []
    current_start, current_end = ranges[0]
    
    for start, end in ranges[1:]:
        if start <= current_end + 1:  # 检查是否相邻或重叠
            current_end = max(current_end, end)
        else:
            merged_ranges.append((current_start, current_end))
            current_start, current_end = start, end

    merged_ranges.append((current_start, current_end))

    # 转换为网络对象（支持 IPv4 和 IPv6）
    merged_networks = []
    for start, end in merged_ranges:
        # 根据 IP 版本选择适当的网络类型
        if isinstance(start, ipaddress.IPv4Address):
            merged_networks.append(ipaddress.ip_network(f"{start}/{ipaddress.IPv4Address(end).max_prefixlen}", strict=False))
        elif isinstance(start, ipaddress.IPv6Address):
            merged_networks.append(ipaddress.ip_network(f"{start}/{ipaddress.IPv6Address(end).max_prefixlen}", strict=False))

    return merged_networks

# 合并并排序 IPv4 和 IPv6
ipv4_merged_sorted = calculate_and_merge_networks(ipv4_networks)
ipv6_merged_sorted = calculate_and_merge_networks(ipv6_networks)

# 将合并并排序后的 IPv4 结果写入文件
with open('Clash/CloudflareCIDR.txt', 'w') as file:
    for ip in ipv4_merged_sorted:
        file.write(f"{ip}\n")

# 将合并并排序后的 IPv6 结果写入文件
with open('Clash/CloudflareCIDR-v6.txt', 'w') as file:
    for ip in ipv6_merged_sorted:
        file.write(f"{ip}\n")

# 清理下载的 zip 文件和解压的文件夹
os.remove("master.zip")
shutil.rmtree("asn-ip-master")
