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

# 直接使用从文件中读取的 CIDR 地址
ipv4_networks = [ipaddress.IPv4Network(ip) for ip in ipv4_addresses]
ipv6_networks = [ipaddress.IPv6Network(ip) for ip in ipv6_addresses]

# 合并重叠的 CIDR 范围
ipv4_collapsed = list(ipaddress.collapse_addresses(ipv4_networks))
ipv6_collapsed = list(ipaddress.collapse_addresses(ipv6_networks))

# 合并相邻的 CIDR 范围
def merge_adjacent_cidr(networks):
    # 排序网络地址
    networks = sorted(networks, key=lambda net: (net.network_address, net.prefixlen))
    merged = []
    current = networks[0]

    for net in networks[1:]:
        # 检查当前网段和下一个网段是否相邻
        if current.broadcast_address + 1 == net.network_address:
            # 合并相邻网段
            current = ipaddress.IPv4Network((current.network_address, current.num_addresses + net.num_addresses), strict=False)
        else:
            # 如果不能合并，则保存当前网段并更新为下一个网段
            merged.append(current)
            current = net
    merged.append(current)  # 添加最后一个网段
    return merged

# 对 IPv4 和 IPv6 网络进行合并相邻 CIDR 范围
ipv4_merged = merge_adjacent_cidr(ipv4_collapsed)
ipv6_merged = merge_adjacent_cidr(ipv6_collapsed)

# 对合并并排序后的 IPv4 和 IPv6 网络进行最终排序
ipv4_merged_sorted = sorted(ipv4_merged, key=lambda net: (net.network_address, net.prefixlen))
ipv6_merged_sorted = sorted(ipv6_merged, key=lambda net: (net.network_address, net.prefixlen))

# 将合并并排序后的 IPv4 结果写入文件
os.makedirs('Clash', exist_ok=True)
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
