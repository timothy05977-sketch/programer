# Amazon Product Tracker

基于 OpenClaw 的亚马逊商品监控 Agent，每 20 分钟自动抓取排名与价格数据，
通过飞书卡片推送动态、追加飞书文档、写入飞书多维表格，并在排名异动时发告警。

---

## 目录

- [架构概览](#架构概览)
- [快速开始](#快速开始)
- [配置项说明](#配置项说明)
- [日常使用](#日常使用)
- [命令与意图](#命令与意图)
- [数据存储](#数据存储)
- [定时调度](#定时调度)
- [告警规则](#告警规则)
- [故障排查](#故障排查)
- [目录结构](#目录结构)

---

## 架构概览

```
┌────────────┐     ┌───────────────────┐     ┌──────────────────┐
│ 20-min 调度 │ ──▶ │  amz-monitor      │ ──▶ │  飞书卡片 / 文档   │
└────────────┘     │  （机器驱动）      │     │  飞书多维表格      │
                   └───────────────────┘     └──────────────────┘
                            ▲
┌────────────┐     ┌───────────────────┐
│  用户对话   │ ──▶ │   amz-agent       │
└────────────┘     │   （人驱动）       │
                   └───────────────────┘
```

| 组成 | 作用 |
|------|------|
| `soul.md` | Agent 人格定义 · 数据诚实、焦点驱动 |
| `agent.md` | 整体能力声明 · 调度规则 · 告警标准 |
| `skills/amz-monitor/` | 定时自动链条（采集 → 分析 → 卡片 → 文档 → Bitable）|
| `skills/amz-agent/` | 用户交互（配置、商品管理、趋势查询、报告生成）|
| `shared/` | 配置加载 + Snapshot 数据模型 |
| 飞书多维表格（Bitable） | **唯一数据存储**（两张表：products + snapshots）|
| `@larksuite/openclaw-lark` 插件 | 所有飞书 API 调用由官方插件处理 |

---

## 快速开始

### 1. 部署 Agent

将本项目加载到 OpenClaw 平台，或在支持 SKILL 协议的运行时中启用。确保：
- Python 3.10+
- 已安装 `@larksuite/openclaw-lark` 飞书插件
- 可以访问互联网（Rainforest / Amazon）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动 Agent

在飞书中输入 `/amz` 命令即可唤醒 Agent：

```
/amz
```

若尚未完成配置，Agent 会自动进入引导向导，依次收集 5 项配置；完成后推送欢迎卡片，并在下一个 20 分钟整点启动监控。

也可以不带斜杠，直接发任意一句话触发：

```
你好
```

---

## 配置项说明

所有配置保存在项目根目录的 `.tracker_config.json`，也可通过环境变量覆盖。

| 配置键 | 说明 | 是否必填 | 环境变量 |
|--------|------|---------|---------|
| `amazon_marketplace` | 市场代码（US/JP/UK/DE/CA）| ✅ | — |
| `rainforest_api_key` | Rainforest API Key | 推荐 | `RAINFOREST_API_KEY` |
| `feishu_doc_token` | 飞书云文档的 docx token | ✅ | `FEISHU_DOC_TOKEN` |
| `feishu_bitable_token` | 多维表格 app_token | ✅ | `FEISHU_BITABLE_TOKEN` |
| `feishu_bitable_table_id_products` | 监控商品表 ID | ✅（自动建表）| — |
| `feishu_bitable_table_id_snapshots` | 快照历史表 ID | ✅（自动建表）| — |
| `alert_threshold` | 排名异动阈值（默认 3）| 可选 | — |
| `interval_minutes` | 采集周期（默认 20）| 可选 | — |

Rainforest Key 留空时自动降级使用直接爬取（稳定性较低）。

---

## 日常使用

系统支持两种操作方式：
- **`/amz` 命令**：在飞书输入框直接触发，支持参数
- **自然语言**：直接发消息，Agent 自动理解意图

### `/amz` 命令速查

| 命令 | 效果 |
|------|------|
| `/amz` | 唤醒 Agent（未配置时自动进入向导）|
| `/amz -help` | 显示完整帮助卡片 |
| `/amz 帮我监控 B0CHWX8DFH` | 添加商品（带前缀的完整指令）|
| `/amz 生成周报` | 生成报告 |
| `/amz 刷新` | 手动触发一次监控 |

`/amz <任意文字>` 等价于直接说那句话，`/amz` 只是入口唤醒词。

### 添加监控商品

```
/amz 帮我监控 B0CHWX8DFH
添加商品 B09G9HD6PD 备注：竞品A
```

### 删除监控商品

```
把 B0CHWX8DFH 从监控列表去掉
删除竞品A
```

### 查看监控列表

```
当前在监控哪些商品？
列表
```

### 查询单品趋势

```
B0CHWX8DFH 最近怎样？
竞品A 的价格走势
```

### 查看全量状态

```
现在所有商品怎么样
当前状态
```

### 查询爆款榜单

```
电子类的爆款榜单
top 20 玩具
```

### 生成报告

```
生成周报
给我一份月报
```

### 手动触发监控

```
/amz 刷新
立即检查
```

### 获取帮助

```
/amz -help
帮助
```

---

## 命令与意图

下表列出 amz-agent 识别的用户意图及映射的内部操作（大部分情况用户无需关心）。

| 意图关键词 | 参考文档 | 涉及脚本 |
|-----------|---------|---------|
| `/amz`（裸命令）| 唤醒入口，未配置则自动走 setup | `init_config.py` |
| `/amz -help` / 帮助 / help / 怎么用 | `references/help.md` | — |
| 配置 / 初始化 / reset | `references/setup.md` | `init_config.py` |
| 添加 / 删除 / 查看 / 备注 | `references/manage.md` | `asin_utils.py` |
| 趋势 / 价格 / 排名 / 爆款 | `references/query.md` | `analyze.py` / `data_provider.py` |
| 报告 / 周报 / 月报 / 汇总 | `references/report.md` | `weekly_report.py` |

底层脚本均为纯计算：**接受 stdin JSON，输出 stdout JSON，不访问数据库**。

---

## 数据存储

不使用本地 SQLite，所有数据存在飞书多维表格（Bitable），首次配置时由 agent
自动建表。详见 `skills/amz-agent/references/bitable-schema.md`。

### products 表

| 字段 | 类型 |
|------|------|
| ASIN | 文本（主键）|
| 商品名 | 文本 |
| 状态 | 单选（active/paused）|
| 添加时间 | 日期时间 |
| 备注 | 文本 |

### snapshots 表

| 字段 | 类型 |
|------|------|
| ASIN | 文本 |
| 商品名 | 文本 |
| 记录时间 | 日期时间 |
| 当前排名 | 数字 |
| 排名变化 | 数字 |
| 当前价格 | 数字 |
| 价格原文 | 文本 |
| 趋势标签 | 单选（📈/📉/➡/⚠/—）|
| 数据来源 | 单选（rainforest/scraper）|

---

## 定时调度

每 20 分钟固定执行 amz-monitor 的 8 步链条：

```
1. 读取 products 表 active 商品
2. data_provider.py fetch → 采集快照
3. 读取 snapshots 表历史（每 ASIN 最近 20 条）
4. analyze.py --all → 计算趋势与告警
5. 发送汇报卡片（蓝色主题）
6. 排名变动 > 阈值 → 发送告警卡片（红色主题，每商品单独一张）
7. 追加飞书文档时间戳区块
8. 写入 snapshots 表
```

---

## 告警规则

| 条件 | 动作 |
|------|------|
| `abs(rank_delta) > alert_threshold`（默认 3）| 单独发红色告警卡片 |
| 同一商品同方向连续 2 次告警 | 末尾追加「⚠ 持续变化中」|
| 单次采集失败 | 汇报卡片标注「获取失败」，继续其他商品 |
| 全部 ASIN 采集失败 | 本轮跳过，发告警消息 |
| 连续 3 轮有失败 | 飞书通知「请检查配置」|

### 趋势标签

| 标签 | 条件 |
|------|------|
| 📈 上升 | 连续 ≥ 2 次排名提升 |
| 📉 下降 | 连续 ≥ 2 次排名下降 |
| ➡ 稳定 | 单次变动 ≤ 3 位 |
| ⚠ 异动 | 单次变动 > 3 位 |
| — 数据不足 | 快照数 < 2 |

---

## 故障排查

### 无法获取商品数据

1. 检查 Rainforest Key：`python skills/amz-agent/scripts/init_config.py test-rainforest`
2. 状态返回 `invalid_api_key` → 重新配置 Key
3. 无 Key 时会自动降级爬取，但 Amazon 反爬偶发，稍后重试即可

### 飞书卡片未推送

1. 检查飞书插件是否正确加载
2. 确认 `feishu_doc_token` / `feishu_bitable_token` 均在同一飞书租户下
3. 检查应用（机器人）是否被加入目标群组 / 拥有文档编辑权限

### Bitable 读写报权限错误

1. 确认已将机器人添加到多维表格的协作者
2. 若字段类型不匹配，对照 `bitable-schema.md` 重新创建表

### 配置检查

```bash
python skills/amz-agent/scripts/init_config.py check
```

输出 JSON，包含 `initialized`（是否就绪）、`missing`（缺失项列表）、
`has_rainforest_key`、`marketplace`。

---

## 目录结构

```
programer/
├── README.md                      # 本文件
├── soul.md                        # Agent 人格
├── agent.md                       # 能力 & 调度 & 规则
├── requirements.txt
├── shared/
│   ├── config.py                  # 配置加载（含环境变量覆盖）
│   └── models.py                  # Snapshot 数据类
└── skills/
    ├── amz-monitor/               # 机器驱动的 20 分钟循环
    │   ├── SKILL.md
    │   └── scripts/
    │       ├── data_provider.py   # 采集（Rainforest + 爬取降级）
    │       ├── analyze.py         # 趋势分析（纯计算）
    │       ├── rainforest.py
    │       └── scraper.py
    └── amz-agent/                 # 人驱动的对话
        ├── SKILL.md               # 意图路由表
        ├── references/
        │   ├── setup.md           # 首次配置引导
        │   ├── manage.md          # 商品增删查改
        │   ├── query.md           # 趋势 / 榜单查询
        │   ├── report.md          # 周报 / 月报
        │   ├── help.md            # 帮助指引
        │   └── bitable-schema.md  # 数据库 schema
        └── scripts/
            ├── init_config.py     # 配置保存 / 检测
            ├── asin_utils.py      # ASIN 校验
            └── weekly_report.py   # 报告聚合（纯计算）
```

---

## 测试

脚本层使用 pytest 单元测试 + HTTP mock 集成测试，零外部依赖，< 3 秒跑完。

```bash
pip install pytest responses
python -m pytest tests/ -v
```

覆盖范围：

| 文件 | 测试 |
|------|------|
| `tests/test_asin_utils.py` | ASIN 规范化、校验、CLI |
| `tests/test_analyze.py` | 趋势标签、告警阈值、焦点商品、CLI stdin/stdout |
| `tests/test_weekly_report.py` | 聚合统计、周/月报趋势分级、CLI |
| `tests/test_rainforest.py` | API 正常路径、缺字段、HTTP 错误、缺 key |
| `tests/test_scraper.py` | 页面解析、容错、HTTP 错误 |
| `tests/test_data_provider.py` | 降级链（Rainforest → scraper）、429 退避 |
| `tests/test_config.py` | 默认值、env 覆盖、`is_initialized()` 必填校验 |

端到端（飞书卡片 / 文档 / Bitable 真实写入）不在脚本测试范围内，请在测试飞书租户手动演练。

---

## 开发者说明

- **所有脚本零 DB 依赖**：接受 stdin JSON，输出 stdout JSON，由 agent 通过飞书插件读写 Bitable
- **飞书 API 调用**：一律通过 `@larksuite/openclaw-lark` 插件，不要写自定义 HTTP 客户端
- **Progressive disclosure**：agent SKILL.md 保持精简，细节放在 `references/*.md`，按需加载
- 贡献新能力时，先扩充 `references/`，再在 `agent/SKILL.md` 路由表加一行即可
