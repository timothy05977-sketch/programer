# Setup Reference

## 触发条件

- 用户首次使用
- `scripts/init_config.py check` 返回 `initialized: false`
- 用户说"重新配置"/"reset config"

## 配置收集流程

每次只问一个问题，等用户回答后再继续。

### Step 1 — Amazon 市场
```
你想监控哪个 Amazon 市场？
  1. 美国 (US) · amazon.com
  2. 日本 (JP) · amazon.co.jp
  3. 英国 (UK) · amazon.co.uk
  4. 德国 (DE) · amazon.de
  5. 加拿大 (CA) · amazon.ca
```

### Step 2 — Rainforest API Key
说明：用于稳定获取 Amazon 数据。无此 Key 时自动降级直接爬取，但稳定性较低。
- 接受用户粘贴 Key
- 或用户选择「跳过，使用爬取降级」

### Step 3 — 飞书文档 Token
说明：监控报告每 20 分钟追加写入的目标文档。
提示：打开飞书文档，URL 末段即为 Token。
例：`https://xxx.feishu.cn/docx/AbCdEfGh` → Token 是 `AbCdEfGh`

### Step 4 — 飞书多维表格（Bitable）
说明：用于存储监控商品列表和历史快照，是系统的唯一数据库。

1. 收集 `feishu_bitable_token` — 多维表格的 app_token
   提示：打开多维表格，URL 格式为 `https://xxx.feishu.cn/base/<app_token>`

2. **自动建表**：使用飞书插件「多维表格-创建数据表」工具分别创建两张表：
   - **products 表**（字段：ASIN/文本、商品名/文本、状态/单选、添加时间/日期时间、备注/文本）
   - **snapshots 表**（字段：ASIN/文本、商品名/文本、记录时间/日期时间、当前排名/数字、排名变化/数字、当前价格/数字、价格原文/文本、趋势标签/单选、数据来源/单选）

   将创建返回的两个 table_id 存入配置：
   - `feishu_bitable_table_id_products`
   - `feishu_bitable_table_id_snapshots`

### Step 5 — 初始监控商品
询问至少 1 个 ASIN（10 位大写字母数字），支持逗号分隔批量输入。
或选择「暂时跳过，稍后添加」。

有 ASIN 时：使用飞书插件「多维表格-创建记录」工具写入 products 表，
字段 `状态 = active`、`添加时间 = 当前时间`。

## 完成后执行

```bash
python scripts/init_config.py save \
  --amazon-marketplace US \
  --rainforest-api-key <KEY> \
  --feishu-doc-token <TOKEN> \
  --feishu-bitable-token <TOKEN> \
  --feishu-bitable-table-id-products <ID> \
  --feishu-bitable-table-id-snapshots <ID>
```

验证：
```bash
python scripts/init_config.py test-rainforest   # 若有 Key
```

飞书文档权限：用飞书插件「更新云文档」工具向文档写入一行「Amazon 监控初始化 ✓」测试权限。

全部通过 → 发送**欢迎卡片**（见下节）
任一失败 → 说明具体原因，引导用户重新填写对应项

## 欢迎卡片（首次配置完成后立即推送）

使用飞书插件「发送消息」发送绿色主题的欢迎卡片，让用户快速知道下一步怎么用：

```
🎉 配置完成！Amazon 监控已就绪
─────────────────────────
📍 市场：{marketplace}  ·  监控商品：{N} 个
⏱ 下一次自动采集：{下个 20 分钟整点时间}

🚀 现在你可以试试这样说：
  · 「帮我监控 B0XXXXXXXX」       — 添加商品
  · 「B0CHWX8DFH 最近怎样」        — 查询单品趋势
  · 「现在所有商品怎么样」         — 查看全量状态
  · 「电子类的爆款榜单」           — 拉取 Amazon Top 榜
  · 「生成周报」 / 「生成月报」    — 汇总报告
  · 「刷新」                      — 立即触发一次监控
  · 「/help」 或 「帮助」          — 查看完整功能列表
─────────────────────────
[查看文档]   [管理商品]   [查看帮助]
```

- `[查看文档]` → URL 跳转 `https://xxx.feishu.cn/docx/{feishu_doc_token}`
- `[管理商品]` → callback action: `manage_products`
- `[查看帮助]` → callback action: `show_help`（加载 `references/help.md`）

若用户在 Step 5 选择了「跳过监控商品」，欢迎卡片将额外追加一段提示：

```
💡 你还没添加任何监控商品，可以随时说「帮我监控 B0XXXXXXXX」开始
```
