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

# 将 CIDR 转换为 IP 地址并去重
def cidr_to_ips(cidr_list):
    ip_set = set()
    for cidr in cidr_list:
        network = ipaddress.IPv4Network(cidr, strict=False) if ':' not in cidr else ipaddress.IPv6Network(cidr, strict=False)
        ip_set.update(network)
    return ip_set

ipv4_ips = cidr_to_ips(ipv4_addresses)
ipv6_ips = cidr_to_ips(ipv6_addresses)

# 将 IP 地址转换回 CIDR 并排序
def ips_to_cidrs(ip_set):
    sorted_ips = sorted(ip_set)
    return sorted(ipaddress.collapse_addresses(sorted_ips))

ipv4_merged_sorted = ips_to_cidrs(ipv4_ips)
ipv6_merged_sorted = ips_to_cidrs(ipv6_ips)

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

print("合并完成，并生成了文件。")
