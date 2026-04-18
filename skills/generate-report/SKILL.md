---
name: generate-report
description: Generate a periodic summary report for monitored Amazon products. Use this skill when the user explicitly requests a report, weekly summary, or monthly analysis ("生成报告/周报/月报/汇总"). Aggregates SQLite snapshot history, generates trend charts via analyze.py, and writes a structured report section to the Feishu document using the OpenClaw Feishu plugin tools.
---

# Generate Report

从 SQLite 历史数据中聚合指定时间范围的快照，生成结构化周报并写入飞书文档。

## 执行方式

```bash
python scripts/weekly_report.py --days 7   # 周报
python scripts/weekly_report.py --days 30  # 月报
```

输出聚合数据 JSON，供 Agent 调用飞书插件写入文档。

## 报告文档结构

使用飞书插件「更新云文档」在文档顶部（固定位置）写入或覆盖：

```
# 📈 Amazon 监控周报 {起始日} ~ {结束日}

## 总览
- 监控商品数：N 个
- 本周快照次数：M 次
- 焦点商品：{ASIN} · {title}（排名变化最大）

## 各商品趋势

### {商品名}（{ASIN}）
- 排名区间：最高 #{min} · 最低 #{max} · 均值 #{avg}
- 价格区间：最低 {min} · 最高 {max}
- 趋势判断：{trend_summary}

[此处嵌入多维表格图表——由飞书 Bitable 数据驱动]

### {下一个商品...}

## 数据说明
报告基于每 20 分钟一次的快照，共 {count} 条记录。
```

## 趋势判断逻辑

- **持续上升**：最近 5 次快照排名均优于均值
- **持续下降**：最近 5 次快照排名均劣于均值
- **波动**：标准差 > 均值的 20%
- **稳定**：标准差 ≤ 均值的 20%

报告生成完毕后，通过飞书插件「发送消息」工具向群发送一张摘要卡片，附带文档链接。
