---
name: feishu-doc
description: Append monitoring snapshots to a Feishu document and update Bitable for chart data. Use this skill after every analyze-trend cycle (every 20 minutes) to write a new timestamped section to the tracking document and insert new records into the Bitable table (which powers the embedded charts). Uses OpenClaw Feishu plugin tools — no direct API calls needed.
---

# Feishu Doc

每 20 分钟向飞书文档追加一个数据区块，同时向多维表格写入新记录作为图表数据源。

## Step 1 — 追加文档区块

使用飞书插件「更新云文档」工具，在文档末尾追加以下结构：

```
## 📊 {YYYY-MM-DD HH:mm} 监控快照

[全量商品数据表格]
| ASIN | 商品名 | 当前排名 | 排名变化 | 价格 | 趋势 |

[焦点商品摘要段落]
本轮焦点：{title}（{asin}），排名 {delta描述}。{summary}
```

文档 Token 从配置 `feishu_doc_token` 读取。

## Step 2 — 写入多维表格

使用飞书插件「多维表格-创建记录」工具，每个监控商品写入一条记录：

| 字段名 | 类型 | 值 |
|-------|------|---|
| ASIN | 文本 | B0CHWX8DFH |
| 商品名 | 文本 | 蓝牙耳机 |
| 记录时间 | 日期时间 | 2026-04-18 14:20 |
| 当前排名 | 数字 | 18 |
| 排名变化 | 数字 | +24 |
| 当前价格 | 数字 | 24.99 |
| 趋势标签 | 单选 | ⚠ 异动 |

Bitable Token 和 Table ID 从配置 `feishu_bitable_token`、`feishu_bitable_table_id` 读取。

多维表格字段结构规范见 `references/doc-structure.md`。

## 执行顺序

先写文档再写 Bitable，两步均失败时在下一轮汇报卡片中附注「本轮文档写入失败」，不阻塞数据采集。
