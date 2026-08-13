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

## 文件结构

```text
codex-router/
├── codex-auto.py
├── codex-auto.ps1
├── codex-auto.cmd
├── router.py
├── classifier.py
├── model_selector.py
├── config_loader.py
├── config.yaml
├── agents/
│   ├── supervisor.md
│   ├── planner.md
│   ├── coder.md
│   ├── tester.md
│   └── reviewer.md
├── memory/
│   ├── __init__.py
│   ├── project_scanner.py
│   └── context_builder.py
├── launcher/
│   ├── codex_auto.py
│   ├── model_runner.py
│   ├── execution_mode.py
│   └── agent_runner.py
├── scripts/
│   ├── install_default_entry.ps1
│   └── uninstall_default_entry.ps1
├── requirements.txt
├── tests/
│   ├── test_router.py
│   ├── test_launcher.py
│   └── test_execution_mode.py
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
