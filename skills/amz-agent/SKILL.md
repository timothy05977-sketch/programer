---
name: amz-agent
description: 亚马逊商品监控 Agent 的用户交互 Skill。负责响应 /amz 命令及自然语言消息，处理首次配置、商品增删管理、趋势与排名查询、周报月报生成，以及飞书卡片回调。
---

# Agent

处理所有用户发起的交互。根据意图加载对应参考文档，按其流程执行。

## `/amz` 命令解析

用户可通过 `/amz` 命令唤醒本 agent，按如下规则解析：

| 输入形式 | 处理方式 |
|---------|---------|
| `/amz` | 唤醒 agent，若未初始化则触发配置引导；否则等待用户下一句意图 |
| `/amz -help` | 直接跳到 `references/help.md`，发送帮助卡片 |
| `/amz <任意文字>` | 剥去 `/amz` 前缀，将剩余文字按下方意图路由表处理 |

`/amz` 只是入口唤醒词，剥离后的内容与直接发消息完全等价。

## 意图路由

| 用户意图 | 参考文档 | 涉及脚本 |
|---------|---------|---------|
| `/amz -help` / 帮助 / `/help` / 怎么用 / 使用说明 | `references/help.md` | — |
| 首次配置 / 重新配置 / 缺少必要参数 | `references/setup.md` | `init_config.py` |
| 添加 / 删除 / 查看 / 备注监控商品 | `references/manage.md` | `asin_utils.py` |
| 查询趋势、价格、排名、爆款榜单 | `references/query.md` | `analyze.py` / `data_provider.py` |
| 生成报告 / 周报 / 月报 | `references/report.md` | `weekly_report.py` |
| 飞书卡片回调（manage_products / view_trend）| `references/manage.md` | `asin_utils.py` |
| 飞书卡片回调（show_help）| `references/help.md` | — |
| 飞书卡片回调（reset_config）| `references/setup.md` | `init_config.py` |

识别意图后，读取对应参考文档并按其流程执行。单条消息可能跨多个意图（如"帮我添加商品然后查一下趋势"），依次处理。

## 首次配置完成的特殊路径

`references/setup.md` 流程结束后**必须**立即推送欢迎卡片（见 setup.md 末尾「欢迎卡片」章节），让用户立即了解下一步能做什么。不要等用户再发一句话才给指引。

## 通用回复规范

- 每次操作完成后，用飞书插件「发送消息」回复确认卡片
- 操作失败时，说明具体原因，提供修正建议
- 不确定用户意图时，主动询问，不要猜测后直接执行
