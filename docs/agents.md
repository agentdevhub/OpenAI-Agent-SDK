# 智能体（Agents）

智能体是应用程序中的核心构建模块。一个智能体就是一个配置了指令和工具的大模型（LLM）。

## 基础配置

智能体最常配置的属性包括：

-   `instructions`：也称为开发者消息或系统提示词
-   `model`：指定使用的LLM模型，以及可选的`model_settings`来配置模型调优参数（如temperature、top_p等）
-   `tools`：智能体用于完成任务的各种工具

```python
from agents import Agent, ModelSettings, function_tool

@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny"

agent = Agent(
    name="Haiku agent",
    instructions="Always respond in haiku form",
    model="o3-mini",
    tools=[get_weather],
)
```

## 上下文机制

智能体采用泛型设计处理`context`类型。上下文是一种依赖注入工具：由您创建并传递给`Runner.run()`的对象，会传递到每个智能体、工具和交接流程中，作为智能体运行的依赖项和状态集合。您可以将任何Python对象作为上下文提供。

```python
@dataclass
class UserContext:
    uid: str
    is_pro_user: bool

    async def fetch_purchases() -> list[Purchase]:
        return ...

agent = Agent[UserContext](
    ...,
)
```

## 输出类型

默认情况下，智能体生成纯文本（即`str`）输出。如需指定输出类型，可使用`output_type`参数。常见选择是使用[Pydantic](https://docs.pydantic.dev/)对象，但我们支持任何能被Pydantic的[TypeAdapter](https://docs.pydantic.dev/latest/api/type_adapter/)封装的数据类型——包括数据类、列表、TypedDict等。

```python
from pydantic import BaseModel
from agents import Agent


class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

agent = Agent(
    name="Calendar extractor",
    instructions="Extract calendar events from text",
    output_type=CalendarEvent,
)
```

!!! 注意  
    当传入`output_type`时，模型将使用[结构化输出](https://platform.openai.com/docs/guides/structured-outputs)而非常规的纯文本响应。

## 任务交接

交接流程是指智能体可以委派执行的子智能体。您提供交接列表后，智能体可在适当时选择委派执行。这种强大模式能协调模块化的专业智能体，每个智能体专精于单一任务。详见[交接流程](handoffs.md)文档。

```python
from agents import Agent

booking_agent = Agent(...)
refund_agent = Agent(...)

triage_agent = Agent(
    name="Triage agent",
    instructions=(
        "Help the user with their questions."
        "If they ask about booking, handoff to the booking agent."
        "If they ask about refunds, handoff to the refund agent."
    ),
    handoffs=[booking_agent, refund_agent],
)
```

## 动态指令

多数情况下，您可以在创建智能体时提供指令。但也可以通过函数提供动态指令——该函数接收智能体和上下文参数，必须返回提示词内容。支持常规函数和`async`函数。

```python
def dynamic_instructions(
    context: RunContextWrapper[UserContext], agent: Agent[UserContext]
) -> str:
    return f"The user's name is {context.context.name}. Help them with their questions."


agent = Agent[UserContext](
    name="Triage agent",
    instructions=dynamic_instructions,
)
```

## 生命周期事件（钩子）

有时需要观察智能体的生命周期。例如记录事件日志，或在特定事件发生时预取数据。您可以通过`hooks`属性挂接智能体生命周期。继承[`AgentHooks`][agents.lifecycle.AgentHooks]类并重写相关方法即可实现。

## 防护机制

防护机制允许在智能体运行的同时对用户输入进行检查/验证。例如筛查用户输入的相关性。详见[防护机制](guardrails.md)文档。

## 克隆/复制智能体

通过智能体的`clone()`方法，可以复制智能体并选择性修改任意属性。

```python
pirate_agent = Agent(
    name="Pirate",
    instructions="Write like a pirate",
    model="o3-mini",
)

robot_agent = pirate_agent.clone(
    name="Robot",
    instructions="Write like a robot",
)
```

## 强制工具调用

提供工具列表并不保证LLM会调用工具。您可以通过设置[`ModelSettings.tool_choice`][agents.model_settings.ModelSettings.tool_choice]强制调用，可选值包括：

1. `auto`：允许LLM自主决定是否调用工具
2. `required`：要求LLM必须调用工具（但可智能选择具体工具）
3. `none`：要求LLM不得调用工具
4. 指定具体字符串如`my_tool`：要求LLM必须调用特定工具

!!! 注意  
    为防止无限循环，框架在工具调用后会自动将`tool_choice`重置为"auto"。此行为可通过[`agent.reset_tool_choice`][agents.agent.Agent.reset_tool_choice]配置。无限循环的成因是：工具结果会传回LLM，而由于`tool_choice`设置，LLM可能再次生成工具调用，如此循环往复。

    如果希望智能体在工具调用后完全停止（而不是继续以auto模式运行），可设置[`Agent.tool_use_behavior="stop_on_first_tool"`]，这将直接把工具输出作为最终响应，不再进行后续LLM处理。