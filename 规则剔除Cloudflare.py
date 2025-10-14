import requests

# URLs
global_list_url = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Global/Global.list"
cloudflare_domains_url = "https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/refs/heads/main/cloudflare_domains.list"
gfw_list_url = "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/refs/heads/meta/geo/geosite/classical/gfw.list"

# 输出文件名
output_file = "cloudflare_gfw.list"

def fetch_list(url):
    """获取列表并去掉空行和注释"""
    response = requests.get(url)
    response.raise_for_status()
    return [line.strip() for line in response.text.splitlines() if line.strip() and not line.startswith("#")]

def main():
    print("正在获取列表...")
    global_list = fetch_list(global_list_url)
    cloudflare_list = fetch_list(cloudflare_domains_url)
    gfw_list = fetch_list(gfw_list_url)

    # 计算需要剔除的域名：Cloudflare 的域名减去 GFW 的域名
    remove_set = set(cloudflare_list) - set(gfw_list)

    print(f"将从 Global.list 中剔除 {len(remove_set)} 条域名...")

    # 过滤 Global.list
    filtered_list = [line for line in global_list if line not in remove_set]

    # 保存结果
    with open(output_file, "w") as f:
        f.write("\n".join(filtered_list))

    print(f"过滤完成，总计 {len(filtered_list)} 条记录保存到 {output_file}")

if __name__ == "__main__":
    main()
