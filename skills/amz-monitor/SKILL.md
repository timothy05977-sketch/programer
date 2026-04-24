---
name: amz-monitor
description: 亚马逊商品监控 Agent 的自动采集 Skill。每 20 分钟触发一次，执行：采集商品快照 → 分析趋势告警 → 推送飞书卡片 → 追加文档 → 写入 Bitable。
---

# Monitor

执行固定的 20 分钟监控链条，全程自动，无需用户干预。

## 前置检查

启动前确认配置完整：
- `amazon_marketplace` 已设置
- `feishu_doc_token` 已设置
- Bitable 监控商品表不为空（`feishu_bitable_token` + `feishu_bitable_table_id` 已配置）

任一缺失 → 停止本轮，通过飞书插件发送提示消息，触发 amz-agent 完成配置。

## Step 1 — 读取监控商品列表

使用飞书插件「多维表格-查询记录」工具，从 **products 表**（`feishu_bitable_table_id_products`）读取所有状态为 active 的商品，获取 ASIN 列表和商品名称。

## Step 2 — 数据采集

```bash
python scripts/data_provider.py fetch --asin <ASIN1> [--asin <ASIN2> ...]
```

- 优先 Rainforest API；失败时自动降级直接爬取
- **只输出 JSON，不写 DB**
- 输出：`{"results":[{"asin","status","source","snapshot":{...}}], "summary":{total,ok,failed[],scraper_fallback[]}}`

## Step 3 — 读取历史快照

对 Step 2 中采集成功的每个 ASIN，使用飞书插件「多维表格-查询记录」工具，从 **snapshots 表**（`feishu_bitable_table_id_snapshots`）按时间倒序读取最近 20 条记录，构造 stdin JSON：

```json
{
  "products": [
    {
      "asin": "B0CHWX8DFH",
      "title": "...",
      "history": [
        {"sales_rank": 18, "price_value": 24.99, "price": "$24.99",
         "fetched_at": "2026-04-18T14:20:00", "data_source": "rainforest"},
        ...
      ]
    }
  ]
}
```

history 顺序：newest → oldest

## Step 4 — 趋势分析

```bash
echo '<stdin json>' | python scripts/analyze.py --all
```

输出 JSON：`{ cycle_time, focus, products[], alerts[] }`

## Step 5 — 飞书汇报卡片

使用 OpenClaw 飞书插件「发送消息」工具，发送蓝色主题汇报卡片：

```
🔍 Amazon 监控报告 · {YYYY-MM-DD HH:mm}
─────────────────────────
⚡ 焦点商品
{focus.title}（{focus.asin}）
排名  #{focus.rank_prev} → #{focus.rank_curr}  {▲/▼}{delta}位
价格  {focus.price_prev} → {focus.price_curr}
{focus.summary}
─────────────────────────
| 商品 | 排名 | 变化 | 价格 | 趋势 |
| ... | ...  | ...  | ... | ...  |
─────────────────────────
[查看文档] [管理商品]
```

- `[查看文档]` → URL 跳转：`https://xxx.feishu.cn/docx/{feishu_doc_token}`
- `[管理商品]` → callback action: `manage_products`

若 Step 2 有降级：卡片底部追加灰色小字「⚠ 数据来源包含直接爬取，仅供参考」

## Step 6 — 告警卡片（条件触发）

对 `alerts[]` 中每个商品**单独**发送红色主题告警卡片：

```
⚠️ 排名异动告警 · {HH:mm}
{title}（{asin}）
排名  #{rank_prev} → #{rank_curr}  {▲/▼}{delta}位（超阈值 {threshold} 位）
{summary}
[查看趋势]
```

同一商品同方向连续 2 次告警：末尾追加「⚠ 持续变化中」

## Step 7 — 追加飞书文档

使用 OpenClaw 飞书插件「更新云文档」工具，在文档末尾追加：

```
## 📊 {YYYY-MM-DD HH:mm} 监控快照
[全量商品数据表格]
本轮焦点：{focus.title}，排名 {delta 描述}。{summary}
```

## Step 8 — 写入 Bitable 快照表

使用飞书插件「多维表格-创建记录」工具，每个采集成功的商品写入一条记录到 **snapshots 表**：

| 字段 | 值 |
|------|----|
| ASIN | 商品 ASIN |
| 商品名 | title（截断 50 字）|
| 记录时间 | ISO 8601 字符串（fetched_at）|
| 当前排名 | sales_rank（整数）|
| 排名变化 | rank_delta（正=提升，来自 analyze 输出）|
| 当前价格 | price_value（浮点）|
| 趋势标签 | label（📈/📉/➡/⚠/—）|
| 数据来源 | rainforest / scraper |

## 错误处理

| 情况 | 处理 |
|------|------|
| 单个 ASIN 采集失败 | 跳过，汇报卡片标注「获取失败」|
| 全部 ASIN 失败 | 本轮跳过，发告警消息 |
| 飞书文档写入失败 | 记录日志，不阻塞下一轮 |
| 连续 3 轮有失败 | 发飞书通知提示用户检查配置 |
