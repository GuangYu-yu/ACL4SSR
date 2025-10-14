import requests

# URLs
global_list_url = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Global/Global.list"
cloudflare_domains_url = "https://raw.githubusercontent.com/GuangYu-yu/ACL4SSR/refs/heads/main/cloudflare_domains.list"
gfw_list_url = "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/refs/heads/meta/geo/geosite/classical/gfw.list"

# 输出文件名
output_file = "global_cf_filtered.list"

def fetch_list(url):
    """获取列表并去掉空行和注释"""
    response = requests.get(url)
    response.raise_for_status()
    return [line.strip() for line in response.text.splitlines() if line.strip() and not line.startswith("#")]

def main():
    # 获取列表
    cloudflare_domains = fetch_list(cloudflare_domains_url)
    gfw_list = fetch_list(gfw_list_url)
    global_list = fetch_list(global_list_url)

    # 从 cloudflare_domains 中剔除 gfw_list 条目
    filtered_cloudflare = [domain for domain in cloudflare_domains if domain not in gfw_list]

    # 从 Global.list 中剔除 filtered_cloudflare 条目
    final_list = [item for item in global_list if item not in filtered_cloudflare]

    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        for line in final_list:
            f.write(line + "\n")

    print(f"完成，生成文件: {output_file}")

if __name__ == "__main__":
    main()
