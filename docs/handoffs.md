# 任务转交

任务转交功能允许一个智能体将任务委托给另一个智能体。这在各智能体专攻不同领域的场景中尤为实用。例如，客户支持应用可能配置了分别处理订单状态、退款、常见问题等专项任务的智能体。

对大模型而言，任务转交以工具形式呈现。若存在向名为`Refund Agent`智能体的转交，对应工具将被命名为`transfer_to_refund_agent`。

## 创建任务转交

所有智能体都具备[`handoffs`][agents.agent.Agent.handoffs]参数，该参数可直接接收`Agent`，或接受用于定制转交行为的`Handoff`对象。

您可通过Agents SDK提供的[`handoff()`][agents.handoffs.handoff]函数创建转交。此函数支持指定目标智能体，并可选择性地配置覆盖参数和输入过滤器。

### 基础用法

以下是创建简单转交的方法：

```python
from agents import Agent, handoff

billing_agent = Agent(name="Billing agent")
refund_agent = Agent(name="Refund agent")

# (1)!
triage_agent = Agent(name="Triage agent", handoffs=[billing_agent, handoff(refund_agent)])
```

1. 您可以直接使用智能体（如`billing_agent`所示），亦可选用`handoff()`函数。

### 通过`handoff()`函数定制转交

[`handoff()`][agents.handoffs.handoff]函数支持以下定制项：

-   `agent`：指定接收转交的目标智能体
-   `tool_name_override`：默认使用`Handoff.default_tool_name()`函数（解析结果为`transfer_to_<agent_name>`），可在此处覆盖
-   `tool_description_override`：覆盖`Handoff.default_tool_description()`提供的默认工具描述
-   `on_handoff`：转交触发时执行的回调函数，适用于在确认转交后立即启动数据获取等场景。该函数接收智能体上下文，并可选择性接收大模型生成的输入（输入数据类型由`input_type`参数控制）
-   `input_type`：指定转交预期的输入类型（可选）
-   `input_filter`：用于过滤后续智能体接收的输入（详见下文）

```python
from agents import Agent, handoff, RunContextWrapper

def on_handoff(ctx: RunContextWrapper[None]):
    print("Handoff called")

agent = Agent(name="My agent")

handoff_obj = handoff(
    agent=agent,
    on_handoff=on_handoff,
    tool_name_override="custom_handoff_tool",
    tool_description_override="Custom description",
)
```

## 转交输入

某些场景下，您可能希望大模型在调用转交时提供特定数据。例如向"升级专员"转交任务时，可能需要附带转交原因以便记录。

```python
from pydantic import BaseModel

from agents import Agent, handoff, RunContextWrapper

class EscalationData(BaseModel):
    reason: str

async def on_handoff(ctx: RunContextWrapper[None], input_data: EscalationData):
    print(f"Escalation agent called with reason: {input_data.reason}")

agent = Agent(name="Escalation agent")

handoff_obj = handoff(
    agent=agent,
    on_handoff=on_handoff,
    input_type=EscalationData,
)
```

## 输入过滤器

发生转交时，新智能体将接管整个对话历史。如需修改此行为，可设置[`input_filter`][agents.handoffs.Handoff.input_filter]。输入过滤器是接收[`HandoffInputData`][agents.handoffs.HandoffInputData]现有输入的函数，必须返回新的`HandoffInputData`。

[`agents.extensions.handoff_filters`][]中已实现若干通用模式（例如清除历史记录中的所有工具调用）：

```python
from agents import Agent, handoff
from agents.extensions import handoff_filters

agent = Agent(name="FAQ agent")

handoff_obj = handoff(
    agent=agent,
    input_filter=handoff_filters.remove_all_tools, # (1)!
)
```

1. 当调用`FAQ agent`时，此配置将自动清除历史记录中的所有工具。

## 推荐提示词

为确保大模型正确理解转交机制，建议在智能体中包含转交说明。[`agents.extensions.handoff_prompt.RECOMMENDED_PROMPT_PREFIX`][]提供建议前缀模板，或调用[`agents.extensions.handoff_prompt.prompt_with_handoff_instructions`][]自动为提示词添加推荐内容。

```python
from agents import Agent
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX

billing_agent = Agent(
    name="Billing agent",
    instructions=f"""{RECOMMENDED_PROMPT_PREFIX}
    <Fill in the rest of your prompt here>.""",
)
```