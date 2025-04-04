#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import logging
from datetime import datetime
import json
import re
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import hashlib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# GitHub Token（从环境变量获取）
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# 配置重试策略
retry_strategy = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("https://", adapter)
session.mount("http://", adapter)

# 如果有GitHub Token，添加到请求头
if GITHUB_TOKEN:
    session.headers.update({'Authorization': f'token {GITHUB_TOKEN}'})

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
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"
        
        for attempt in range(3):  # 最多重试3次
            try:
                response = session.get(url, headers=headers)
                response.raise_for_status()
                
                # 如果遇到API限制，等待一段时间
                if response.headers.get('X-RateLimit-Remaining') == '0':
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                    wait_time = reset_time - int(time.time()) + 1
                    if wait_time > 0:
                        logging.warning(f"API速率限制，等待 {wait_time} 秒...")
                        time.sleep(wait_time)
                        continue
                
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == 2:  # 最后一次尝试
                    raise
                time.sleep(2 ** attempt)  # 指数退避
        return []
    except Exception as e:
        logging.error(f"获取目录内容失败 {path}: {str(e)}")
        return []

def download_file(url, local_path):
    """下载文件并保存到本地"""
    try:
        for attempt in range(3):  # 最多重试3次
            try:
                headers = {}
                if GITHUB_TOKEN:
                    headers["Authorization"] = f"token {GITHUB_TOKEN}"
                
                response = session.get(url, headers=headers)
                response.raise_for_status()
                
                # 如果遇到API限制，等待一段时间
                if response.headers.get('X-RateLimit-Remaining') == '0':
                    reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                    wait_time = reset_time - int(time.time()) + 1
                    if wait_time > 0:
                        logging.warning(f"API速率限制，等待 {wait_time} 秒...")
                        time.sleep(wait_time)
                        continue
                
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                return True
            except requests.exceptions.RequestException as e:
                if attempt == 2:  # 最后一次尝试
                    raise
                time.sleep(2 ** attempt)  # 指数退避
    except Exception as e:
        logging.error(f"下载文件失败 {url}: {str(e)}")
        return False

def download_directory(platform, rule):
    """下载整个规则目录"""
    path = f"{platform}/{rule}"
    contents = get_directory_contents(path)
    
    if not contents:
        return False
    
    success = True
    for item in contents:
        if item['type'] == 'file':
            download_url = item['download_url']
            local_path = os.path.join(LOCAL_RULES_DIR, platform, rule, item['name'])
            if download_file(download_url, local_path):
                logging.info(f"成功下载文件: {item['name']}")
            else:
                success = False
        elif item['type'] == 'dir':
            sub_path = os.path.join(platform, rule, item['name'])
            if not download_directory(platform, sub_path):
                success = False
    
    return success

def create_readme(platform, rule_name, description):
    """创建README文件"""
    content = f"""# {rule_name}

## 前言

本项目的{rule_name}规则由《规则生成器》自动整合与去重。

定时更新时间：每天4:00和16:00。

## 规则说明

{description}

## 规则统计

总计规则数：根据实际规则数量自动更新

### {platform}

规则文件：{rule_name}.list

更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    output_path = os.path.join(LOCAL_RULES_DIR, platform, rule_name, "README.md")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

def get_file_hash(file_path):
    """获取文件的MD5哈希值"""
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def should_update_ai_rules(platform):
    """检查AI规则是否需要更新"""
    has_updates = False
    
    for rule in AI_RULES:
        rule_path = f"{platform}/{rule}"
        contents = get_directory_contents(rule_path)
        
        if contents:
            for item in contents:
                if item['type'] == 'file' and item['name'].endswith('.list'):
                    try:
                        headers = {}
                        if GITHUB_TOKEN:
                            headers["Authorization"] = f"token {GITHUB_TOKEN}"
                        response = session.get(item['download_url'], headers=headers)
                        if response.status_code == 200:
                            # 如果任何一个源文件有更新，就需要更新合并文件
                            has_updates = True
                            break
                    except Exception as e:
                        logging.error(f"检查AI规则更新失败 {item['name']}: {str(e)}")
                        continue
        
        if has_updates:
            break
    
    return has_updates

def merge_ai_rules(platform):
    """合并AI相关规则"""
    output_dir = os.path.join(LOCAL_RULES_DIR, platform, "AiService")
    output_path = os.path.join(output_dir, "AiService.list")
    
    # 如果目录不存在，创建目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 检查是否需要更新
    if not should_update_ai_rules(platform):
        logging.info(f"{platform} AI规则无更新，跳过合并")
        return
    
    merged_content = f"# AI Services Rules - Updated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    for rule in AI_RULES:
        rule_path = f"{platform}/{rule}"
        contents = get_directory_contents(rule_path)
        
        if contents:
            merged_content += f"\n# {rule}\n"
            for item in contents:
                if item['type'] == 'file' and item['name'].endswith('.list'):
                    try:
                        headers = {}
                        if GITHUB_TOKEN:
                            headers["Authorization"] = f"token {GITHUB_TOKEN}"
                        response = session.get(item['download_url'], headers=headers)
                        if response.status_code == 200:
                            merged_content += f"# Source: {item['name']}\n"
                            merged_content += response.text + "\n"
                    except Exception as e:
                        logging.error(f"下载AI规则失败 {item['name']}: {str(e)}")
    
    # 保存合并后的规则文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(merged_content)
    
    # 只在首次创建时添加README文件
    readme_path = os.path.join(output_dir, "README.md")
    if not os.path.exists(readme_path):
        create_readme(platform, "AiService", "整合了各大AI服务的分流规则，包括但不限于：OpenAI（ChatGPT）、Claude、Google Gemini等。")

def create_extra_myself_direct(platform):
    """创建自定义直连规则"""
    output_dir = os.path.join(LOCAL_RULES_DIR, platform, "Extra_myself_direct")
    output_path = os.path.join(output_dir, "Extra_myself_direct.list")
    
    # 如果文件已存在，直接返回
    if os.path.exists(output_path):
        logging.info(f"{platform} Extra_myself_direct规则已存在，跳过创建")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
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

    # 保存规则文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 只在首次创建时添加README文件
    readme_path = os.path.join(output_dir, "README.md")
    if not os.path.exists(readme_path):
        create_readme(platform, "Extra_myself_direct", "个人自定义的直连规则，包含常用的应用和服务。")

def cleanup_root_lists(platform):
    """清理根目录下的.list文件"""
    platform_dir = os.path.join(LOCAL_RULES_DIR, platform)
    if os.path.exists(platform_dir):
        for file in os.listdir(platform_dir):
            if file.endswith('.list') and os.path.isfile(os.path.join(platform_dir, file)):
                os.remove(os.path.join(platform_dir, file))
                logging.info(f"删除根目录规则文件: {file}")

def main():
    """主函数"""
    if not GITHUB_TOKEN:
        logging.warning("未设置GITHUB_TOKEN，可能会遇到API限制")
    
    for platform in PLATFORMS:
        logging.info(f"开始更新 {platform} 规则...")
        
        # 更新基础规则
        for rule in BASIC_RULES:
            logging.info(f"下载 {rule} 规则目录...")
            if download_directory(platform, rule):
                logging.info(f"成功更新 {rule} 规则目录")
            else:
                logging.warning(f"更新 {rule} 规则目录时发生错误")
        
        # 合并AI规则
        logging.info(f"合并 {platform} AI规则...")
        merge_ai_rules(platform)
        
        # 创建自定义规则
        logging.info(f"创建 {platform} 自定义规则...")
        create_extra_myself_direct(platform)
        
        # 清理根目录下的.list文件
        logging.info(f"清理 {platform} 根目录下的规则文件...")
        cleanup_root_lists(platform)
    
    logging.info("规则更新完成！")

if __name__ == "__main__":
    main() 