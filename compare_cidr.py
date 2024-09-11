import ipaddress
import requests

# 定义地区的文件 URL 和输出文件名
regions = {
    'HK': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/HK_cidr.txt',
    'TW': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/TW_cidr.txt',
    'SG': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/SG_cidr.txt',
    'JP': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/JP_cidr.txt',
    'KR': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/KR_cidr.txt'
}

output_files = {
    'HK': 'Cloudflare-HK.txt',
    'TW': 'Cloudflare-TW.txt',
    'SG': 'Cloudflare-SG.txt',
    'JP': 'Cloudflare-JP.txt',
    'KR': 'Cloudflare-KR.txt'
}

# 加载 Cloudflare CIDR 文件
cloudflare_cidr_url = 'https://raw.githubusercontent.com/GuangYu-yu/About-Cloudflare/main/output_folder/CIDR.txt'
cloudflare_cidr_list = requests.get(cloudflare_cidr_url).text.splitlines()

# 对 Cloudflare CIDR 转换为 IP 网络对象
cloudflare_cidr_networks = [ipaddress.ip_network(cidr.strip()) for cidr in cloudflare_cidr_list if cidr.strip()]

# 遍历每个地区的 CIDR 文件，进行比较
for region, region_url in regions.items():
    # 通过 URL 获取地区的 CIDR 文件
    region_cidr_list = requests.get(region_url).text.splitlines()

    # 对比地区和 Cloudflare 的 CIDR，保留重复部分
    common_cidrs = []
    for region_cidr in region_cidr_list:
        region_cidr = region_cidr.strip()
        if not region_cidr:
            continue
        region_network = ipaddress.ip_network(region_cidr)
        for cloudflare_network in cloudflare_cidr_networks:
            if region_network.overlaps(cloudflare_network):
                common_cidrs.append(region_cidr)
                break  # 找到重叠就跳出

    # 去重、排序
    common_cidrs = sorted(set(common_cidrs), key=lambda x: ipaddress.ip_network(x))

    # 将结果写入文件
    with open(output_files[region], 'w') as f:
        f.write('\n'.join(common_cidrs) + '\n')
