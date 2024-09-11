import requests
from netaddr import IPSet, IPNetwork

# 读取远程 CIDR 文件
def read_cidr_file(url):
    response = requests.get(url)
    return response.text.strip().splitlines()

# 找出 CIDR 列表的重叠部分
def find_ip_overlaps(region_cidrs, cloudflare_cidrs):
    # 分离 IPv4 和 IPv6 的 CIDR 列表
    ipv4_region = [cidr for cidr in region_cidrs if IPNetwork(cidr).version == 4]
    ipv6_region = [cidr for cidr in region_cidrs if IPNetwork(cidr).version == 6]
    ipv4_cloudflare = [cidr for cidr in cloudflare_cidrs if IPNetwork(cidr).version == 4]
    ipv6_cloudflare = [cidr for cidr in cloudflare_cidrs if IPNetwork(cidr).version == 6]
    
    # 使用 IPSet 找出重叠的 IP 部分
    ipv4_region_set = IPSet(ipv4_region)
    ipv4_cloudflare_set = IPSet(ipv4_cloudflare)
    ipv6_region_set = IPSet(ipv6_region)
    ipv6_cloudflare_set = IPSet(ipv6_cloudflare)
    
    # 计算重叠的 IPv4 和 IPv6 CIDR
    ipv4_overlap_set = ipv4_region_set & ipv4_cloudflare_set
    ipv6_overlap_set = ipv6_region_set & ipv6_cloudflare_set
    
    # 返回排序后的重叠 CIDR 列表
    return sorted(ipv4_overlap_set.iter_cidrs()), sorted(ipv6_overlap_set.iter_cidrs())

# 保存 CIDR 到文件
def save_cidrs_to_file(filename, ipv4_cidrs, ipv6_cidrs):
    with open(filename, 'w') as f:
        # 仅写入 CIDR，不包含额外文本
        f.write('\n'.join(str(cidr) for cidr in ipv4_cidrs) + '\n')
        f.write('\n'.join(str(cidr) for cidr in ipv6_cidrs) + '\n')

# 各地区 CIDR 文件 URL
region_cidr_urls = {
    'HK': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/HK_cidr.txt',  # 香港
    'SG': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/SG_cidr.txt',  # 新加坡
    'JP': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/JP_cidr.txt',  # 日本
    'KR': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/KR_cidr.txt',  # 韩国
    'TW': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/TW_cidr.txt'   # 台湾
}

# Cloudflare CIDR 文件 URL
cloudflare_url = 'https://raw.githubusercontent.com/GuangYu-yu/About-Cloudflare/main/output_folder/CIDR.txt'

# 获取 Cloudflare 的 CIDR 列表
cloudflare_cidrs = read_cidr_file(cloudflare_url)

# 对每个地区执行 CIDR 重叠计算
for region_code, region_url in region_cidr_urls.items():
    # 获取地区 CIDR 列表
    region_cidrs = read_cidr_file(region_url)
    
    # 计算与 Cloudflare 的重叠部分
    ipv4_common_cidrs, ipv6_common_cidrs = find_ip_overlaps(region_cidrs, cloudflare_cidrs)
    
    # 合并并排序 IPv4 和 IPv6 的 CIDR 结果
    all_cidrs = sorted(set(ipv4_common_cidrs + ipv6_common_cidrs), key=lambda x: (x.version, x))

    # 保存结果到对应文件
    output_filename = f"Cloudflare-{region_code}.txt"
    save_cidrs_to_file(output_filename, ipv4_common_cidrs, ipv6_common_cidrs)

print("重叠计算完成，CIDR 文件已生成。")
