import requests
from netaddr import IPSet, IPNetwork
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

# 读取远程 CIDR 文件
def read_cidr_file(url):
    response = requests.get(url)
    return response.text.strip().splitlines()

# 找出 CIDR 列表的重叠部分（针对 IPv4 和 IPv6）
def find_ip_overlaps(region_cidrs, cloudflare_cidrs):
    region_set = IPSet(region_cidrs)
    cloudflare_set = IPSet(cloudflare_cidrs)
    overlap_set = region_set & cloudflare_set  # 找到重叠部分
    return sorted(overlap_set.iter_cidrs())

# 合并相邻的 CIDR 范围
def merge_adjacent_cidrs(cidrs):
    if not cidrs:
        return []

    cidrs = sorted(cidrs, key=lambda net: (net.network, net.prefixlen))
    merged = []
    current = cidrs[0]

    for net in cidrs[1:]:
        # 将 IPNetwork 转换为整数以进行比较
        if int(current.network) + current.size == int(net.network):  # 比较是否相邻
            # 如果相邻，扩展 current 的 CIDR 范围
            current = IPNetwork((current.network, current.prefixlen - 1))  # 合并网络
        else:
            merged.append(current)
            current = net
    merged.append(current)
    return merged

# 保存 CIDR 到文件
def save_cidrs_to_file(filename, cidrs):
    with open(filename, 'w') as f:
        f.write('\n'.join(str(cidr) for cidr in cidrs) + '\n')

# 处理每个地区 CIDR 与 Cloudflare 重叠部分，并保存结果
def process_region_cidrs(region_name, region_url, cloudflare_cidrs):
    print(f"正在处理 {region_name} 的 CIDR 数据...")
    region_cidrs = read_cidr_file(region_url)
    
    ipv4_region = [cidr for cidr in region_cidrs if IPNetwork(cidr).version == 4]
    ipv6_region = [cidr for cidr in region_cidrs if IPNetwork(cidr).version == 6]

    ipv4_overlap = find_ip_overlaps(ipv4_region, cloudflare_cidrs['ipv4'])
    ipv6_overlap = find_ip_overlaps(ipv6_region, cloudflare_cidrs['ipv6'])

    ipv4_merged = merge_adjacent_cidrs(ipv4_overlap)
    ipv6_merged = merge_adjacent_cidrs(ipv6_overlap)

    save_cidrs_to_file(f"Cloudflare-{region_name}.txt", ipv4_merged + ipv6_merged)
    print(f"{region_name} 处理完成！")

# 主函数，获取 Cloudflare CIDR 并处理所有地区
def main():
    # Cloudflare CIDR 文件 URL
    cloudflare_url = 'https://raw.githubusercontent.com/GuangYu-yu/About-Cloudflare/main/output_folder/CloudflareCIDR合并地址.txt'
    cloudflare_cidrs = read_cidr_file(cloudflare_url)
    
    # 分离 IPv4 和 IPv6
    cloudflare_ipv4 = [cidr for cidr in cloudflare_cidrs if IPNetwork(cidr).version == 4]
    cloudflare_ipv6 = [cidr for cidr in cloudflare_cidrs if IPNetwork(cidr).version == 6]
    
    cloudflare_cidrs_dict = {'ipv4': cloudflare_ipv4, 'ipv6': cloudflare_ipv6}

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

    # 获取系统的 CPU 核心数量，作为线程池的最大线程数
    max_workers = os.cpu_count()
    
    print(f"使用 {max_workers} 个线程来并发处理 CIDR 数据...")

    # 使用 ThreadPoolExecutor 来并发处理多个地区的 CIDR
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_region_cidrs, region_name, region_url, cloudflare_cidrs_dict): region_name 
                   for region_name, region_url in region_cidr_urls.items()}

        # 等待所有线程完成
        for future in as_completed(futures):
            region_name = futures[future]
            try:
                future.result()
            except Exception as exc:
                print(f"{region_name} 处理时出现错误: {exc}")

    print("所有地区的重叠计算和文件生成完成。")

if __name__ == "__main__":
    main()
