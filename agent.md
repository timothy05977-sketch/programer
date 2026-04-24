---
name: amazon-tracker
version: 1.0
commands:
  - name: amz
    description: "Amazon Product Tracker — 启动亚马逊商品监控助手"
    usage: "/amz [-help] [意图描述]"
    examples:
      - "/amz"
      - "/amz -help"
      - "/amz 帮我监控 B0CHWX8DFH"
      - "/amz 生成周报"
---

# Purpose

每 20 分钟抓取监控商品的 Amazon 排名与价格，通过飞书卡片汇报、追加文档、写入多维表格；排名变动 > 3 位时独立发告警。

# Capabilities

| Skill | 驱动 | 职责 |
|-------|------|------|
| amz-monitor | 定时 | 完整 20 分钟循环 |
| amz-agent | 对话 | 配置、商品管理、查询、报告 |

# Decision Rules

- **焦点商品**：排名变动绝对值最大者；并列取当前排名更高；无历史则"首次快照"
- **告警**：`abs(rank_delta) > 3` 独立发红色卡片，不合并汇报；同方向连续 2 次起加"持续变化中"
- **降级链**：Rainforest → 直接爬取 → 跳过标注失败；连续 3 轮有失败触发飞书告警
- **初始化**：启动检查配置，缺失则触发 setup 流程并暂停调度

详细流程见 `skills/amz-monitor/SKILL.md` 与 `skills/amz-agent/SKILL.md`。
