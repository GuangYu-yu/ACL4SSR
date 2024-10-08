import requests
from datetime import datetime
import yaml
import os

def download_and_save(url, filename):
    response = requests.get(url)
    if response.status_code == 200:
        # 确保 yaml 文件夹存在
        os.makedirs("yaml", exist_ok=True)
        
        # 在 yaml 文件夹中保存文件
        file_path = os.path.join("yaml", f"{filename}.yaml")
        with open(file_path, "wb") as file:
            file.write(response.content)
        print(f"成功下载并保存: {file_path}")
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
