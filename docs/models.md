# 模型

Agents SDK 默认支持两种类型的 OpenAI 模型：

-   **推荐使用**：[`OpenAIResponsesModel`][agents.models.openai_responses.OpenAIResponsesModel]，该模型通过全新的 [Responses API](https://platform.openai.com/docs/api-reference/responses) 调用 OpenAI 接口。
-   [`OpenAIChatCompletionsModel`][agents.models.openai_chatcompletions.OpenAIChatCompletionsModel]，该模型通过 [Chat Completions API](https://platform.openai.com/docs/api-reference/chat) 调用 OpenAI 接口。

## 混合搭配模型

在单个工作流中，您可能希望为不同智能体使用不同模型。例如，可以使用更小更快的模型进行初步筛选，而使用更强大模型处理复杂任务。配置 [`Agent`][agents.Agent] 时，可通过以下方式选择特定模型：

1. 直接传入 OpenAI 模型名称
2. 传入任意模型名称 + 能够将该名称映射到 Model 实例的 [`ModelProvider`][agents.models.interface.ModelProvider]
3. 直接提供 [`Model`][agents.models.interface.Model] 实现

!!!注意

    虽然 SDK 同时支持 [`OpenAIResponsesModel`][agents.models.openai_responses.OpenAIResponsesModel] 和 [`OpenAIChatCompletionsModel`][agents.models.openai_chatcompletions.OpenAIChatCompletionsModel] 两种形态，但我们建议每个工作流使用单一模型形态，因为二者支持的功能和工具集不同。若工作流必须混用模型形态，请确保所需功能在两种形态下均可用。

```python
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
import asyncio

spanish_agent = Agent(
    name="Spanish agent",
    instructions="You only speak Spanish.",
    model="o3-mini", # (1)!
)

english_agent = Agent(
    name="English agent",
    instructions="You only speak English",
    model=OpenAIChatCompletionsModel( # (2)!
        model="gpt-4o",
        openai_client=AsyncOpenAI()
    ),
)

triage_agent = Agent(
    name="Triage agent",
    instructions="Handoff to the appropriate agent based on the language of the request.",
    handoffs=[spanish_agent, english_agent],
    model="gpt-3.5-turbo",
)

async def main():
    result = await Runner.run(triage_agent, input="Hola, ¿cómo estás?")
    print(result.final_output)
```

1. 直接设置 OpenAI 模型名称
2. 提供 [`Model`][agents.models.interface.Model] 实现

如需进一步配置智能体使用的模型，可传入 [`ModelSettings`][agents.models.interface.ModelSettings]，该设置包含温度值等可选模型配置参数。

```python
from agents import Agent, ModelSettings

english_agent = Agent(
    name="English agent",
    instructions="You only speak English",
    model="gpt-4o",
    model_settings=ModelSettings(temperature=0.1),
)
```

## 使用其他大模型供应商

可通过三种方式使用其他大模型供应商（示例参见[此处](https://github.com/agentdevhub/OpenAI-Agent-SDK/tree/main/examples/model_providers/)）：

1. [`set_default_openai_client`][agents.set_default_openai_client] 适用于全局使用 `AsyncOpenAI` 实例作为大模型客户端的情况。当供应商提供与 OpenAI 兼容的 API 端点时，可通过该方法设置 `base_url` 和 `api_key`。可配置示例见 [examples/model_providers/custom_example_global.py](https://github.com/agentdevhub/OpenAI-Agent-SDK/tree/main/examples/model_providers/custom_example_global.py)
2. [`ModelProvider`][agents.models.interface.ModelProvider] 作用于 `Runner.run` 层级。该方法可实现"为本次运行中的所有智能体使用自定义模型供应商"。可配置示例见 [examples/model_providers/custom_example_provider.py](https://github.com/agentdevhub/OpenAI-Agent-SDK/tree/main/examples/model_providers/custom_example_provider.py)
3. [`Agent.model`][agents.agent.Agent.model] 可为特定智能体实例指定模型。该方法支持为不同智能体混用不同供应商。可配置示例见 [examples/model_providers/custom_example_agent.py](https://github.com/agentdevhub/OpenAI-Agent-SDK/tree/main/examples/model_providers/custom_example_agent.py)

若未持有 `platform.openai.com` 的 API 密钥，建议通过 `set_tracing_disabled()` 禁用追踪功能，或设置[其他追踪处理器](tracing.md)。

!!! 注意

    这些示例中使用的是 Chat Completions API/模型，因为目前大多数大模型供应商尚未支持 Responses API。若您的供应商已支持该 API，我们推荐使用 Responses 方案。

## 使用其他大模型供应商的常见问题

### 追踪客户端报错 401

若出现与追踪功能相关的错误，通常是因为追踪数据需上传至 OpenAI 服务器，而您未持有 OpenAI API 密钥。可通过以下三种方式解决：

1. 完全禁用追踪功能：[`set_tracing_disabled(True)`][agents.set_tracing_disabled]
2. 为追踪功能设置 OpenAI 密钥：[`set_tracing_export_api_key(...)`][agents.set_tracing_export_api_key]。该密钥仅用于上传追踪数据，且必须来自 [platform.openai.com](https://platform.openai.com/)
3. 使用非 OpenAI 的追踪处理器。详见[追踪文档](tracing.md#custom-tracing-processors)

### Responses API 支持问题

SDK 默认使用 Responses API，但多数大模型供应商尚未支持该接口。您可能会遇到 404 等类似问题。解决方案如下：

1. 调用 [`set_default_openai_api("chat_completions")`][agents.set_default_openai_api]。该方法适用于通过环境变量设置 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL` 的情况
2. 使用 [`OpenAIChatCompletionsModel`][agents.models.openai_chatcompletions.OpenAIChatCompletionsModel]。示例参见[此处](https://github.com/agentdevhub/OpenAI-Agent-SDK/tree/main/examples/model_providers/)

### 结构化输出支持问题

部分模型供应商不支持[结构化输出](https://platform.openai.com/docs/guides/structured-outputs)。此时可能会遇到如下错误：

```
BadRequestError: Error code: 400 - {'error': {'message': "'response_format.type' : value is not one of the allowed values ['text','json_object']", 'type': 'invalid_request_error'}}
```

这是某些供应商的局限性——它们支持 JSON 输出，但不允许指定输出使用的 `json_schema`。我们正在修复该问题，但建议优先选择支持 JSON 模式输出的供应商，否则应用常会因格式错误的 JSON 而中断。