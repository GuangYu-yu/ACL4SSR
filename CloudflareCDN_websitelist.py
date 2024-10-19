import requests
import re
import os
import argparse
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

# 定义URL列表
urls = [
    "https://trends.builtwith.com/zh/websitelist/Cloudflare-CDN/Hong-Kong",
    "https://trends.builtwith.com/zh/websitelist/Cloudflare-CDN/United-States",
    "https://trends.builtwith.com/zh/websitelist/Cloudflare-CDN/United-Kingdom",
    "https://trends.builtwith.com/zh/websitelist/Cloudflare-CDN/Russia",
    "https://trends.builtwith.com/zh/websitelist/Cloudflare-CDN/India",
    "https://trends.builtwith.com/zh/websitelist/Cloudflare-CDN/Germany",
    "https://trends.builtwith.com/zh/websitelist/Cloudflare-CDN/Australia",
    "https://trends.builtwith.com/zh/cdns/Cloudflare-CDN/Brazil",
    "https://trends.builtwith.com/zh/cdns/Cloudflare-CDN/France",
    "https://trends.builtwith.com/zh/cdns/Cloudflare-CDN/Canada",
    "https://trends.builtwith.com/zh/cdns/Cloudflare-CDN/Netherlands",
    "https://trends.builtwith.com/zh/cdns/Cloudflare-CDN/China",
    "https://trends.builtwith.com/zh/cdns/Cloudflare-CDN/Japan",
    "https://trends.builtwith.com/zh/websitelist/Cloudflare-CDN/EU",
    "https://trends.builtwith.com/zh/websitelist/Cloudflare-CDN/High-Traffic-Volume"
]

def fetch_and_cache(url, force_refresh=False):
    """获取并缓存网页内容"""
    filename = f"cache_{urlparse(url).path.split('/')[-1]}.html"
    if os.path.exists(filename) and not force_refresh:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        response = requests.get(url)
        content = response.text
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return content

def extract_domains(content):
    """从网页内容中提取域名"""
    pattern = r'data-domain="([^"]+)"'
    return re.findall(pattern, content)

def process_url(url, force_refresh):
    """处理单个URL"""
    content = fetch_and_cache(url, force_refresh)
    return extract_domains(content)

def clear_cache():
    """删除所有缓存文件"""
    cache_files = [f for f in os.listdir() if f.startswith("cache_") and f.endswith(".html")]
    for file in cache_files:
        os.remove(file)
    print(f"已删除 {len(cache_files)} 个缓存文件")

def main():
    parser = argparse.ArgumentParser(description="提取使用Cloudflare CDN的网站列表")
    parser.add_argument("--clear-cache", action="store_true", help="删除所有缓存文件并重新获取数据")
    args = parser.parse_args()

    if args.clear_cache:
        clear_cache()

    all_domains = set()

    # 使用线程池并发处理URL
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(lambda url: process_url(url, args.clear_cache), urls)
        for domains in results:
            all_domains.update(domains)

    # 排序域名
    sorted_domains = sorted(all_domains)

    # 保存到文件
    with open('CloudflareCDN_websitelist.txt', 'w', encoding='utf-8') as f:
        for domain in sorted_domains:
            f.write(f"{domain}\n")

    print(f"已提取并保存 {len(sorted_domains)} 个唯一域名到 CloudflareCDN_websitelist.txt")

if __name__ == "__main__":
    main()
