import os
import zipfile
import requests

# 创建保存结果的目录
os.makedirs('Clash', exist_ok=True)

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
    'hk': 'Hong Kong',
    'tw': 'Taiwan',
    'jp': 'Japan',
    'kr': 'South Korea',
    'in': 'India',
    'sg': 'Singapore',
    'th': 'Thailand',
    'vn': 'Vietnam',
    'ph': 'Philippines',
    'my': 'Malaysia',
    'fr': 'France',
    'de': 'Germany',
    'gb': 'United Kingdom',
    'it': 'Italy',
    'es': 'Spain',
    'ru': 'Russia',
    'se': 'Sweden',
    'ch': 'Switzerland',
    'pl': 'Poland',
    'us': 'United States',
    'ca': 'Canada',
    'mx': 'Mexico',
    'cu': 'Cuba',
    'gt': 'Guatemala',
    'do': 'Dominican Republic',
    'cr': 'Costa Rica',
    'pa': 'Panama',
    'hn': 'Honduras',
    'jm': 'Jamaica',
    'br': 'Brazil',
    'ar': 'Argentina',
    'cl': 'Chile',
    'co': 'Colombia',
    'pe': 'Peru',
    've': 'Venezuela',
    'uy': 'Uruguay',
    'py': 'Paraguay',
    'bo': 'Bolivia',
    'ec': 'Ecuador',
    'za': 'South Africa',
    'ng': 'Nigeria',
    'eg': 'Egypt',
    'ke': 'Kenya',
    'dz': 'Algeria',
    'ma': 'Morocco',
    'gh': 'Ghana',
    'et': 'Ethiopia',
    'tz': 'Tanzania',
    'sn': 'Senegal',
    'au': 'Australia',
    'nz': 'New Zealand',
    'fj': 'Fiji',
    'pg': 'Papua New Guinea',
    'sb': 'Solomon Islands',
    'vu': 'Vanuatu',
    'to': 'Tonga',
    'wf': 'Wallis and Futuna',
    'nr': 'Nauru',
    'tv': 'Tuvalu',
    'sa': 'Saudi Arabia',
    'ae': 'United Arab Emirates',
    'ir': 'Iran',
    'iq': 'Iraq',
    'il': 'Israel',
    'jo': 'Jordan',
    'kw': 'Kuwait',
    'qa': 'Qatar'
}

# 初始化结果字典，用于保存各地区的 CIDR 列表
result = {region: [] for region in regions.keys()}

# 遍历解压后的文件夹
for region_code in regions.keys():
    for version in ['ipv4', 'ipv6']:
        file_path = f'rir-ip-master/country/{region_code}/{version}-aggregated.txt'
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                for line in file:
                    if not line.startswith('#'):
                        cidr_str = line.strip()
                        result[region_code].append(cidr_str)

# 将结果保存到对应文件中
for region_code, cidrs in result.items():
    if cidrs:
        with open(f'Clash/{region_code.upper()}_cidr.txt', 'w') as f:
            f.write('\n'.join(cidrs) + '\n')
