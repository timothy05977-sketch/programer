# Bitable Schema

飞书多维表格作为唯一数据存储，包含两张表。配置键：

| 配置键 | 说明 |
|--------|------|
| `feishu_bitable_token` | 多维表格 app_token |
| `feishu_bitable_table_id_products` | products 表的 table_id |
| `feishu_bitable_table_id_snapshots` | snapshots 表的 table_id |

---

## Table 1 — products（监控商品）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| ASIN | 文本 | 主键标识，10位大写字母数字 |
| 商品名 | 文本 | 商品标题 |
| 状态 | 单选 | `active` / `paused` |
| 添加时间 | 日期时间 | 首次添加的 ISO 8601 时间戳 |
| 备注 | 文本 | 可选用户备注 |

**查询示例（飞书插件）：**
- 读取所有 active 商品：filter `状态 = active`
- 检查 ASIN 是否已存在：filter `ASIN = <asin>`

---

## Table 2 — snapshots（历史快照）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| ASIN | 文本 | 对应商品 ASIN |
| 商品名 | 文本 | 快照时的商品名（可能变化）|
| 记录时间 | 日期时间 | fetched_at ISO 8601 |
| 当前排名 | 数字 | sales_rank（整数）|
| 排名变化 | 数字 | rank_delta，正=排名提升（analyze 计算）|
| 当前价格 | 数字 | price_value（浮点，仅数字）|
| 价格原文 | 文本 | price（如 "$24.99"）|
| 趋势标签 | 单选 | 📈 上升 / 📉 下降 / ➡ 稳定 / ⚠ 异动 / — 数据不足 |
| 数据来源 | 单选 | `rainforest` / `scraper` |

**查询示例（飞书插件）：**
- 读取某 ASIN 最近 20 条（用于 analyze.py stdin）：  
  filter `ASIN = <asin>`，按「记录时间」降序，limit 20

---

## Stdin 数据格式（传给 scripts）

### analyze.py `--all`

```json
{
  "products": [
    {
      "asin": "B0CHWX8DFH",
      "title": "...",
      "history": [
        {
          "sales_rank": 18,
          "price_value": 24.99,
          "price": "$24.99",
          "fetched_at": "2026-04-18T14:20:00",
          "data_source": "rainforest"
        }
      ]
    }
  ]
}
```

history 顺序：**newest → oldest**（Bitable 降序查询直接使用）

### weekly_report.py

```json
{
  "products": [
    {
      "asin": "B0CHWX8DFH",
      "title": "...",
      "snapshots": [
        {
          "sales_rank": 18,
          "price_value": 24.99,
          "fetched_at": "2026-04-18T14:20:00"
        }
      ]
    }
  ]
}
```

snapshots 顺序任意，脚本自动按 fetched_at 排序。

---

## 初始化建表

首次 setup 时，使用飞书插件「多维表格-创建数据表」工具按上方字段创建两张表，
将返回的 table_id 分别存入 `feishu_bitable_table_id_products` 和
`feishu_bitable_table_id_snapshots` 配置项。
