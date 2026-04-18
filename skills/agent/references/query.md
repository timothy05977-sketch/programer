# Query Reference

## 单商品趋势查询

触发词：趋势、走势、变化、排名、价格、分析 + ASIN 或商品名

```bash
python scripts/analyze.py --asin <ASIN>
```

解析输出后，用飞书插件「发送消息」发送绿色主题趋势卡片：

```
📊 {title} 趋势分析
ASIN：{asin}  ·  分析时间：{cycle_time}
─────────────────────────
排名：{label}
{summary}
─────────────────────────
近期快照（最新 → 最旧）
| 时间 | 排名 | 价格 |
| ...  | ...  | ...  |
─────────────────────────
数据来源：{data_source}（共 {N} 次快照）
```

快照数 < 2 时：显示「数据不足，仅有 {N} 次快照，建议等待更多数据积累」

## 爆款榜单查询

触发词：爆款、榜单、bestseller、热销、top + 类目名

```bash
python scripts/data_provider.py bestsellers --category <slug> --top 20
```

类目 slug 对照：
- 电子/electronics → `electronics`
- 书籍/books → `books`
- 玩具/toys → `toys`
- 厨房/kitchen → `kitchen`
- 服装/clothing → `clothing`
- 运动/sports → `sports`
- 美妆/beauty → `beauty`
- 家居/home → `home`
- 不指定 → `all`

解析输出后，用飞书插件「发送消息」发送榜单卡片：

```
🏆 Amazon 爆款榜单 · {category} · {时间}
| 排名 | ASIN | 商品名 | 价格 | 评分 |
| #1   | ...  | ...    | ...  | ...  |
...（最多展示 20 条）
─────────────────────────
[添加监控] 按钮（批量，用户可勾选要监控的 ASIN）
```

## 全量商品快速查询

触发词：现在怎样、当前状态、所有商品

```bash
python scripts/analyze.py --all
```

发送简洁的汇总卡片（同汇报卡片格式，但不写入文档和 Bitable）。

## 商品识别

用户可能用商品名而非 ASIN 查询。处理步骤：
1. 先在 SQLite products 表中按 label 字段模糊匹配
2. 找到唯一匹配 → 直接使用对应 ASIN
3. 找到多个匹配 → 列出让用户确认
4. 未找到 → 提示用户提供 ASIN
