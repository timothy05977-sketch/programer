---
name: manage-products
description: Manage the list of Amazon products under monitoring. Use this skill when the user wants to add a product (添加/add/monitor/监控), remove a product (删除/移除/remove/stop), view the current list (查看/列表/list), or update a product's label/note. Accepts ASIN codes or product names. Also triggered when a user clicks the "管理商品" button on a Feishu card callback.
---

# Manage Products

对监控商品列表进行增删改查，所有操作持久化到 SQLite。

## 操作映射

| 用户意图 | 执行命令 |
|---------|---------|
| 添加商品 | `scripts/manage_db.py add <ASIN> [--label "备注"]` |
| 删除商品 | `scripts/manage_db.py remove <ASIN>` |
| 查看列表 | `scripts/manage_db.py list` |
| 修改备注 | `scripts/manage_db.py label <ASIN> "新备注"` |

## 添加商品

1. 验证 ASIN 格式（10位字母数字，大写）
2. 检查是否已在监控列表中（重复则提示无需重复添加）
3. 写入数据库，立即触发一次 `fetch-data` 获取初始快照
4. 回复确认消息，告知下次汇报时间

## 删除商品

1. 确认 ASIN 存在于列表
2. 询问是否保留历史快照数据（默认保留）
3. 从 products 表删除，snapshots 数据保留（除非用户选择清除）

## 查看列表

输出当前所有监控商品，格式：
```
监控中 (N 个商品)
ASIN          备注          添加时间
B0CHWX8DFH   蓝牙耳机      2026-04-18
B09G9HD6PD   无线鼠标      2026-04-18
```

## 飞书卡片回调处理

当来自飞书卡片的 callback action 为 `manage_products` 时：
- 返回带操作按钮的更新卡片（每个商品一行，含 [移除] 按钮）
- 用户点击 [+ 添加] 后返回 input 组件卡片
- 操作完成后刷新卡片显示最新列表
