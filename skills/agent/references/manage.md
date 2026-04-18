# Manage Products Reference

## 操作映射

| 用户意图 | 命令 | 备注 |
|---------|------|------|
| 添加商品 | `python scripts/manage_db.py add <ASIN> [--label "备注"]` | 自动触发一次初始快照 |
| 删除商品 | `python scripts/manage_db.py remove <ASIN>` | 历史数据默认保留 |
| 查看列表 | `python scripts/manage_db.py list` | 返回 JSON |
| 修改备注 | `python scripts/manage_db.py label <ASIN> "新备注"` | |

所有命令输出 JSON，解析后用飞书插件「发送消息」工具回复确认卡片。

## 添加商品流程

1. 验证 ASIN 格式（10 位大写字母数字，正则 `^[A-Z0-9]{10}$`）
2. 检查是否已在监控列表（重复则提示，不重复添加）
3. 写入 SQLite，立即调用 monitor skill 的 Step 1 获取初始快照
4. 回复确认：「已添加 {ASIN}，初始快照获取完成，下次汇报时将出现在列表中」

## 删除商品流程

1. 确认 ASIN 在列表中（不存在则提示）
2. 询问：「是否同时清除该商品的历史快照数据？（默认：保留）」
3. 执行删除，回复确认

## 飞书卡片回调（action: manage_products）

收到回调后，调用 `manage_db.py list` 获取当前列表，用飞书插件更新原卡片：

```
📋 监控商品管理（共 N 个）
─────────────────────────
{title 截断 25 字}（{asin}）  [移除]
{title 截断 25 字}（{asin}）  [移除]
─────────────────────────
[+ 添加商品]  [完成]
```

- `[移除]` → callback action: `remove_product`, value: `{asin}`
- `[+ 添加商品]` → 更新卡片，展示 ASIN 输入框（input 组件）
- 用户提交 ASIN → 执行添加流程，刷新卡片

## 飞书卡片回调（action: view_trend）

value 为 ASIN，加载 `references/query.md` 的「单商品趋势查询」流程执行。
