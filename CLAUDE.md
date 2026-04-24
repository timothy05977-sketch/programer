# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

亚马逊商品监控 Agent，运行于 OpenClaw 平台。每 20 分钟自动采集排名与价格，通过飞书卡片推送动态、追加飞书云文档、写入飞书多维表格（Bitable），排名异动时触发告警。

**唯一数据存储**：飞书 Bitable（两张表：products + snapshots）。没有本地数据库。

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行全部测试
python -m pytest tests/ -v

# 运行单个测试文件
python -m pytest tests/test_analyze.py -v

# 运行单个测试用例
python -m pytest tests/test_analyze.py::TestLabel::test_consecutive_up -v

# 配置检查
python skills/amz-agent/scripts/init_config.py check

# 测试 Rainforest API Key 是否有效
python skills/amz-agent/scripts/init_config.py test-rainforest

# 手动采集快照（输出 JSON）
python skills/amz-monitor/scripts/data_provider.py fetch --asin B0CHWX8DFH

# 手动趋势分析（从 stdin 读 JSON）
echo '{"products":[...]}' | python skills/amz-monitor/scripts/analyze.py --all

# 生成周报（从 stdin 读 JSON）
echo '{"products":[...]}' | python skills/amz-agent/scripts/weekly_report.py --days 7
```

## 架构

### 双 Skill 结构

| Skill | 文件 | 触发方式 | 职责 |
|-------|------|---------|------|
| `amz-monitor` | `skills/amz-monitor/SKILL.md` | 定时调度（每 20 分钟）| 采集 → 分析 → 推送卡片 → 写文档 → 写 Bitable |
| `amz-agent` | `skills/amz-agent/SKILL.md` | 用户消息 / `/amz` 命令 | 配置引导、商品管理、查询、报告生成 |

SKILL.md frontmatter（`name` + `description`）始终加载；body 仅在 Skill 触发时加载；`references/*.md` 按意图按需加载（progressive disclosure）。

### 脚本协议：stdin JSON → stdout JSON

所有 Python 脚本都是**纯计算**，不访问 Bitable，不发飞书消息。由 OpenClaw Agent 通过 `@larksuite/openclaw-lark` 官方插件完成所有飞书 API 调用。

| 脚本 | 位置 | 输入 | 输出 |
|------|------|------|------|
| `data_provider.py` | `skills/amz-monitor/scripts/` | CLI 参数（`--asin`）| 快照 JSON |
| `analyze.py` | `skills/amz-monitor/scripts/` | stdin JSON（products + history）| 趋势/告警 JSON |
| `rainforest.py` | `skills/amz-monitor/scripts/` | 被 data_provider 调用 | Snapshot 对象 |
| `scraper.py` | `skills/amz-monitor/scripts/` | 被 data_provider 调用 | Snapshot 对象 |
| `init_config.py` | `skills/amz-agent/scripts/` | CLI 参数 | 配置状态 JSON |
| `asin_utils.py` | `skills/amz-agent/scripts/` | CLI 参数（ASIN 列表）| 校验结果 JSON |
| `weekly_report.py` | `skills/amz-agent/scripts/` | stdin JSON（products + snapshots）| 报告 JSON |

### 共享层

- `shared/config.py`：配置加载。优先级：环境变量 > `.tracker_config.json` > 默认值。`REQUIRED_KEYS` 是初始化检查的唯一来源，`is_initialized()` 依赖它。
- `shared/models.py`：`Snapshot` dataclass，所有采集脚本的通用数据结构。

### 数据降级链

`data_provider._fetch_one()` 实现：Rainforest API → 直接爬取 (`scraper`)。有 Rainforest Key 时优先调用；遇 429 等待 60s 后重试一次；失败则降级爬取；两者都失败返回 `{"status":"failed"}`。

### 告警规则

`analyze.py` 中：`abs(rank_delta) > THRESHOLD`（默认 3）触发告警。`THRESHOLD` 从 `shared/config` 读取，测试中需 mock `cfg.get` 或 `THRESHOLD` 常量。

## 测试

测试框架：`pytest` + `responses`（HTTP mock）。`tests/conftest.py` 将 `shared/`、`skills/amz-monitor/scripts/`、`skills/amz-agent/scripts/` 全部加入 `sys.path`。

测试分两层：
- **L1 单元测试**：纯函数直接调用（`test_analyze.py`、`test_weekly_report.py`、`test_asin_utils.py`、`test_config.py`）
- **L2 mock 集成测试**：用 `responses` 库拦截 HTTP（`test_rainforest.py`、`test_scraper.py`、`test_data_provider.py`）

## 配置

配置文件路径：项目根目录 `.tracker_config.json`（被 `.gitignore` 排除）。

必填项（`REQUIRED_KEYS`）：`amazon_marketplace`、`feishu_doc_token`、`feishu_bitable_token`、`feishu_bitable_table_id_products`、`feishu_bitable_table_id_snapshots`。

`rainforest_api_key` 可选，缺失时自动降级爬取。

环境变量名为配置 key 的大写形式（如 `FEISHU_DOC_TOKEN`），可覆盖文件配置。

## 扩展规范

- 新增用户交互能力：在 `skills/amz-agent/references/` 新增 `.md`，在 `skills/amz-agent/SKILL.md` 意图路由表加一行。
- 新增脚本：保持 stdin JSON → stdout JSON 协议，不在脚本内调用飞书 API。
- Bitable schema 变更：对照 `skills/amz-agent/references/bitable-schema.md` 更新字段定义。
