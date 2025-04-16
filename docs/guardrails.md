# 防护机制

防护机制与您的智能体_并行运行_，使您能够对用户输入进行检查和验证。例如，假设您有一个使用非常智能（因此速度慢/成本高）的大模型来处理客户请求的智能体。您肯定不希望恶意用户要求该模型帮他们解答数学作业。这时，您可以通过一个快速/廉价的模型运行防护机制。如果防护机制检测到恶意使用行为，它可以立即触发错误，从而阻止昂贵模型的运行，为您节省时间和成本。

防护机制分为两种类型：

1. 输入防护机制：在初始用户输入时运行
2. 输出防护机制：在最终智能体输出时运行

## 输入防护机制

输入防护机制分三步运行：

1. 首先，防护机制接收与传递给智能体相同的输入
2. 接着，防护函数运行并生成一个[`GuardrailFunctionOutput`][agents.guardrail.GuardrailFunctionOutput]，随后被封装到[`InputGuardrailResult`][agents.guardrail.InputGuardrailResult]中
3. 最后，我们检查[`.tripwire_triggered`][agents.guardrail.GuardrailFunctionOutput.tripwire_triggered]是否为true。如果为true，则触发[`InputGuardrailTripwireTriggered`][agents.exceptions.InputGuardrailTripwireTriggered]异常，以便您能适应用户或处理异常

!!! 注意  
    输入防护机制设计用于处理用户输入，因此只有当智能体是_第一个_智能体时才会运行其防护机制。您可能会疑惑，为什么`guardrails`属性设置在智能体上而不是传递给`Runner.run`？这是因为防护机制通常与实际智能体相关——不同的智能体会运行不同的防护机制，因此将代码放在一起有助于提高可读性。

## 输出防护机制

输出防护机制分三步运行：

1. 首先，防护机制接收与传递给智能体相同的输入
2. 接着，防护函数运行并生成一个[`GuardrailFunctionOutput`][agents.guardrail.GuardrailFunctionOutput]，随后被封装到[`OutputGuardrailResult`][agents.guardrail.OutputGuardrailResult]中
3. 最后，我们检查[`.tripwire_triggered`][agents.guardrail.GuardrailFunctionOutput.tripwire_triggered]是否为true。如果为true，则触发[`OutputGuardrailTripwireTriggered`][agents.exceptions.OutputGuardrailTripwireTriggered]异常，以便您能适应用户或处理异常

!!! 注意  
    输出防护机制设计用于处理最终智能体输出，因此只有当智能体是_最后一个_智能体时才会运行其防护机制。与输入防护机制类似，我们这样做是因为防护机制通常与实际智能体相关——不同的智能体会运行不同的防护机制，因此将代码放在一起有助于提高可读性。

## 触发机制

如果输入或输出未通过防护机制检查，防护机制可以通过触发机制发出信号。一旦我们发现某个防护机制触发了触发机制，就会立即引发`{Input,Output}GuardrailTripwireTriggered`异常并停止智能体执行。

## 实现防护机制

您需要提供一个接收输入并返回[`GuardrailFunctionOutput`][agents.guardrail.GuardrailFunctionOutput]的函数。在以下示例中，我们将通过底层运行一个智能体来实现这一点。

```python
from pydantic import BaseModel
from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)

class MathHomeworkOutput(BaseModel):
    is_math_homework: bool
    reasoning: str

guardrail_agent = Agent( # (1)!
    name="Guardrail check",
    instructions="Check if the user is asking you to do their math homework.",
    output_type=MathHomeworkOutput,
)


@input_guardrail
async def math_guardrail( # (2)!
    ctx: RunContextWrapper[None], agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, input, context=ctx.context)

    return GuardrailFunctionOutput(
        output_info=result.final_output, # (3)!
        tripwire_triggered=result.final_output.is_math_homework,
    )


agent = Agent(  # (4)!
    name="Customer support agent",
    instructions="You are a customer support agent. You help customers with their questions.",
    input_guardrails=[math_guardrail],
)

async def main():
    # This should trip the guardrail
    try:
        await Runner.run(agent, "Hello, can you help me solve for x: 2x + 3 = 11?")
        print("Guardrail didn't trip - this is unexpected")

    except InputGuardrailTripwireTriggered:
        print("Math homework guardrail tripped")
```

1. 我们将在防护函数中使用此智能体
2. 这是接收智能体输入/上下文并返回结果的防护函数
3. 我们可以在防护结果中包含额外信息
4. 这是定义工作流程的实际智能体

输出防护机制的实现类似。

```python
from pydantic import BaseModel
from agents import (
    Agent,
    GuardrailFunctionOutput,
    OutputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    output_guardrail,
)
class MessageOutput(BaseModel): # (1)!
    response: str

class MathOutput(BaseModel): # (2)!
    reasoning: str
    is_math: bool

guardrail_agent = Agent(
    name="Guardrail check",
    instructions="Check if the output includes any math.",
    output_type=MathOutput,
)

@output_guardrail
async def math_guardrail(  # (3)!
    ctx: RunContextWrapper, agent: Agent, output: MessageOutput
) -> GuardrailFunctionOutput:
    result = await Runner.run(guardrail_agent, output.response, context=ctx.context)

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_math,
    )

agent = Agent( # (4)!
    name="Customer support agent",
    instructions="You are a customer support agent. You help customers with their questions.",
    output_guardrails=[math_guardrail],
    output_type=MessageOutput,
)

async def main():
    # This should trip the guardrail
    try:
        await Runner.run(agent, "Hello, can you help me solve for x: 2x + 3 = 11?")
        print("Guardrail didn't trip - this is unexpected")

    except OutputGuardrailTripwireTriggered:
        print("Math output guardrail tripped")
```

1. 这是实际智能体的输出类型
2. 这是防护机制的输出类型
3. 这是接收智能体输出并返回结果的防护函数
4. 这是定义工作流程的实际智能体