---
name: analyze-trend
description: Analyze price and rank trends for monitored Amazon products. Use this skill after every data fetch cycle, or when the user asks about a product's trend ("趋势/走势/变化/分析"). Computes rank changes, assigns trend labels, identifies the focus product (largest rank change), and generates natural-language summaries. Does NOT call any external API — operates purely on local SQLite data.
---

# Analyze Trend

对 SQLite 历史快照进行趋势分析，输出结构化结果供飞书通知和文档写入使用。

## 执行方式

```bash
# 分析所有监控商品（每轮标准调用）
python scripts/analyze.py --all

# 分析单个商品
python scripts/analyze.py --asin B0CHWX8DFH
```

输出 JSON 到 stdout，格式见下方。

## 输出结构

```json
{
  "cycle_time": "2026-04-18T14:20:00",
  "focus": {
    "asin": "B0CHWX8DFH",
    "title": "蓝牙耳机 XXX",
    "rank_prev": 42,
    "rank_curr": 18,
    "rank_delta": 24,
    "price_prev": "$29.99",
    "price_curr": "$24.99",
    "price_delta_pct": -16.7,
    "label": "⚠ 异动",
    "summary": "排名从 #42 升至 #18，▲24 位。单次大幅跳升，建议持续关注。"
  },
  "products": [
    {
      "asin": "...",
      "title": "...",
      "rank_curr": 18,
      "rank_delta": 24,
      "price_curr": "$24.99",
      "label": "⚠ 异动",
      "alert": true
    }
  ]
}
```

`alert: true` 表示该商品本轮排名变动超过阈值（默认 3 位），需触发告警卡片。

## 趋势判断规则

详见 `references/trend-rules.md`。
