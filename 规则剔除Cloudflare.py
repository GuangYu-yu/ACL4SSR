import requests

# URLs
global_list_url = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Global/Global.list"
cloudflare_domains_url = "https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/refs/heads/main/cloudflare_domains.list"
gfw_list_url = "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/refs/heads/meta/geo/geosite/classical/gfw.list"

# 输出文件名
output_file = "cloudflare_gfw.list"

# 获取列表
def fetch_list(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text.splitlines()

# 过滤列表
def filter_lists(global_list, cloudflare_domains_list, gfw_list):
    cloudflare_set = set(line for line in cloudflare_domains_list if not line.startswith("#"))
    gfw_set = set(line for line in gfw_list if not line.startswith("#"))
    
    filtered_list = []
    for line in global_list:
        if line.startswith("#"):
            continue
        # 如果域名在 cloudflare_domains_list 中，且不在 gfw_list 中，则排除
        if line in cloudflare_set and line not in gfw_set:
            continue
        filtered_list.append(line)
    return filtered_list

def main():
    print("正在获取列表...")
    global_list = fetch_list(global_list_url)
    cloudflare_domains_list = fetch_list(cloudflare_domains_url)
    gfw_list = fetch_list(gfw_list_url)

    print("正在过滤列表...")
    filtered_list = filter_lists(global_list, cloudflare_domains_list, gfw_list)

    # 保存结果
    with open(output_file, "w") as f:
        for line in filtered_list:
            f.write(line + "\n")

    print(f"过滤完成，总计 {len(filtered_list)} 条记录保存到 {output_file}")

if __name__ == "__main__":
    main()
