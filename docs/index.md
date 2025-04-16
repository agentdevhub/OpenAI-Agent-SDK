# OpenAI Agents SDK

[OpenAI Agents SDK](https://github.com/openai/openai-agents-python) 让您能够通过一个轻量级、易用且抽象层级极少的工具包构建智能体式 AI 应用。这是我们早期智能体实验项目 [Swarm](https://github.com/openai/swarm/tree/main) 的生产级升级版本。该 SDK 仅包含少量核心概念：

-   **智能体（Agents）**：配备指令和工具的大模型
-   **任务转交（Handoffs）**：允许智能体将特定任务委托给其他智能体
-   **防护机制（Guardrails）**：用于验证输入数据的有效性

结合 Python 使用时，这些基础组件足以表达工具与智能体之间的复杂关系，让您无需陡峭的学习曲线就能构建真实场景的应用。此外，SDK 内置**追踪功能**，可帮助您可视化调试智能体工作流，进行评估甚至为大模型进行微调。

## 为什么选择 Agents SDK

本 SDK 遵循两大设计原则：

1. 功能足够丰富且实用，同时保持核心概念精简以降低学习成本
2. 开箱即用体验优秀，同时支持深度自定义

主要功能特性包括：

-   智能体循环：内置处理工具调用、结果返回大模型及循环执行的核心逻辑
-   Python 原生：利用 Python 语言特性编排智能体链，无需学习新抽象概念
-   任务转交：实现多智能体协作与任务委派的强大功能
-   防护机制：与智能体并行执行输入验证，验证失败时提前终止
-   函数工具：将任意 Python 函数转化为工具，自动生成模式并使用 Pydantic 进行验证
-   追踪功能：内置可视化、调试和监控支持，兼容 OpenAI 的评估、微调及蒸馏工具链

## 安装指南

```bash
pip install openai-agents
```

## 入门示例

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="You are a helpful assistant")

result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
print(result.final_output)

# Code within the code,
# Functions calling themselves,
# Infinite loop's dance.
```

（运行前请确保设置 `OPENAI_API_KEY` 环境变量）

```bash
export OPENAI_API_KEY=sk-...
```