---
name: fetch-data
description: Fetch Amazon product snapshots and bestseller lists. Use this skill when the 20-minute monitoring cycle triggers, when the user requests a manual snapshot of a product ("查看/快照/snapshot"), or when a new product is added and needs an initial data fetch. Tries Rainforest API first; automatically falls back to direct scraping if Rainforest is unavailable or unconfigured.
---

# Fetch Data

获取 Amazon 商品数据，标准化后存入 SQLite，供趋势分析使用。

## 执行流程

```
data_provider.py fetch --asin <ASIN> [--asin <ASIN2> ...]
```

`data_provider.py` 内部逻辑：
1. 调用 `rainforest.py` 请求 Rainforest API
2. 若 Rainforest 返回非 200 / 429 / 超时 → 切换 `scraper.py`
3. 若 Rainforest Key 未配置 → 直接走 `scraper.py`
4. 标准化结果为 `Snapshot` dataclass → 写入 SQLite

## 数据降级标记

每条 Snapshot 记录 `data_source` 字段：`"rainforest"` 或 `"scraper"`。
连续 3 次 scraper 降级时，在下一次汇报卡片中附注「数据来源已降级，建议检查 Rainforest Key」。

## 获取爆款榜单

```
data_provider.py bestsellers --category <slug> --top <N>
```

类目 slug 参照 `references/rainforest-api.md`。
结果仅输出到 stdout（JSON），不写入 SQLite。

## 错误处理

| 错误类型 | 处理方式 |
|---------|---------|
| Rainforest 429 | 等待 60s 后降级爬取 |
| 网络超时（>15s） | 立即降级爬取 |
| 两者均失败 | 跳过该 ASIN，在 stdout 输出 `{"asin": "...", "status": "failed"}` |
| ASIN 格式非法 | 立即报错，不请求 |

详细 API 字段映射参见 `references/rainforest-api.md`。
