import os
import shutil
import zipfile
import requests
import ipaddress

# 下载zip文件
url = "https://github.com/ipverse/asn-ip/archive/refs/heads/master.zip"
r = requests.get(url)
with open("master.zip", "wb") as code:
    code.write(r.content)

# 解压zip文件
with zipfile.ZipFile("master.zip", 'r') as zip_ref:
    zip_ref.extractall(".")

# 将IPv4和IPv6结果存储在两个列表中
ipv4_addresses = []
ipv6_addresses = []
included_asns = ['209242', '13335', '149648', '132892', '139242', '202623', '203898', '394536', '395747']

# 遍历as文件夹
for root, dirs, files in os.walk("asn-ip-master/as"):
    asn = root.split('/')[-1]
    if asn in included_asns:
        # 处理IPv4
        if 'ipv4-aggregated.txt' in files:
            with open(os.path.join(root, 'ipv4-aggregated.txt'), 'r') as file:
                ipv4s = file.read().splitlines()
                for ip in ipv4s:
                    # 忽略包含井号的行
                    if not ip.startswith('#'):
                        ipv4_addresses.append(ip)
        
        # 处理IPv6
        if 'ipv6-aggregated.txt' in files:
            with open(os.path.join(root, 'ipv6-aggregated.txt'), 'r') as file:
                ipv6s = file.read().splitlines()
                for ip in ipv6s:
                    # 忽略包含井号的行
                    if not ip.startswith('#'):
                        ipv6_addresses.append(ip)

# 将字符串转换为IPv4/IPv6网络对象
ipv4_networks = [ipaddress.IPv4Network(ip, strict=False) for ip in ipv4_addresses]
ipv6_networks = [ipaddress.IPv6Network(ip, strict=False) for ip in ipv6_addresses]

# 合并CIDR范围并排序
ipv4_merged_sorted = sorted(ipaddress.collapse_addresses(ipv4_networks), key=lambda net: (net.network_address, net.prefixlen))
ipv6_merged_sorted = sorted(ipaddress.collapse_addresses(ipv6_networks), key=lambda net: (net.network_address, net.prefixlen))

# 将合并并排序后的IPv4结果写入文件
with open('Clash/CloudflareCIDR.txt', 'w') as file:
    for ip in ipv4_merged_sorted:
        file.write(f"{ip}\n")

# 将合并并排序后的IPv6结果写入文件
with open('Clash/CloudflareCIDR-v6.txt', 'w') as file:
    for ip in ipv6_merged_sorted:
        file.write(f"{ip}\n")

# 清理下载的zip文件和解压的文件夹
os.remove("master.zip")
shutil.rmtree("asn-ip-master")
