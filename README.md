# OpenAI Agents SDK 中文文档

OpenAI Agents SDK 是一个轻量级但功能强大的多智能体工作流构建框架。

<img src="https://cdn.openai.com/API/docs/images/orchestration.png" alt="Agents 跟踪界面示意图" style="max-height: 803px;">

### 核心概念：

1. [**Agents（智能体）**](https://openai-agent-sdk.agentdevhub.com/agents)：配置了指令、工具、护栏和交接功能的LLM
2. [**Handoffs（交接）**](https://openai-agent-sdk.agentdevhub.com/handoffs/)：Agents SDK 用于在智能体间转移控制权的专用工具调用
3. [**Guardrails（护栏）**](https://openai-agent-sdk.agentdevhub.com/guardrails/)：可配置的输入输出安全验证机制
4. [**Tracing（跟踪）**](https://openai-agent-sdk.agentdevhub.com/tracing/)：内置的智能体运行追踪功能，支持可视化、调试和优化工作流

浏览[示例](examples)目录查看实际应用案例，详细文档请访问[官方文档](https://openai-agent-sdk.agentdevhub.com/)。

值得注意的是，本SDK[兼容](https://openai-agent-sdk.agentdevhub.com/models/)所有支持OpenAI聊天补全API格式的模型供应商。

## 快速上手

1. 配置Python环境

```bash
python -m venv env
source env/bin/activate
```

2. 安装Agents SDK

```bash
pip install openai-agents
```

如需语音支持，可使用可选`voice`组安装：`pip install 'openai-agents[voice]'`。

## Hello world 示例

```python
from agents import Agent, Runner

agent = Agent(name="Assistant", instructions="你是一个乐于助人的助手")

result = Runner.run_sync(agent, "写一首关于编程递归的俳句。")
print(result.final_output)

# 代码嵌套代码，
# 函数自我调用循环，
# 无限舞步翩跹。
```

（运行前请确保已设置`OPENAI_API_KEY`环境变量）

（Jupyter笔记本用户请参考[hello_world_jupyter.py](examples/basic/hello_world_jupyter.py)）

## 交接示例

```python
from agents import Agent, Runner
import asyncio

spanish_agent = Agent(
    name="Spanish agent",
    instructions="你只能说西班牙语。",
)

english_agent = Agent(
    name="English agent",
    instructions="你只能说英语",
)

triage_agent = Agent(
    name="Triage agent",
    instructions="根据请求语言交接给对应智能体",
    handoffs=[spanish_agent, english_agent],
)


async def main():
    result = await Runner.run(triage_agent, input="Hola, ¿cómo estás?")
    print(result.final_output)
    # ¡Hola! Estoy bien, gracias por preguntar. ¿Y tú, cómo estás?


if __name__ == "__main__":
    asyncio.run(main())
```

## 工具函数示例

```python
import asyncio

from agents import Agent, Runner, function_tool


@function_tool
def get_weather(city: str) -> str:
    return f"{city}的天气晴朗"


agent = Agent(
    name="Hello world",
    instructions="你是一个乐于助人的智能体",
    tools=[get_weather],
)


async def main():
    result = await Runner.run(agent, input="东京的天气如何？")
    print(result.final_output)
    # 东京的天气晴朗


if __name__ == "__main__":
    asyncio.run(main())
```

## 智能体循环机制

调用`Runner.run()`时，系统会持续循环直至获得最终输出：

1. 调用LLM，使用智能体配置的模型参数和消息历史
2. LLM返回响应，可能包含工具调用
3. 若响应包含最终输出（见下文说明），终止循环并返回结果
4. 若响应包含交接指令，切换当前智能体后回到步骤1
5. 处理工具调用（如有）并追加工具响应消息，然后回到步骤1

可通过`max_turns`参数限制循环次数。

### 最终输出判定

最终输出是智能体在循环结束时产生的最终结果：

1. 若智能体设置了`output_type`，当LLM返回符合该类型的结构化输出时终止。我们使用[结构化输出](https://platform.openai.com/docs/guides/structured-outputs)实现此功能
2. 若未设置`output_type`（即纯文本响应），则首个不含工具调用/交接指令的LLM响应将作为最终输出

因此，智能体循环的思维模型为：

1. 若当前智能体有`output_type`，循环持续到生成匹配该类型的结构化输出
2. 若当前智能体无`output_type`，循环持续到生成不含工具调用/交接的纯文本响应

## 常见智能体模式

Agents SDK设计高度灵活，可建模各类LLM工作流，包括确定性流程、迭代循环等。更多示例参见[`examples/agent_patterns`](examples/agent_patterns)。

## 跟踪功能

Agents SDK自动追踪智能体运行过程，便于跟踪和调试。跟踪功能可扩展设计，支持自定义span和多种外部目标平台，包括[Logfire](https://logfire.pydantic.dev/docs/integrations/llms/openai/#openai-agents)、[AgentOps](https://docs.agentops.ai/v1/integrations/agentssdk)、[Braintrust](https://braintrust.dev/docs/guides/traces/integrations#openai-agents-sdk)、[Scorecard](https://docs.scorecard.io/docs/documentation/features/tracing#openai-agents-sdk-integration)和[Keywords AI](https://docs.keywordsai.co/integration/development-frameworks/openai-agent)。关于自定义或禁用跟踪的详细说明，参见[跟踪文档](http://openai-agent-sdk.agentdevhub.com/tracing)，其中还包含[外部跟踪处理器列表](http://openai-agent-sdk.agentdevhub.com/tracing/#external-tracing-processors-list)。

## 开发指南（仅在需要修改SDK/示例时适用）

0. 确保已安装[`uv`](https://docs.astral.sh/uv/)

```bash
uv --version
```

1. 安装依赖

```bash
make sync
```

2. （修改后）执行测试

```bash
make tests  # 运行测试
make mypy   # 类型检查
make lint   # 代码规范检查
```

## 致谢

感谢开源社区的卓越贡献，特别致谢：

- [Pydantic](https://docs.pydantic.dev/latest/)（数据验证）和[PydanticAI](https://ai.pydantic.dev/)（高级智能体框架）
- [MkDocs](https://github.com/squidfunk/mkdocs-material)
- [Griffe](https://github.com/mkdocstrings/griffe)
- [uv](https://github.com/astral-sh/uv) 和 [ruff](https://github.com/astral-sh/ruff)

我们致力于将Agents SDK作为开源框架持续开发，推动社区扩展和创新。
