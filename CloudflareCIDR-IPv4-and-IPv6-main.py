import os
import shutil
import zipfile
import requests
import re  # 导入正则表达式库

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
                ipv4_addresses.extend(ipv4s)
        
        # 处理IPv6
        if 'ipv6-aggregated.txt' in files:
            with open(os.path.join(root, 'ipv6-aggregated.txt'), 'r') as file:
                ipv6s = file.read().splitlines()
                ipv6_addresses.extend(ipv6s)

# 正则表达式用于匹配IPv4和IPv6地址与子网掩码
ipv4_regex = re.compile(r'^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})$')
ipv6_regex = re.compile(r'^([a-fA-F0-9]{1,4}:){1,7}[a-fA-F0-9]{1,4}(/\d{1,3})$')

# 将IPv4结果写入一个新的文件
with open('Clash/CloudflareCIDR.list', 'w') as file:
    for ip in ipv4_addresses:
        # 检查IP是否符合IPv4/子网掩码格式
        if ipv4_regex.match(ip):
            file.write(f"IP-CIDR,{ip},no-resolve\n")
        else:
            file.write(f"{ip}\n")

# 将IPv6结果写入一个新的文件
with open('Clash/CloudflareCIDR-v6.list', 'w') as file:
    for ip in ipv6_addresses:
        # 检查IP是否符合IPv6/子网掩码格式
        if ipv6_regex.match(ip):
            file.write(f"IP-CIDR6,{ip},no-resolve\n")
        else:
            file.write(f"{ip}\n")

# 清理下载的zip文件和解压的文件夹
os.remove("master.zip")
shutil.rmtree("asn-ip-master")
