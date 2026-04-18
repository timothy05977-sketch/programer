---
name: init-tracker
description: Initialize the Amazon Product Tracker agent. Use this skill when the user starts for the first time, when required configuration is missing (Rainforest API key, Feishu doc token, Amazon marketplace), or when the user explicitly requests reconfiguration. Guides the user step-by-step to collect all settings before monitoring begins. Do NOT ask for Feishu App ID or App Secret — those are managed by the OpenClaw Feishu plugin separately.
---

# Init Tracker

引导用户完成首次配置，逐步收集参数，写入配置文件，最后验证连通性。每次只问一个问题，等待用户回答后再继续。

## 配置收集顺序

### Step 1 — Amazon 市场
询问监控的目标市场，给出选项：
- 美国 US / 日本 JP / 英国 UK / 德国 DE / 加拿大 CA

### Step 2 — Rainforest API Key
- 说明：用于可靠获取 Amazon 商品数据，无此 Key 时自动降级为直接爬取（稳定性较低）
- 接受用户粘贴 Key，或选择「跳过，使用爬取降级」

### Step 3 — 飞书文档 Token
- 说明：监控报告每 20 分钟追加写入的目标文档，从飞书文档 URL 末段获取
- 示例：URL 为 `https://xxx.feishu.cn/docx/AbCdEfGh`，Token 即 `AbCdEfGh`

### Step 4 — 飞书多维表格
依次收集：
1. `feishu_bitable_token` — 多维表格应用 Token（用于趋势图表数据源）
2. `feishu_bitable_table_id` — 数据表 ID

### Step 5 — 初始监控商品
询问用户提供至少 1 个 ASIN（10位大写字母数字），逗号分隔可批量输入。
或选择「先跳过，稍后添加」。

### Step 6 — 可选确认
告知以下已固定默认值，无需用户输入：
- 告警阈值：排名变动 > 3 位
- 汇报间隔：20 分钟
- 时区：UTC+8

## 完成后操作

执行 `scripts/init_config.py --save`，将所有参数写入 `.tracker_config.json`。

验证步骤：
1. 若有 Rainforest Key → 执行 `scripts/init_config.py --test-rainforest`
2. 飞书文档 Token → 提示用户通过飞书插件的「更新云文档」工具写入一行测试文字验证权限
3. 全部通过 → 告知用户「配置完成，监控将在下一个 20 分钟节点启动」
4. 任一失败 → 说明原因，引导用户重新填写对应项
