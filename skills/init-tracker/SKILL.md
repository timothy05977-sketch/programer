---
name: init-tracker
description: Initialize the Amazon Product Tracker agent. Use this skill when the user starts for the first time, when required configuration is missing (Rainforest API key, Feishu doc token, Amazon marketplace), or when the user explicitly requests reconfiguration. Guides the user step-by-step to provide all necessary settings before monitoring can begin.
---

# Init Tracker

引导用户完成首次配置，按顺序收集所有必要参数后写入配置文件，最后验证连通性。

## 配置收集顺序

按以下步骤逐一提问，每步确认后再进入下一步，不要一次性列出所有问题：

### Step 1 — Amazon 市场
询问用户目标市场，给出选项：
- 美国 (US) / 日本 (JP) / 英国 (UK) / 德国 (DE) / 加拿大 (CA)

### Step 2 — Rainforest API Key
- 说明用途：用于可靠获取 Amazon 商品数据
- 提醒：无 Key 时系统自动降级为直接爬取，但稳定性较低
- 接受用户粘贴 Key，或用户选择"跳过（使用降级爬取）"

### Step 3 — 飞书配置
依次收集（每项单独确认）：
1. `feishu_app_id` — 飞书应用 App ID
2. `feishu_app_secret` — 飞书应用 App Secret
3. `feishu_doc_token` — 监控报告写入的目标文档 Token（文档 URL 末段）
4. `feishu_bitable_token` — 多维表格 Token（用于图表数据源，可与文档 Token 相同）
5. `feishu_bitable_table_id` — 多维表格中的数据表 ID

### Step 4 — 初始监控商品
- 询问用户提供至少 1 个 ASIN，或选择先从爆款榜单开始
- 支持批量输入，逗号分隔

### Step 5 — 可选项确认
提示以下默认值，用户可直接回车跳过：
- 告警阈值：排名变动 > 3 位（已固定）
- 汇报间隔：20 分钟（已固定）
- 时区：UTC+8

## 完成后操作

收集完毕后执行 `scripts/init_config.py`，写入配置并验证：
1. Rainforest API 连通性测试（如有 Key）
2. 飞书 API token 获取测试
3. 飞书文档写入权限测试

全部通过后告知用户"配置完成，监控即将启动"。任一失败则提示具体错误并引导修正。
