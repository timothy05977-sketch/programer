---
name: amazon-tracker
version: 1.0
---

# Purpose

每 20 分钟自动抓取并分析所有监控商品的 Amazon 数据，通过飞书卡片汇报动态、追加飞书文档记录、在排名变动超过 3 位时发送告警。支持用户通过自然语言动态管理监控列表。

# Capabilities

| Skill | 职责 |
|-------|------|
| init-tracker | 首次配置引导 |
| manage-products | 增删改查监控商品 |
| fetch-data | 获取商品快照（Rainforest → 降级爬取）|
| analyze-trend | 趋势分析 + 焦点商品判断 |
| feishu-notify | 发送汇报卡片 & 告警卡片 |
| feishu-doc | 追加飞书文档 & 更新 Bitable |
| generate-report | 生成周报/月报 |

# Scheduling（20-Minute Cycle）

每轮固定执行链：

```
fetch-data（全部监控 ASIN）
  → analyze-trend（计算变化 & 焦点商品）
  → feishu-doc（追加文档区块 + 更新 Bitable）
  → feishu-notify（发送汇报卡片）
  → [若排名变动 > 3 位] feishu-notify（发送告警卡片）
```

# Decision Rules

## 焦点商品
- 本轮所有监控商品中，排名变动绝对值最大的商品
- 并列时，取当前排名更高（数字更小）的商品
- 无历史数据时，标注"首次快照，无对比基准"

## 告警触发
- 条件：`abs(current_rank - previous_rank) > 3`
- 告警卡片独立发送，不合并进汇报卡片
- 同一商品同一方向连续告警，第二次起加注"持续变化中"

## 降级处理
- Rainforest API 失败（HTTP 非 200 / 429 / 超时）→ 自动切换直接爬取
- 直接爬取也失败 → 跳过该 ASIN，在汇报卡片中标注"本轮数据获取失败"
- 连续 3 轮失败 → 飞书告警通知，提示用户检查配置

## 初始化检测
- 每次启动检查配置完整性（Amazon 市场、Rainforest Key、飞书文档 Token）
- 配置缺失 → 优先触发 init-tracker，暂停调度直至配置完成

# Output Standards

## 汇报卡片结构
1. 标题：报告时间
2. 焦点商品模块（排名变化 + 价格变化 + 趋势描述）
3. 全量商品状态表（ASIN / 排名变化 / 价格 / 趋势标签）
4. 操作按钮：[查看文档] [管理商品]

## 文档追加结构
1. H2 时间戳标题
2. 全量数据表格
3. 飞书 Bitable 内嵌排名趋势图
4. 焦点商品文字摘要

## 趋势标签规范
| 标签 | 条件 |
|------|------|
| 📈 上升 | 连续 2 次及以上排名提升 |
| 📉 下降 | 连续 2 次及以上排名下降 |
| ➡ 稳定 | 变动 ≤ 3 位 |
| ⚠ 异动 | 单次变动 > 3 位 |
| — 数据不足 | 快照数 < 2 |
