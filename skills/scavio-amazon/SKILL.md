---
name: scavio-amazon
description: 亚马逊商品监控与搜索 Skill，由 Scavio API 驱动。支持商品快照采集、关键词搜索、ASIN 查询、趋势分析及飞书推送。
---

# Scavio Amazon

处理所有亚马逊商品相关操作，由 Scavio API 提供数据。根据触发方式分为定时监控链和用户交互两条路径。

## 初始化检查

每次激活前执行：

```bash
python scripts/init_config.py check
```

若 `initialized: false`，加载 `references/setup.md` 引导配置并暂停调度。

---

## 路径 A — 定时监控（每 20 分钟）

**Step 1** 从飞书 Bitable `products` 表查询所有 `status=active` 商品，获取 ASIN 列表。

**Step 2** 批量采集快照：

```bash
python scripts/data_provider.py fetch --asin <ASIN1> [--asin <ASIN2> ...]
```

**Step 3** 从 Bitable `snapshots` 表为每个 ASIN 查询最近 5 条历史记录，将本次快照合并进去，送入分析：

```bash
echo '<stdin json>' | python scripts/analyze.py --all
```

**Step 4** 用飞书插件将本次快照写入 `snapshots` 表。

**Step 5** 根据分析结果：
- 汇报卡片：展示排名变化、焦点商品、价格变动摘要
- 告警卡片：`alert=true` 的商品单独发红色卡片（与汇报卡片同一轮次）
- 追加飞书文档：写入摘要与产品清单

**Step 6** 连续告警检测：若同一 ASIN 最近 3 次快照均 `abs(rank_delta) > threshold`，在告警卡片底部追加「持续变化中」标注。

---

## 路径 B — 用户交互（`/amz` 命令或自然语言）

根据用户意图路由到参考文档：

| 意图 | 参考文档 |
|------|---------|
| 首次配置 / 设置 API Key | `references/setup.md` |
| 添加 / 删除 / 列出商品 | `references/manage.md` |
| 查询排名、价格、趋势 | `references/query.md` |
| 生成周报 / 月报 | `references/report.md` |
| 帮助说明 | `references/help.md` |
| Bitable 字段定义 | `references/bitable-schema.md` |

收到 `/amz` 命令时，加载对应参考文档后执行其中的步骤。

---

## 数据源

| 优先级 | 来源 | 触发条件 |
|--------|------|---------|
| 1 | Scavio API | `SCAVIO_API_KEY` 已配置 |
| 2 | 直接爬取 (scraper) | Scavio 失败或无 Key |

两者均失败时返回 `{"status":"failed"}`，连续 3 轮失败触发飞书告警。

---

## 关键词搜索（用户请求时）

```bash
python scripts/data_provider.py search --query "wireless headphones" --sort average_review
```

结果展示：商品名、价格、评分、评论数、URL、Prime 状态。

---

## 守则

- 不伪造商品名称、ASIN、价格或评分，数据必须来自 API 或爬取。
- 若 ASIN 未找到，告知用户并建议使用关键词搜索。
- 始终附上商品 URL，方便用户核实。
- API 返回错误时，上报状态码并停止当前步骤。
