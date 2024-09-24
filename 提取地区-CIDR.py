import os
import shutil
import zipfile
import requests
import ipaddress

# 下载 zip 文件
url = "https://github.com/ipverse/rir-ip/archive/refs/heads/master.zip"
r = requests.get(url)
with open("rir_ip.zip", "wb") as code:
    code.write(r.content)

# 解压 zip 文件
with zipfile.ZipFile("rir_ip.zip", 'r') as zip_ref:
    zip_ref.extractall(".")

# 定义要查找的地区及其名称
regions = {
    'HK': 'Hong Kong',
    'TW': 'Taiwan',
    'JP': 'Japan',
    'KR': 'South Korea',
    'IN': 'India',
    'SG': 'Singapore',
    'TH': 'Thailand',
    'VN': 'Vietnam',
    'PH': 'Philippines',
    'MY': 'Malaysia',
    'FR': 'France',
    'DE': 'Germany',
    'GB': 'United Kingdom',
    'IT': 'Italy',
    'ES': 'Spain',
    'RU': 'Russia',
    'SE': 'Sweden',
    'CH': 'Switzerland',
    'PL': 'Poland',
    'US': 'United States',
    'CA': 'Canada',
    'MX': 'Mexico',
    'CU': 'Cuba',
    'GT': 'Guatemala',
    'DO': 'Dominican Republic',
    'CR': 'Costa Rica',
    'PA': 'Panama',
    'HN': 'Honduras',
    'JM': 'Jamaica',
    'BR': 'Brazil',
    'AR': 'Argentina',
    'CL': 'Chile',
    'CO': 'Colombia',
    'PE': 'Peru',
    'VE': 'Venezuela',
    'UY': 'Uruguay',
    'PY': 'Paraguay',
    'BO': 'Bolivia',
    'EC': 'Ecuador',
    'ZA': 'South Africa',
    'NG': 'Nigeria',
    'EG': 'Egypt',
    'KE': 'Kenya',
    'DZ': 'Algeria',
    'MA': 'Morocco',
    'GH': 'Ghana',
    'ET': 'Ethiopia',
    'TZ': 'Tanzania',
    'SN': 'Senegal',
    'AU': 'Australia',
    'NZ': 'New Zealand',
    'FJ': 'Fiji',
    'PG': 'Papua New Guinea',
    'SB': 'Solomon Islands',
    'VU': 'Vanuatu',
    'TO': 'Tonga',
    'WF': 'Wallis and Futuna',
    'NR': 'Nauru',
    'TV': 'Tuvalu',
    'SA': 'Saudi Arabia',
    'AE': 'United Arab Emirates',
    'IR': 'Iran',
    'IQ': 'Iraq',
    'IL': 'Israel',
    'JO': 'Jordan',
    'KW': 'Kuwait',
    'QA': 'Qatar'
}

# 文件名映射，保存 CIDR 列表到指定文件
region_files = {region: f'Clash/{region}_cidr.txt' for region in regions.keys()}

# 初始化结果字典，用于保存各地区的 IPv4 和 IPv6 CIDR 列表
result = {region: {'ipv4': [], 'ipv6': []} for region in regions.keys()}

# 遍历解压后的文件夹
for region_code in regions.keys():
    for version in ['ipv4', 'ipv6']:
        file_path = f'rir-ip-master/country/{region_code}/{version}-aggregated.txt'
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                for line in file:
                    if not line.startswith('#'):
                        cidr_str = line.strip()
                        if version == 'ipv4':
                            result[region_code]['ipv4'].append(cidr_str)
                        else:
                            result[region_code]['ipv6'].append(cidr_str)

# 将结果保存到对应文件中
for region_code, data in result.items():
    if data['ipv4'] or data['ipv6']:
        with open(region_files[region_code], 'w') as f:
            if data['ipv4']:
                f.write('\n'.join(data['ipv4']) + '\n')
            if data['ipv6']:
                f.write('\n'.join(data['ipv6']) + '\n')
