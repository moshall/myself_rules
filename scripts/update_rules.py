#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import logging
from datetime import datetime
import json
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 基础配置
BASE_URL = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule"
API_BASE_URL = "https://api.github.com/repos/blackmatrix7/ios_rule_script/contents/rule"
PLATFORMS = ["QuantumultX", "Shadowrocket", "Clash"]
LOCAL_RULES_DIR = "rules"

# 规则配置
BASIC_RULES = [
    "Lan", "China", "ChinaMax", "Apple", "IPTVMainland",
    "Google", "Netflix", "YouTube", "Spotify", "Instagram",
    "Telegram", "Notion", "Disney", "TikTok", "GitHub"
]

AI_RULES = ["OpenAI", "Claude", "Gemini"]

def get_directory_contents(path):
    """获取目录下所有文件的列表"""
    try:
        url = f"{API_BASE_URL}/{path}"
        headers = {"Accept": "application/vnd.github.v3+json"}
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.error(f"获取目录内容失败 {path}: {str(e)}")
        return []

def download_file(url, local_path):
    """下载文件并保存到本地"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        return True
    except Exception as e:
        logging.error(f"下载文件失败 {url}: {str(e)}")
        return False

def download_directory(platform, rule):
    """下载整个规则目录"""
    path = f"{platform}/{rule}"
    contents = get_directory_contents(path)
    
    if not contents:
        return False
    
    for item in contents:
        if item['type'] == 'file':
            download_url = item['download_url']
            local_path = os.path.join(LOCAL_RULES_DIR, platform, rule, item['name'])
            if download_file(download_url, local_path):
                logging.info(f"成功下载文件: {item['name']}")
        elif item['type'] == 'dir':
            sub_path = os.path.join(platform, rule, item['name'])
            download_directory(platform, sub_path)
    
    return True

def merge_ai_rules(platform):
    """合并AI相关规则"""
    merged_content = f"# AI Services Rules - Updated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    for rule in AI_RULES:
        rule_path = f"{platform}/{rule}"
        contents = get_directory_contents(rule_path)
        
        if contents:
            merged_content += f"\n# {rule}\n"
            for item in contents:
                if item['type'] == 'file' and item['name'].endswith('.list'):
                    response = requests.get(item['download_url'])
                    if response.status_code == 200:
                        merged_content += f"# Source: {item['name']}\n"
                        merged_content += response.text + "\n"
    
    output_path = f"{LOCAL_RULES_DIR}/{platform}/AiService.list"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(merged_content)

def create_extra_myself_direct(platform):
    """创建自定义直连规则"""
    content = """# Extra Myself Direct Rules
# 多邻国
DOMAIN-SUFFIX,duolingo.cn
DOMAIN-SUFFIX,duolingo.com

# PicoPico
DOMAIN-SUFFIX,picopi.cn
DOMAIN-SUFFIX,xintiaotime.com

# 坚果云
DOMAIN-SUFFIX,gdfgq.club
DOMAIN-SUFFIX,jianguopuzi.com
DOMAIN-SUFFIX,jianguoyun.com
DOMAIN-SUFFIX,nutstore.net
DOMAIN-SUFFIX,nutstorehq.com"""

    output_path = f"{LOCAL_RULES_DIR}/{platform}/Extra_myself_direct.list"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    """主函数"""
    for platform in PLATFORMS:
        logging.info(f"开始更新 {platform} 规则...")
        
        # 更新基础规则
        for rule in BASIC_RULES:
            logging.info(f"下载 {rule} 规则目录...")
            if download_directory(platform, rule):
                logging.info(f"成功更新 {rule} 规则目录")
        
        # 合并AI规则
        logging.info(f"合并 {platform} AI规则...")
        merge_ai_rules(platform)
        
        # 创建自定义规则
        logging.info(f"创建 {platform} 自定义规则...")
        create_extra_myself_direct(platform)
    
    logging.info("规则更新完成！")

if __name__ == "__main__":
    main() 