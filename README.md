# Codex AI Model Router + Auto Launcher

给 Codex 使用层加一个“智能调度器”：先分析任务复杂度，再决定执行模式与
模型，最后启动对应的 Codex。

它不改动你的 ROS2 机器人项目，机器人项目保持模型无关。以后换 Qwen、GPT、
本地模型也可以复用同一套路由配置。

## 执行模式

```text
用户任务
    |
    v
Task Router（复杂度 0-100）
    |
    +-- 0-40  Direct Mode  ------> Flash 直接执行
    +-- 40-70 Enhanced Direct ------> Flash/Pro + 简单计划
    +-- 70-100 Agent Mode --------> Supervisor 编排
                                      |
                                      v
                    Planner(Pro) -> Coder(Flash) -> Tester(Flash) -> Reviewer(Pro)
```

## 项目记忆（Project Memory）

执行任务前自动扫描当前目录：

- `README.md` / `AGENTS.md` / `PROJECT_STATUS.md` / `ARCHITECTURE.md`
- Git 分支、未提交文件、最近提交
- 技术栈（Python / ROS2 / Gazebo / YOLO / Docker 等）

生成统一上下文并注入到 Codex 提示与 Agent 各角色。缺少文件时不报错。
执行前会显示：

```text
[Project Context]
Project: ROS2-Embodied-Robot-Agent
Stack: ROS2, Python, Gazebo, YOLO
Recent: Vision Pipeline completed
```

## Git Lifecycle（v1.4）

独立的 Git 自动化闭环命令：

```powershell
# 只分析 + 建议 commit，不真正提交
python git_lifecycle.py

# 自动 git add + git commit
python git_lifecycle.py --commit

# commit 后 push origin 当前分支
python git_lifecycle.py --commit --push
```

`git_lifecycle.py` 会扫描分支/远程/改动文件，分析新增/修改/删除，按
`feat/fix/refactor/docs/test` 生成 commit，并输出 Task Report。`--push`
只执行普通 `git push origin <branch>`，不会 force push。

## Project Knowledge RAG（v1.5）

索引项目文档、代码和 git commit 到本地向量库，按问题检索证据：

```powershell
python rag_query.py "为什么这个模块这样设计？"
```

输出检索到的文档/代码/commit 片段与相关度分数。向量库使用依赖-free 的
hashing trick，无需外部模型或数据库。

## Agent Adapter Framework（v1.6）

模型 provider 可插拔：

```text
agents/base_agent.py            统一 BaseAgent 接口
agents/codex_agent/adapter.py   Codex
agents/deepseek_agent/          DeepSeek
agents/claude_agent/            Claude
agents/gemini_agent/            Gemini
agents/local_agent/             Ollama / LM Studio
```

`config.yaml` 的 `agent_adapters` 控制启用状态与 adapter class，新增 provider
只需增加 adapter 和注册配置，无需改动核心。查看已启用 adapter：

```powershell
python agent_registry.py
```

## Dynamic Agent Planner（v1.7）

Agent 模式会根据任务领域自动生成团队，而不是固定 Planner/Coder/Tester/
Reviewer：

- 软件开发 → Requirement / Architecture / Backend / Frontend / Testing / Reviewer
- 数据分析 → Research / Data / Python / Visualization / Reviewer
- 论文 → Research / Experiment / Writer / Reviewer
- ROS2 → Planner / Coder / Tester / Reviewer

由 `launcher/dynamic_planner.py` 负责领域识别与团队规划，`config.yaml` 的
`agents.dynamic: true` 开启。

## Multi-Agent Collaboration（v1.8）

`launcher/collaboration.py` 提供并行协作原语：

- 任务分配 `plan_parallel_tasks`
- 并发执行 `run_parallel`
- 结果合并 `merge_outputs`
- 文件冲突检测 `detect_file_conflicts`

## Multi Project Management（v1.9）

`project_manager.py` 维护多项目注册表，支持识别项目、加载 Memory 与 RAG、
保存历史：

```powershell
python project_manager.py register C:\path\to\project
python project_manager.py list
python project_manager.py load C:\path\to\project
```

## Universal AI Engineering Platform（v2.0）

`platform.py` 提供统一平台入口：

```powershell
python platform.py status
python platform.py run "修复Python报错" --dry-run
```

它组合了 Router / Memory / RAG / Agents / Git / Test / Report 全链路，
形成多模型、多智能体的软件工程自动化平台。

## 文件结构

```text
codex-router/
├── codex-auto.py
├── codex-auto.ps1
├── codex-auto.cmd
├── agent_registry.py
├── router.py
├── classifier.py
├── model_selector.py
├── config_loader.py
├── config.yaml
├── agents/
│   ├── base.py
│   ├── base_agent.py
│   ├── supervisor.md
│   ├── planner.md
│   ├── coder.md
│   ├── tester.md
│   ├── reviewer.md
│   ├── planner_agent.py
│   ├── coder_agent.py
│   ├── tester_agent.py
│   ├── reviewer_agent.py
│   ├── git_agent.py
│   ├── codex_agent/adapter.py
│   ├── deepseek_agent/adapter.py
│   ├── claude_agent/adapter.py
│   ├── gemini_agent/adapter.py
│   └── local_agent/adapter.py
├── orchestrator/
│   ├── supervisor.py
│   ├── workflow.py
│   ├── task_queue.py
│   └── agent_manager.py
├── providers/
│   ├── base_provider.py
│   ├── codex_provider.py
│   └── deepseek_provider.py
├── workflows/
│   └── developer_workflow.yaml
├── usage/
│   ├── tracker.py
│   ├── database.py
│   ├── models.py
│   ├── calculator.py
│   └── collector.py
├── dashboard/
│   ├── app.py
│   ├── charts.py
│   └── widgets.py
├── config/
│   └── pricing.yaml
├── memory/
│   ├── __init__.py
│   ├── project_scanner.py
│   └── context_builder.py
├── git_manager/
│   ├── __init__.py
│   ├── scanner.py
│   ├── diff_analyzer.py
│   ├── commit_generator.py
│   └── operator.py
├── task_manager/
│   └── manager.py
├── report/
│   └── generator.py
├── vector_store/
│   └── store.py
├── knowledge/
│   └── indexer.py
├── rag/
│   └── engine.py
├── project_manager/
│   └── manager.py
├── project_manager.py
├── platform.py
├── workflow.py
├── usage_cli.py
├── git_lifecycle.py
├── rag_query.py
├── launcher/
│   ├── codex_auto.py
│   ├── model_runner.py
│   ├── execution_mode.py
│   ├── agent_runner.py
│   ├── dynamic_planner.py
│   └── collaboration.py
├── scripts/
│   ├── install_default_entry.ps1
│   └── uninstall_default_entry.ps1
├── requirements.txt
├── tests/
│   ├── test_router.py
│   ├── test_launcher.py
│   ├── test_execution_mode.py
│   ├── test_memory.py
│   ├── test_git_lifecycle.py
│   └── test_rag.py
└── README.md
```

## 安装

```powershell
cd codex-router
python -m pip install -r requirements.txt
```

## 设为系统默认 codex 入口

```powershell
cd codex-router
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install_default_entry.ps1
```

安装后：

- `codex "任务"` 自动经过 router
- 原版 codex 备份为 `codex-real`
- `codex --help`、`codex --version`、`codex login` 等管理命令自动透传

卸载并恢复原版：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\uninstall_default_entry.ps1
```

## 使用

```powershell
# 自动路由
codex "修改README"
codex "设计ROS2机器人Agent系统架构"

# 强制执行模式
codex --direct "设计系统架构"
codex --agent "修改README"

# 强制模型
codex --flash "设计系统架构"
codex --pro "重构ROS2通信层"

# 原参数透传
codex --help
codex --add-dir C:\tmp --search "修改一个Python函数"
codex --model deepseek-v4-pro "修改一个Python函数"

# 预览命令，不真正执行
codex --dry-run "设计ROS2机器人Agent系统架构"
```

## 配置说明

```yaml
auto_router: true
default_model: flash

models:
  flash:
    provider: deepseek
    model_name: deepseek-v4-flash
  pro:
    provider: deepseek
    model_name: deepseek-v4-pro

threshold:
  pro_score: 70
  pro_token_warning: 8000

execution:
  direct_threshold: 40
  enhanced_threshold: 70

agents:
  enabled: true

agent_roles:
  planner:
    model: pro
    sandbox: read-only
  coder:
    model: flash
    sandbox: workspace-write
  tester:
    model: flash
    sandbox: workspace-write
  reviewer:
    model: pro
    sandbox: read-only

launcher:
  codex_bin: codex-real
  mode: exec
  model_switch: cli
  pass_provider: false
```

### 模型切换模式

| 模式 | 行为 | 适用场景 |
| --- | --- | --- |
| `cli` | `codex exec -m <model>` | Codex 支持 `--model` 直接切换 |
| `config` | `codex exec -c model=<model> -c model_provider=<provider>` | 用 `config.toml` 覆盖 |
| `profile` | `codex exec -p <profile>` | 模型绑定独立 profile |
| `env` | 设置 `MODEL_PROVIDER` / `MODEL_NAME` 环境变量 | API 登录模式通过环境变量切换 |

## 判断规则

复杂度评分 = 基础分 20，叠加关键词、文件数量、行数提示、`git diff` 范围，
最终限制在 0-100。

- 0-40 → Direct Mode + Flash
- 40-70 → Enhanced Direct Mode（默认 Flash）
- 70-100 → Agent Mode（Planner/Coder/Tester/Reviewer）

## Agent 角色

| 角色 | 模型 | 职责 |
| --- | --- | --- |
| Supervisor | — | 拆分任务、分配角色、汇总结果 |
| Planner | Pro | 架构设计、技术方案，不改代码 |
| Coder | Flash | 编写代码、修改文件 |
| Tester | Flash | 运行测试、报告结果 |
| Reviewer | Pro | 代码质量与架构审查 |

## 安全机制

选择 Pro 且预估 token 超过 `threshold.pro_token_warning` 时先询问确认。
Agent 模式可用 `--dry-run` 预览完整流水线，避免误触发多轮模型调用。

## 测试

```powershell
python -m unittest discover -s tests -v
```

覆盖：Direct/Enhanced/Agent 模式判定、`--direct` / `--agent` 覆盖、Agent
角色与模型、项目上下文扫描（空目录 / Git / ROS2）、参数透传、显式
`--model` 尊重，以及 `cli` / `config` / `env` 三种命令构建。


## Universal Developer Agent Workflow（v2.1）

Agent 与 Provider 分离：

- `agents/base.py` 统一 BaseAgent / AgentResult
- `providers/` 统一 LLMProvider，Codex 已实现，DeepSeek 预留
- `orchestrator/` 负责任务队列、Agent 管理、Supervisor 调度与 workflow
- 5 个内置 Agent：Planner / Coder / Tester / Reviewer / Git

```powershell
# 运行默认 developer workflow
codex --workflow "重构ROS2机器人控制模块"

# 指定单个 Agent
codex --agent planner "重构ROS2机器人控制模块"

# 查看 workflow 状态
codex --workflow-status
```


## Token Usage Monitoring（v2.1）

统一记录模型调用消耗，SQLite 存储，按模型/项目/Agent 统计成本：

```powershell
codex --usage
codex --usage --detail
```

价格配置位于 `config/pricing.yaml`，支持 DeepSeek / GPT / Claude / Gemini /
本地模型，不硬编码。桌面 Dashboard 入口：

```powershell
python dashboard/app.py
```
