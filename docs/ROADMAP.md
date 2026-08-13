# codex-router Future Roadmap v3.0 - v4.0

## 当前状态

已完成：

- v1.x：模型路由、Agent Adapter、项目上下文
- v2.x：Workflow、多 Agent 协作、RAG、Token 统计、Dashboard、多 Provider、健康检查、Fallback、Desktop 状态中心、智能任务规划判断

## 目标

从“AI 任务执行平台”升级为“AI 软件研发操作系统”。

## 推荐顺序

```text
v2.5
  |
实际使用 AI-Robot-Demo
  |
v3.0 自动测试闭环
  |
v3.1 项目记忆
  |
v3.2 代码理解
  |
v3.3 实验 Agent
  |
v3.4 项目团队
  |
v4.0 AI 研发平台
```

## v3.0 Autonomous Development Loop

用户任务 → 规划 → 代码修改 → 自动测试 → 错误分析 → 自动修复 → 重新测试 → 完成。

新增模块：

```text
autonomous/
├── executor.py
├── test_runner.py
├── error_analyzer.py
├── repair_agent.py
└── loop_controller.py
```

测试类型：Python(pytest) → ROS2(colcon test) → 自定义工程测试脚本。

完成标准：自动运行测试、读取错误、生成修复方案、自动重试、最大循环限制、失败保存现场。

## v3.1 Project Long-term Memory

让 AI 记住项目历史，从资料查询升级为项目经验记忆。

```text
memory/
├── project_memory
├── decision_memory
├── failure_memory
└── experience_memory
```

保存设计决策、Bug 经验、工程经验，使 AI 能回答：

- 为什么这样设计？
- 以前遇到过类似问题吗？
- 修改这个模块有什么影响？

## v3.2 Code Intelligence System

增强大型项目理解，建立代码知识图谱。

```text
code_graph/
├── parser.py
├── dependency_graph.py
├── impact_analysis.py
└── code_index.py
```

分析文件、函数、类、调用关系、依赖关系，支持影响分析和调用点查询。

## v3.3 Experiment Agent

服务科研开发，适合 AI-Robot-Demo、论文实验、算法验证。

```text
experiment/
├── experiment_agent.py
├── parameter_manager.py
├── result_collector.py
└── report_generator.py
```

流程：设计实验 → 生成配置 → 运行程序 → 保存结果 → 生成图表 → 生成报告。

## v3.4 Project AI Team

每个项目拥有独立 AI 团队。

```text
project_agents/
├── team_config.yaml
├── role_manager.py
└── project_agent_loader.py
```

示例：

- AI-Robot-Demo：Robot Architect / ROS2 Developer / Control Algorithm / Simulation / Test
- InduAgent：PLC Expert / RAG Engineer / Knowledge / Backend / Test

## v4.0 Personal AI Research Platform

用户只需提出研究方向，系统自动完成：查资料 → 设计方案 → 修改代码 → 做实验 → 分析结果 → 生成报告。

## 开发原则

不无限增加 Agent 数量，重点放在：

1. 自动闭环
2. 项目记忆
3. 工程理解
4. 科研能力

## 阶段建议

v2.5 完成后先冻结平台开发一段时间，用 `codex-router` 推进 AI-Robot-Demo 与 InduAgent；v3.0 的自动测试闭环比继续增加 Agent 更有工程价值。
