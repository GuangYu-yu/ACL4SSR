import requests

# URLs
global_list_url = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Global/Global.list"
cloudflare_list_url = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Cloudflare/Cloudflare.list"

# 获取列表
def fetch_list(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text.splitlines()

# 过滤列表
def filter_lists(global_list, cloudflare_list):
    cloudflare_set = set(line for line in cloudflare_list if not line.startswith("#"))
    filtered_list = [line for line in global_list if line not in cloudflare_set and not line.startswith("#")]
    return filtered_list

def main():
    global_list = fetch_list(global_list_url)
    cloudflare_list = fetch_list(cloudflare_list_url)

    filtered_list = filter_lists(global_list, cloudflare_list)

    # 保存结果
    with open("filtered_list.txt", "w") as f:
        for line in filtered_list:
            f.write(line + "\n")

if __name__ == "__main__":
    main()
