import requests
import os
from netaddr import IPSet, IPNetwork

os.makedirs('CF-Country', exist_ok=True)  # 创建文件夹

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
        f.write('\n'.join(str(cidr) for cidr in ipv4_cidrs) + '\n')
        f.write('\n'.join(str(cidr) for cidr in ipv6_cidrs) + '\n')

# 各地区 CIDR 文件 URL
region_cidr_urls = {
    'Hong Kong': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/HK_cidr.txt',  # 香港特别行政区
    'Taiwan': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/TW_cidr.txt',  # 台湾省
    'Japan': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/JP_cidr.txt',  # 日本
    'South Korea': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/KR_cidr.txt',  # 韩国
    'India': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/IN_cidr.txt',  # 印度
    'Singapore': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/SG_cidr.txt',  # 新加坡
    'Thailand': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/TH_cidr.txt',  # 泰国
    'Vietnam': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/VN_cidr.txt',  # 越南
    'Philippines': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/PH_cidr.txt',  # 菲律宾
    'Malaysia': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/MY_cidr.txt',  # 马来西亚
    'France': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/FR_cidr.txt',  # 法国
    'Germany': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/DE_cidr.txt',  # 德国
    'United Kingdom': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/GB_cidr.txt',  # 英国
    'Italy': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/IT_cidr.txt',  # 意大利
    'Spain': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/ES_cidr.txt',  # 西班牙
    'Russia': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/RU_cidr.txt',  # 俄罗斯
    'Sweden': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/SE_cidr.txt',  # 瑞典
    'Switzerland': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/CH_cidr.txt',  # 瑞士
    'Poland': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/PL_cidr.txt',  # 波兰
    'United States': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/US_cidr.txt',  # 美国
    'Canada': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/CA_cidr.txt',  # 加拿大
    'Mexico': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/MX_cidr.txt',  # 墨西哥
    'Cuba': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/CU_cidr.txt',  # 古巴
    'Guatemala': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/GT_cidr.txt',  # 危地马拉
    'Dominican Republic': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/DO_cidr.txt',  # 多米尼加
    'Costa Rica': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/CR_cidr.txt',  # 哥斯达黎加
    'Panama': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/PA_cidr.txt',  # 巴拿马
    'Honduras': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/HN_cidr.txt',  # 洪都拉斯
    'Jamaica': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/JM_cidr.txt',  # 牙买加
    'Brazil': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/BR_cidr.txt',  # 巴西
    'Argentina': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/AR_cidr.txt',  # 阿根廷
    'Chile': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/CL_cidr.txt',  # 智利
    'Colombia': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/CO_cidr.txt',  # 哥伦比亚
    'Peru': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/PE_cidr.txt',  # 秘鲁
    'Venezuela': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/VE_cidr.txt',  # 委内瑞拉
    'Uruguay': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/UY_cidr.txt',  # 乌拉圭
    'Paraguay': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/PY_cidr.txt',  # 巴拉圭
    'Bolivia': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/BO_cidr.txt',  # 玻利维亚
    'Ecuador': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/EC_cidr.txt',  # 厄瓜多尔
    'South Africa': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/ZA_cidr.txt',  # 南非
    'Nigeria': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/NG_cidr.txt',  # 尼日利亚
    'Egypt': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/EG_cidr.txt',  # 埃及
    'Kenya': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/KE_cidr.txt',  # 肯尼亚
    'Algeria': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/DZ_cidr.txt',  # 阿尔及利亚
    'Morocco': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/MA_cidr.txt',  # 摩洛哥
    'Ghana': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/GH_cidr.txt',  # 加纳
    'Ethiopia': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/ET_cidr.txt',  # 埃塞俄比亚
    'Tanzania': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/TZ_cidr.txt',  # 坦桑尼亚
    'Senegal': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/SN_cidr.txt',  # 塞内加尔
    'Australia': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/AU_cidr.txt',  # 澳大利亚
    'New Zealand': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/NZ_cidr.txt',  # 新西兰
    'Fiji': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/FJ_cidr.txt',  # 斐济
    'Papua New Guinea': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/PG_cidr.txt',  # 巴布亚新几内亚
    'Solomon Islands': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/SB_cidr.txt',  # 所罗门群岛
    'Vanuatu': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/VU_cidr.txt',  # 瓦努阿图
    'Tonga': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/TO_cidr.txt',  # 汤加
    'Wallis and Futuna': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/WF_cidr.txt',  # 瓦利斯和富图纳
    'Nauru': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/NR_cidr.txt',  # 瑙鲁
    'Tuvalu': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/TV_cidr.txt',  # 图瓦卢
    'Saudi Arabia': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/SA_cidr.txt',  # 沙特阿拉伯
    'United Arab Emirates': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/AE_cidr.txt',  # 阿联酋
    'Iran': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/IR_cidr.txt',  # 伊朗
    'Iraq': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/IQ_cidr.txt',  # 伊拉克
    'Israel': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/IL_cidr.txt',  # 以色列
    'Jordan': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/JO_cidr.txt',  # 约旦
    'Kuwait': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/KW_cidr.txt',  # 科威特
    'Qatar': 'https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/main/Clash/QA_cidr.txt'  # 卡塔尔
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
    
    # 合并并排序 IPv4 和 IPv6 的 CIDR 结果
    all_cidrs = sorted(set(ipv4_common_cidrs + ipv6_common_cidrs), key=lambda x: (x.version, x))

    # 保存结果到对应文件
    output_filename = f"CF-Country/Cloudflare-{region_name}.txt"
    save_cidrs_to_file(output_filename, ipv4_common_cidrs, ipv6_common_cidrs)

print("重叠计算完成，CIDR 文件已生成。")
