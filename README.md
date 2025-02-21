# QuantumultX 规则集

这个项目提供了一套适用于 QuantumultX、Shadowrocket 等软件的分流规则集合。

## 功能特点

- 整合了来自 blackmatrix7 的优质规则
- 提供了专门的 AI 服务分流规则（包含 OpenAI、Claude、Gemini 等）
- 包含自定义的直连规则
- 每日自动更新（凌晨4:00和下午16:00）

## 规则列表

1. 基础规则（直接引用）
   - Lan
   - China
   - ChinaMax
   - Apple
   - IPTVMainland
   - Google
   - Netflix
   - YouTube
   - Spotify
   - Instagram
   - Telegram
   - Notion
   - Disney
   - TikTok
   - GitHub

2. 合并规则
   - AiService（整合了 OpenAI、Claude、Gemini 的规则）

3. 自定义规则
   - Extra_myself_direct（自定义直连规则）

## 使用方法

1. 在 QuantumultX 配置文件中引用规则：
```conf
# 示例：引用 AI 服务规则
https://raw.githubusercontent.com/[你的用户名]/[仓库名]/master/rules/QuantumultX/AiService.list
```

## 自动更新

本项目每日会在以下时间点自动检查并更新规则：
- 凌晨 4:00
- 下午 16:00

## 致谢

- [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) 