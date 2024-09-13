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
included_asns = ['209242', '13335', '149648', '132892', '139242', '202623', '203898', '394536', '395747']  # 需要包含的 ASN 列表

# 遍历 as 文件夹，提取符合条件的 ASN 数据
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

# 将 CIDR 字符串转换为 IPv4/IPv6 网络对象
ipv4_networks = [ipaddress.IPv4Network(ip) for ip in ipv4_addresses]
ipv6_networks = [ipaddress.IPv6Network(ip) for ip in ipv6_addresses]

def merge_adjacent_cidr(cidr_list):
    """
    合并相邻或重叠的 CIDR 范围
    :param cidr_list: 已排序的 IPv4Network 对象列表
    :return: 合并后的 CIDR 列表
    """
    merged = []  # 存储合并后的 CIDR 范围
    
    # 初始化当前正在处理的 CIDR 范围的起始和结束地址
    current = cidr_list[0]  # 第一个 CIDR 范围
    current_start = int(current.network_address)  # 起始地址转为整数
    current_end = int(current.broadcast_address)  # 结束地址转为整数

    # 遍历剩余的 CIDR 范围
    for net in cidr_list[1:]:
        net_start = int(net.network_address)  # 下一个 CIDR 的起始地址
        net_end = int(net.broadcast_address)  # 下一个 CIDR 的结束地址
        
        # 判断当前 CIDR 和下一个 CIDR 是否相邻或重叠
        if net_start <= current_end + 1:
            # 如果相邻或重叠，更新当前 CIDR 的结束地址
            current_end = max(current_end, net_end)
        else:
            # 如果不相邻，将当前合并好的 CIDR 加入列表
            merged.append(ipaddress.IPv4Network((current_start, current_end - current_start + 1), strict=False))
            # 更新为新的 CIDR 范围
            current_start = net_start
            current_end = net_end

    # 将最后一个合并的 CIDR 加入列表
    merged.append(ipaddress.IPv4Network((current_start, current_end - current_start + 1), strict=False))

    return merged

# 合并相邻的 IPv4 和 IPv6 CIDR 范围
ipv4_merged = merge_adjacent_cidr(sorted(ipv4_networks, key=lambda net: net.network_address))
ipv6_merged = merge_adjacent_cidr(sorted(ipv6_networks, key=lambda net: net.network_address))

# 将合并并排序后的 IPv4 结果写入文件
with open('Clash/CloudflareCIDR.txt', 'w') as file:
    for ip in ipv4_merged:
        file.write(f"{ip}\n")

# 将合并并排序后的 IPv6 结果写入文件
with open('Clash/CloudflareCIDR-v6.txt', 'w') as file:
    for ip in ipv6_merged:
        file.write(f"{ip}\n")

# 清理下载的 zip 文件和解压的文件夹
os.remove("master.zip")
shutil.rmtree("asn-ip-master")

print("合并完成，并生成了文件。")
