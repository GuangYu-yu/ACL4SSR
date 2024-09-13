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

# 合并相邻的 CIDR 范围
def merge_adjacent_cidrs(cidrs):
    # 排序网络地址
    cidrs = sorted(cidrs, key=lambda net: (net.network, net.prefixlen))
    merged = []
    current = cidrs[0]

    for net in cidrs[1:]:
        # 检查当前网段和下一个网段是否相邻
        if current.broadcast + 1 == net.network:
            # 合并相邻网段
            current = IPNetwork((current.network, current.size + net.size))
        else:
            # 如果不能合并，则保存当前网段并更新为下一个网段
            merged.append(current)
            current = net
    merged.append(current)  # 添加最后一个网段
    return merged

# 保存 CIDR 到文件
def save_cidrs_to_file(filename, ipv4_cidrs, ipv6_cidrs):
    with open(filename, 'w') as f:
        # 仅写入 CIDR，不包含额外文本
        f.write('\n'.join(str(cidr) for cidr in ipv4_cidrs) + '\n')
        f.write('\n'.join(str(cidr) for cidr in ipv6_cidrs) + '\n')

# 各地区 CIDR 文件 URL
region_cidr_urls = {
    'Hong Kong': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/HK_cidr.txt',
    'Taiwan': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/TW_cidr.txt',
    'Japan': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/JP_cidr.txt',
    'South Korea': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/KR_cidr.txt',
    'India': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/IN_cidr.txt',
    'Singapore': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/SG_cidr.txt',
    'Thailand': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/TH_cidr.txt',
    'Vietnam': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/VN_cidr.txt',
    'Philippines': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/PH_cidr.txt',
    'Malaysia': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/MY_cidr.txt',
    'France': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/FR_cidr.txt',
    'Germany': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/DE_cidr.txt',
    'United Kingdom': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/GB_cidr.txt',
    'Italy': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/IT_cidr.txt',
    'Spain': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/ES_cidr.txt',
    'Russia': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/RU_cidr.txt',
    'Sweden': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/SE_cidr.txt',
    'Switzerland': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/CH_cidr.txt',
    'Poland': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/PL_cidr.txt',
    'United States': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/US_cidr.txt',
    'Canada': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/CA_cidr.txt',
    'Mexico': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/MX_cidr.txt',
    'Cuba': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/CU_cidr.txt',
    'Guatemala': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/GT_cidr.txt',
    'Dominican Republic': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/DO_cidr.txt',
    'Costa Rica': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/CR_cidr.txt',
    'Panama': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/PA_cidr.txt',
    'Honduras': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/HN_cidr.txt',
    'Jamaica': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/JM_cidr.txt',
    'Brazil': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/BR_cidr.txt',
    'Argentina': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/AR_cidr.txt',
    'Chile': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/CL_cidr.txt',
    'Colombia': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/CO_cidr.txt',
    'Peru': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/PE_cidr.txt',
    'Venezuela': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/VE_cidr.txt',
    'Uruguay': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/UY_cidr.txt',
    'Paraguay': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/PY_cidr.txt',
    'Bolivia': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/BO_cidr.txt',
    'Ecuador': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/EC_cidr.txt',
    'South Africa': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/ZA_cidr.txt',
    'Nigeria': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/NG_cidr.txt',
    'Egypt': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/EG_cidr.txt',
    'Kenya': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/KE_cidr.txt',
    'Algeria': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/DZ_cidr.txt',
    'Morocco': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/MA_cidr.txt',
    'Ghana': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/GH_cidr.txt',
    'Ethiopia': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/ET_cidr.txt',
    'Tanzania': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/TZ_cidr.txt',
    'Senegal': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/SN_cidr.txt',
    'Australia': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/AU_cidr.txt',
    'New Zealand': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/NZ_cidr.txt',
    'Fiji': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/FJ_cidr.txt',
    'Papua New Guinea': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/PG_cidr.txt',
    'Solomon Islands': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/SB_cidr.txt',
    'Vanuatu': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/VU_cidr.txt',
    'Tonga': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/TO_cidr.txt',
    'Wallis and Futuna': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/WF_cidr.txt',
    'Nauru': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/NR_cidr.txt',
    'Tuvalu': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/TV_cidr.txt',
    'Saudi Arabia': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/SA_cidr.txt',
    'United Arab Emirates': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/AE_cidr.txt',
    'Iran': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/IR_cidr.txt',
    'Iraq': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/IQ_cidr.txt',
    'Israel': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/IL_cidr.txt',
    'Jordan': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/JO_cidr.txt',
    'Kuwait': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/KW_cidr.txt',
    'Qatar': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/QA_cidr.txt'
}

# Cloudflare CIDR 文件 URL
cloudflare_url = 'https://raw.githubusercontent.com/GuangYu-yu/About-Cloudflare/main/output_folder/CloudflareCIDR合并地址.txt'

# 获取 Cloudflare 的 CIDR 列表
cloudflare_cidrs = read_cidr_file(cloudflare_url)

# 对每个地区执行 CIDR 重叠计算
for region_name, region_url in region_cidr_urls.items():
    # 获取地区 CIDR 列表
    region_cidrs = read_cidr_file(region_url)
    
    # 计算与 Cloudflare 的重叠部分
    ipv4_common_cidrs, ipv6_common_cidrs = find_ip_overlaps(region_cidrs, cloudflare_cidrs)
    
    # 合并相邻的 CIDR 范围
    ipv4_common_cidrs_merged = merge_adjacent_cidrs(ipv4_common_cidrs)
    ipv6_common_cidrs_merged = merge_adjacent_cidrs(ipv6_common_cidrs)
    
    # 合并并排序 IPv4 和 IPv6 的 CIDR 结果
    all_cidrs = sorted(set(ipv4_common_cidrs_merged + ipv6_common_cidrs_merged), key=lambda x: (x.version, x))
    
    # 保存结果到对应文件
    output_filename = f"Cloudflare-{region_name}.txt"
    save_cidrs_to_file(output_filename, ipv4_common_cidrs_merged, ipv6_common_cidrs_merged)

print("重叠计算完成，CIDR 文件已生成。")
