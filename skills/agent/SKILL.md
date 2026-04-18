---
name: agent
description: Handle all user-initiated interactions with the Amazon Product Tracker. Use this skill when the user sends any message requesting: configuration or first-time setup (配置/初始化/setup), adding or removing monitored products (添加/删除/查看商品/ASIN), querying trends or prices (趋势/价格/排名/变化/走势/爆款榜单), or generating reports (报告/周报/月报/汇总). Also handles Feishu card callback actions (manage_products, view_trend). Do NOT use for the automated 20-minute monitoring cycle.
---

# Agent

处理所有用户发起的交互。根据意图加载对应参考文档，按其流程执行。

## 意图路由

| 用户意图 | 参考文档 | 涉及脚本 |
|---------|---------|---------|
| 首次配置 / 重新配置 / 缺少必要参数 | `references/setup.md` | `init_config.py` |
| 添加 / 删除 / 查看 / 备注监控商品 | `references/manage.md` | `manage_db.py` |
| 查询趋势、价格、排名、爆款榜单 | `references/query.md` | `analyze.py` / `data_provider.py` |
| 生成报告 / 周报 / 月报 | `references/report.md` | `weekly_report.py` |
| 飞书卡片回调（manage_products / view_trend）| `references/manage.md` | `manage_db.py` |

识别意图后，读取对应参考文档并按其流程执行。单条消息可能跨多个意图（如"帮我添加商品然后查一下趋势"），依次处理。

## 通用回复规范

- 每次操作完成后，用飞书插件「发送消息」回复确认卡片
- 操作失败时，说明具体原因，提供修正建议
- 不确定用户意图时，主动询问，不要猜测后直接执行
