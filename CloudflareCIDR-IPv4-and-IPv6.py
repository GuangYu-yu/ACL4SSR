import os
import shutil
import zipfile
import requests
import ipaddress

# 下载 zip 文件，包含所有 ASN 的 IP 地址段数据
url = "https://github.com/ipverse/asn-ip/archive/refs/heads/master.zip"
r = requests.get(url)
with open("master.zip", "wb") as code:
    code.write(r.content)

# 解压下载的 zip 文件
with zipfile.ZipFile("master.zip", 'r') as zip_ref:
    zip_ref.extractall(".")

# 用于存储最终的 IPv4 和 IPv6 地址列表
ipv4_addresses = []
ipv6_addresses = []

# 指定需要包含的 ASN 列表
included_asns = ['209242', '13335', '149648', '132892', '139242', '202623', '203898', '394536', '395747']

# 遍历解压文件夹中的 ASN 文件夹
for root, dirs, files in os.walk("asn-ip-master/as"):
    asn = root.split('/')[-1]  # 提取 ASN 号
    if asn in included_asns:
        # 处理 IPv4 地址
        if 'ipv4-aggregated.txt' in files:
            with open(os.path.join(root, 'ipv4-aggregated.txt'), 'r') as file:
                ipv4s = file.read().splitlines()
                for ip in ipv4s:
                    # 忽略注释行
                    if not ip.startswith('#'):
                        ipv4_addresses.append(ip)
        
        # 处理 IPv6 地址
        if 'ipv6-aggregated.txt' in files:
            with open(os.path.join(root, 'ipv6-aggregated.txt'), 'r') as file:
                ipv6s = file.read().splitlines()
                for ip in ipv6s:
                    # 忽略注释行
                    if not ip.startswith('#'):
                        ipv6_addresses.append(ip)

# 将字符串形式的 CIDR 转换为网络对象
ipv4_networks = [ipaddress.IPv4Network(ip) for ip in ipv4_addresses]
ipv6_networks = [ipaddress.IPv6Network(ip) for ip in ipv6_addresses]

# 定义一个函数，计算网络的起始和结束 IP
def get_network_range(network):
    start_ip = network.network_address
    end_ip = network.broadcast_address
    return start_ip, end_ip

# 定义一个函数，合并相邻的 CIDR 范围
def merge_adjacent_cidr(networks):
    if not networks:
        return networks
    
    merged = []
    current = networks[0]  # 初始化为第一个 CIDR 段
    current_start, current_end = get_network_range(current)
    
    for net in networks[1:]:
        net_start, net_end = get_network_range(net)
        
        # 如果当前 CIDR 的结束地址和下一个 CIDR 的开始地址相邻，则合并
        if current_end + 1 == net_start:
            # 合并的结果是取当前 CIDR 的开始地址和下一个 CIDR 的结束地址
            current_end = net_end
        else:
            # 如果不相邻，将当前 CIDR 加入到合并后的列表，并更新当前 CIDR
            merged.append(ipaddress.IPv4Network((current_start, current_end - current_start + 1), strict=False))
            current_start, current_end = net_start, net_end
    
    # 最后一个 CIDR 段加入结果列表
    merged.append(ipaddress.IPv4Network((current_start, current_end - current_start + 1), strict=False))
    
    return merged

# 按照开始地址排序后进行合并
ipv4_merged = merge_adjacent_cidr(sorted(ipv4_networks, key=lambda net: net.network_address))
ipv6_merged = merge_adjacent_cidr(sorted(ipv6_networks, key=lambda net: net.network_address))

# 将合并后的结果写入文件
with open('Clash/CloudflareCIDR.txt', 'w') as file:
    for ip in ipv4_merged:
        file.write(f"{ip}\n")

with open('Clash/CloudflareCIDR-v6.txt', 'w') as file:
    for ip in ipv6_merged:
        file.write(f"{ip}\n")

# 清理临时文件
os.remove("master.zip")
shutil.rmtree("asn-ip-master")

print("合并完成，并生成了文件。")
