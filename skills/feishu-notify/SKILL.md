---
name: feishu-notify
description: Send Feishu message cards for monitoring reports and alerts. Use this skill after every analyze-trend cycle to send the 20-minute report card, when any product's rank change exceeds the alert threshold (default 3 positions) to send an alert card, or when responding to user interactions (manage products button callback). Uses the OpenClaw Feishu plugin tools to send messages — no direct API calls needed.
---

# Feishu Notify

使用 OpenClaw 飞书插件的「发送消息」工具，向配置的飞书群/会话推送卡片。

## 每 20 分钟汇报卡片

从 `analyze-trend` 的 JSON 输出中读取数据，调用飞书插件工具发送以下结构的卡片：

```
标题：🔍 Amazon 监控报告 · {时间}
---
⚡ 焦点商品
{title}（{asin}）
排名  #{rank_prev} → #{rank_curr}  {方向}{delta}位
价格  {price_prev} → {price_curr}  {涨跌百分比}
趋势：{summary}
---
全部监控商品
| 商品 | 当前排名 | 变化 | 价格 | 趋势 |
| ... | ...     | ... | ... | ... |
---
[查看完整文档]  [管理监控商品]
```

- `[查看完整文档]` 按钮：链接跳转到飞书文档（URL 由 `feishu_doc_token` 拼接）
- `[管理监控商品]` 按钮：触发 callback，action 值为 `manage_products`

## 告警卡片（排名变动 > 阈值）

对每个 `alert: true` 的商品独立发送，使用红色主题：

```
标题：⚠️ 排名异动告警 · {时间}
---
{title}（{asin}）
排名  #{rank_prev} → #{rank_curr}  {方向}{delta}位（超过阈值 {threshold} 位）
判断：{summary}
---
[查看趋势]
```

同一商品同方向连续告警第 2 次起，在判断末尾追加「持续变化中」。

## 卡片回调处理

收到 action 为 `manage_products` 的回调时：
1. 调用 `manage-products` skill 获取当前商品列表
2. 更新原卡片，展示带 [移除] 按钮的列表 + [+ 添加] 按钮
3. 用户填写新 ASIN 提交后，调用 `manage-products` skill 执行添加，刷新卡片

详细卡片内容模板见 `references/card-templates.md`。
