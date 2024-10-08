import requests
from datetime import datetime
import yaml
import os

def modify_proxy_names(data, source):
    if not isinstance(data, dict):
        return data

    # 修改主proxies列表
    if 'proxies' in data and isinstance(data['proxies'], list):
        proxy_map = {}
        for proxy in data['proxies']:
            if 'name' in proxy:
                old_name = proxy['name']
                new_name = f"{old_name}_{source}"
                proxy['name'] = new_name
                proxy_map[old_name] = new_name

    # 修改proxy-groups中的proxies列表
    if 'proxy-groups' in data and isinstance(data['proxy-groups'], list):
        for group in data['proxy-groups']:
            if 'proxies' in group and isinstance(group['proxies'], list):
                group['proxies'] = [proxy_map.get(p, p) for p in group['proxies']]

    return data

def download_and_save(url, filename):
    response = requests.get(url)
    if response.status_code == 200:
        # 确保 yaml 文件夹存在
        os.makedirs("yaml", exist_ok=True)
        
        try:
            # 解析YAML内容
            data = yaml.safe_load(response.text)
            # 修改代理名称
            modified_data = modify_proxy_names(data, filename)
            
            # 在 yaml 文件夹中保存修改后的文件
            file_path = os.path.join("yaml", f"{filename}.yaml")
            with open(file_path, "w", encoding="utf-8") as file:
                yaml.dump(modified_data, file, allow_unicode=True)
            print(f"成功下载、修改并保存: {file_path}")
        except yaml.YAMLError as e:
            print(f"解析YAML失败: {url}")
            print(f"错误信息: {str(e)}")
    else:
        print(f"下载失败: {url}")

def main():
    today = datetime.now()
    
    urls = [
        f"https://oneclash.githubrowcontent.com/{today.strftime('%Y/%m/%Y%m%d')}.yaml",
        f"https://clashgithub.com/wp-content/uploads/rss/{today.strftime('%Y%m%d')}.yml",
        f"https://wenode.githubrowcontent.com/{today.strftime('%Y/%m/%Y%m%d')}.yaml",
        f"https://freenode.openrunner.net/uploads/{today.strftime('%Y%m%d')}-clash.yaml",
        f"http://mm.mibei77.com/{today.strftime('%Y%m')}/{today.strftime('%m.%d')}Clashidf.yaml"
    ]

    filenames = ["oneclash", "clashgithub", "wenode", "openrunner", "miebei"]

    for url, filename in zip(urls, filenames):
        download_and_save(url, filename)

if __name__ == "__main__":
    main()
