import requests
from bs4 import BeautifulSoup
import os
import re
import ipaddress
from typing import List, Tuple

class CloudflareCIDRCollector:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.clash_dir = "Clash"
        os.makedirs(self.clash_dir, exist_ok=True)

    def get_asns(self) -> List[str]:
        """获取Cloudflare的ASN列表"""
        search_url = "https://bgp.he.net/search?search%5Bsearch%5D=cloudflare&commit=Search"
        response = requests.get(search_url, headers=self.headers)
        soup = BeautifulSoup(response.content, "html.parser")
        
        asns = []
        for row in soup.find_all('tr'):
            asn_link = row.find('a')
            if asn_link and 'AS' in asn_link.text:
                asns.append(asn_link.text)
        return asns

    def get_cidrs_from_asn(self, asn: str) -> List[str]:
        """从指定ASN获取CIDR列表"""
        url = f"https://bgp.he.net/{asn}#_prefixes"
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.content, "html.parser")
            cidrs = []
            for row in soup.find_all('tr'):
                cidr = row.find('a')
                if cidr and '/net/' in cidr['href']:
                    cidr_text = cidr.text
                    if re.match(r'^\d{1,3}(\.\d{1,3}){3}(\/\d{1,2})?$|^[0-9a-fA-F:]+(\/\d{1,3})?$', cidr_text):
                        cidrs.append(cidr_text)
            return cidrs
        except Exception as e:
            print(f"获取ASN {asn} 的CIDR失败: {e}")
            return []

    def filter_overlapping_cidrs(self, cidrs: List[str]) -> List[str]:
        """过滤重叠的CIDR，保留最小范围的CIDR"""
        networks = []
        for cidr in cidrs:
            try:
                networks.append(ipaddress.ip_network(cidr))
            except Exception:
                continue

        networks.sort(key=lambda x: (-x.prefixlen, str(x.network_address)))
        
        filtered_networks = []
        for network in networks:
            is_subset = any(
                network.subnet_of(existing_net)
                for existing_net in filtered_networks
            )
            contains_existing = any(
                existing_net.subnet_of(network)
                for existing_net in filtered_networks
            )
            
            if not is_subset and not contains_existing:
                filtered_networks.append(network)

        return [str(net) for net in sorted(filtered_networks)]

    def separate_and_sort_cidrs(self, cidrs: List[str]) -> Tuple[List[str], List[str]]:
        """分离并排序IPv4和IPv6地址，同时过滤重叠的CIDR"""
        ipv4_cidrs = []
        ipv6_cidrs = []
        
        for cidr in cidrs:
            try:
                network = ipaddress.ip_network(cidr)
                if isinstance(network, ipaddress.IPv4Network):
                    ipv4_cidrs.append(cidr)
                else:
                    ipv6_cidrs.append(cidr)
            except Exception:
                continue

        ipv4_cidrs = self.filter_overlapping_cidrs(ipv4_cidrs)
        ipv6_cidrs = self.filter_overlapping_cidrs(ipv6_cidrs)

        return ipv4_cidrs, ipv6_cidrs

    def save_cidrs(self, ipv4_cidrs: List[str], ipv6_cidrs: List[str]):
        """保存CIDR到Clash文件夹"""
        # 保存IPv4
        with open(os.path.join(self.clash_dir, "CloudflareCIDR.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(ipv4_cidrs) + "\n")
        
        # 保存IPv6
        with open(os.path.join(self.clash_dir, "CloudflareCIDR-v6.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(ipv6_cidrs) + "\n")
            
        # 保存合并的文件
        with open(os.path.join(self.clash_dir, "Cloudflare.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(ipv4_cidrs + ipv6_cidrs) + "\n")

    def run(self):
        print("开始获取Cloudflare CIDR列表...")
        
        asns = self.get_asns()
        print(f"找到 {len(asns)} 个Cloudflare ASN")

        all_cidrs = []
        for asn in asns:
            print(f"正在获取 {asn} 的CIDR...")
            cidrs = self.get_cidrs_from_asn(asn)
            all_cidrs.extend(cidrs)
            print(f"从 {asn} 获取到 {len(cidrs)} 个CIDR")

        ipv4_cidrs, ipv6_cidrs = self.separate_and_sort_cidrs(all_cidrs)
        print(f"总共获取到 {len(ipv4_cidrs)} 个IPv4 CIDR和 {len(ipv6_cidrs)} 个IPv6 CIDR")

        self.save_cidrs(ipv4_cidrs, ipv6_cidrs)
        print("CIDR列表已保存到Clash文件夹")

if __name__ == "__main__":
    collector = CloudflareCIDRCollector()
    collector.run()
