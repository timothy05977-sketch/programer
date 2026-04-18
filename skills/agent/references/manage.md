# Manage Products Reference

## 操作映射

| 用户意图 | 操作方式 |
|---------|---------|
| 添加商品 | Bitable 写入 products 表 + 触发初始快照 |
| 删除商品 | Bitable 更新 products 表（状态改为 paused 或删除记录）|
| 查看列表 | Bitable 查询 products 表 active 记录 |
| 修改备注 | Bitable 更新 products 表对应记录的「备注」字段 |

所有操作通过飞书插件完成，结果用飞书插件「发送消息」工具回复确认卡片。

## 添加商品流程

1. 验证 ASIN 格式：
   ```bash
   python scripts/asin_utils.py <ASIN>
   ```
   输出 `valid: false` → 提示格式错误，终止

2. 检查是否已存在：使用飞书插件「多维表格-查询记录」，filter `ASIN = <asin>`
   找到记录 → 提示「已在监控列表中」，终止

3. 写入 products 表：使用飞书插件「多维表格-创建记录」：
   ```json
   {
     "ASIN": "<asin>",
     "商品名": "<title 或 待填充>",
     "状态": "active",
     "添加时间": "<ISO 8601>",
     "备注": "<用户备注或空>"
   }
   ```

4. 立即采集初始快照：
   ```bash
   python scripts/data_provider.py fetch --asin <ASIN>
   ```
   成功 → 使用飞书插件「多维表格-创建记录」将快照写入 snapshots 表，并回填 products 表的「商品名」字段

5. 回复确认：「已添加 {ASIN}（{title}），初始快照获取完成，下次汇报时将出现在列表中」

## 删除商品流程

1. 确认 ASIN 存在：使用飞书插件「多维表格-查询记录」，filter `ASIN = <asin>`
   未找到 → 提示「不在监控列表中」

2. 询问：「是否同时清除该商品的历史快照数据？（默认：保留）」

3. 执行：
   - 使用飞书插件「多维表格-删除记录」从 products 表删除该记录
   - 若用户选择清除：同样从 snapshots 表删除该 ASIN 的所有记录

4. 回复确认

## 飞书卡片回调（action: manage_products）

收到回调后，使用飞书插件「多维表格-查询记录」获取所有 active 商品，用飞书插件更新原卡片：

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
