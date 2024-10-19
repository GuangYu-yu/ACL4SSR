import requests
import re
import os
import argparse
from urllib.parse import urlparse
import logging
import time
import socks
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

# SOCKS5代理列表URL
SOCKS5_LIST_URL = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt"

def get_socks5_list():
    try:
        response = requests.get(SOCKS5_LIST_URL)
        response.raise_for_status()
        return [line.strip() for line in response.text.split('\n') if line.strip()]
    except requests.RequestException as e:
        logging.error(f"Error fetching SOCKS5 list: {e}")
        return []

def test_proxy(proxy):
    host, port = proxy.split(':')
    try:
        socks.set_default_proxy(socks.SOCKS5, host, int(port))
        socket.socket = socks.socksocket
        response = requests.get("https://api.ipify.org", timeout=10)
        if response.status_code == 200:
            logging.info(f"Proxy {proxy} is working")
            return proxy
    except:
        pass
    return None

def find_working_proxy(proxy_list):
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in proxy_list}
        for future in as_completed(future_to_proxy):
            result = future.result()
            if result:
                return result
    return None

def fetch_and_cache(url, proxy, force_refresh=False):
    """获取并缓存网页内容"""
    filename = f"cache_{urlparse(url).path.split('/')[-1]}.html"
    if os.path.exists(filename) and not force_refresh:
        with open(filename, 'r', encoding='utf-8') as f:
            logging.info(f"Reading from cache: {filename}")
            return f.read()
    else:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        try:
            logging.info(f"Fetching URL: {url}")
            host, port = proxy.split(':')
            proxies = {
                'http': f'socks5://{host}:{port}',
                'https': f'socks5://{host}:{port}'
            }
            response = requests.get(url, headers=headers, proxies=proxies, allow_redirects=True, timeout=30)
            response.raise_for_status()
            content = response.text
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            logging.info(f"Successfully fetched and cached: {url}")
            return content
        except requests.RequestException as e:
            logging.error(f"Error fetching {url}: {e}")
            return None

def extract_domains(content):
    """从网页内容中提取域名"""
    if content is None:
        return []
    pattern = r'data-domain="([^"]+)"'
    domains = re.findall(pattern, content)
    if not domains:
        logging.warning("No domains found in the content. The page structure might have changed.")
    return domains

def process_url(url, proxy, force_refresh):
    """处理单个URL"""
    content = fetch_and_cache(url, proxy, force_refresh)
    domains = extract_domains(content)
    logging.info(f"Extracted {len(domains)} domains from {url}")
    return domains

def clear_cache():
    """删除所有缓存文件"""
    cache_files = [f for f in os.listdir() if f.startswith("cache_") and f.endswith(".html")]
    for file in cache_files:
        os.remove(file)
    logging.info(f"Deleted {len(cache_files)} cache files")

def main():
    parser = argparse.ArgumentParser(description="提取使用Cloudflare CDN的网站列表")
    parser.add_argument("--clear-cache", action="store_true", help="删除所有缓存文件并重新获取数据")
    args = parser.parse_args()

    if args.clear_cache:
        clear_cache()

    proxy_list = get_socks5_list()
    working_proxy = find_working_proxy(proxy_list)

    if not working_proxy:
        logging.error("No working proxy found. Exiting.")
        return

    logging.info(f"Using proxy: {working_proxy}")

    all_domains = set()

    for url in urls:
        domains = process_url(url, working_proxy, args.clear_cache)
        all_domains.update(domains)
        time.sleep(2)  # 添加延迟以避免过于频繁的请求

    # 排序域名
    sorted_domains = sorted(all_domains)

    # 保存到文件
    with open('CloudflareCDN_websitelist.txt', 'w', encoding='utf-8') as f:
        for domain in sorted_domains:
            f.write(f"{domain}\n")

    logging.info(f"已提取并保存 {len(sorted_domains)} 个唯一域名到 CloudflareCDN_websitelist.txt")

if __name__ == "__main__":
    main()
