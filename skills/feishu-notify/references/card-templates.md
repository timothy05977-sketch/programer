# Feishu Card Templates

使用 OpenClaw 飞书插件「发送消息」工具时，按以下模板组织卡片内容。

---

## 1. 定时汇报卡片（每 20 分钟）

**标题**：🔍 Amazon 监控报告 · {YYYY-MM-DD HH:mm}
**主题色**：蓝色（blue）

**焦点商品区块**（加粗标注）：
```
⚡ 焦点商品
{title}（{asin}）
排名  #{rank_prev} → #{rank_curr}  {▲/▼}{abs(delta)}位
价格  {price_prev} → {price_curr}  ({涨跌百分比})
{summary}
```

**全量商品表格**：
| 商品 | 当前排名 | 变化 | 价格 | 趋势 |
| {label} {title截断30字} | #{rank_curr} | {▲/▼/—}{delta} | {price_curr} | {trend_label} |

**操作按钮**：
- `查看完整文档` → type: url, url: `https://xxx.feishu.cn/docx/{feishu_doc_token}`
- `管理监控商品` → type: callback, action: `manage_products`

---

## 2. 告警卡片

**标题**：⚠️ 排名异动告警 · {HH:mm}
**主题色**：红色（red）

**内容**：
```
{title}（{asin}）
排名  #{rank_prev} → #{rank_curr}  {▲/▼}{abs(delta)}位
超过告警阈值 {threshold} 位

判断：{summary}
```
若连续告警：末尾追加「⚠ 持续变化中」

**操作按钮**：
- `查看趋势` → type: callback, action: `view_trend`, value: `{asin}`

---

## 3. 管理商品卡片（回调更新）

**标题**：📋 监控商品管理
**主题色**：默认（default）

**商品列表**（每行一个）：
```
{title截断25字}（{asin}）  [移除]
```
[移除] 按钮 → type: callback, action: `remove_product`, value: `{asin}`

**底部操作**：
- `+ 添加商品` → 更新卡片展示 ASIN 输入框（input 组件）
- `完成` → 关闭管理面板，恢复汇报卡片

---

## 4. 趋势详情卡片

**标题**：📊 {title} 趋势分析
**主题色**：绿色（green）

**内容**：
```
ASIN：{asin}
分析时间：{cycle_time}

排名：{label}
{rank_trend_description}

价格：{price_trend_description}

综合判断：{summary}

数据来源：{data_source}（共 {snapshot_count} 次快照）
```

**操作按钮**：
- `查看完整文档` → type: url

---

## 通用规范

- 商品名超过 30 字时截断并追加「…」
- 价格变化百分比保留一位小数，如 `-16.7%`
- 排名前面统一加 `#`，如 `#42`
- 数据来源为 scraper 时，在卡片底部追加灰色小字「⚠ 数据来源：直接爬取，仅供参考」
