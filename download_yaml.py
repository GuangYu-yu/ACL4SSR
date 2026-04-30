import requests
from datetime import datetime
import yaml
import os
import re
from bs4 import BeautifulSoup
import tempfile

def get_mibei_url():
    today = datetime.now()
    base_url = "https://www.mibei77.com"
    
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    target_date = today.strftime("%Y年%m月%d日")
    for article in soup.find_all('article', class_='blog-post'):
        title = article.find('h2', class_='entry-title').text
        if target_date in title:
            return article.find('a')['href']
    
    return None

def get_clash_url(article_url):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        response = requests.get(article_url)
        temp_file.write(response.text)
        temp_file.seek(0)
        
        soup = BeautifulSoup(temp_file, 'html.parser')
        
        for p in soup.find_all('p'):
            if 'clash订阅链接' in p.text.lower():
                clash_url = p.find_next('p').text.strip()
                os.unlink(temp_file.name)
                return clash_url
    
    os.unlink(temp_file.name)
    return None

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
        os.makedirs("yaml", exist_ok=True)
        file_path = os.path.join("yaml", f"{filename}.yaml")
        try:
            data = yaml.safe_load(response.text)
            modified_data = modify_proxy_names(data, filename)
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
    ]

    filenames = ["oneclash", "clashgithub", "wenode", "openrunner"]

    # 获取米贝的URL
    mibei_article_url = get_mibei_url()
    if mibei_article_url:
        mibei_clash_url = get_clash_url(mibei_article_url)
        if mibei_clash_url:
            urls.append(mibei_clash_url)
            filenames.append("miebei")
        else:
            print("未找到米贝的Clash订阅链接")
    else:
        print("未找到今天的米贝文章")

    for url, filename in zip(urls, filenames):
        download_and_save(url, filename)

if __name__ == "__main__":
    main()
