# 运行智能体

您可以通过[`Runner`][agents.run.Runner]类来运行智能体，共有三种运行方式：

1. [`Runner.run()`][agents.run.Runner.run]：异步运行方法，返回[`RunResult`][agents.result.RunResult]
2. [`Runner.run_sync()`][agents.run.Runner.run_sync]：同步运行方法，底层实际调用的是`.run()`
3. [`Runner.run_streamed()`][agents.run.Runner.run_streamed]：异步流式运行方法，返回[`RunResultStreaming`][agents.result.RunResultStreaming]。该方法以大模型流式模式调用，并实时将接收到的流事件推送给您

```python
from agents import Agent, Runner

async def main():
    agent = Agent(name="Assistant", instructions="You are a helpful assistant")

    result = await Runner.run(agent, "Write a haiku about recursion in programming.")
    print(result.final_output)
    # Code within the code,
    # Functions calling themselves,
    # Infinite loop's dance.
```

更多细节请参阅[结果指南](results.md)。

## 智能体运行循环

当使用`Runner`中的运行方法时，您需要传入初始智能体和输入参数。输入可以是字符串（视为用户消息），也可以是OpenAI Responses API中的输入项列表。

运行器会执行以下循环流程：

1. 使用当前输入调用当前智能体的大模型
2. 大模型生成输出结果：
    1. 如果返回`final_output`，则循环终止并返回最终结果
    2. 如果执行了交接（handoff），则更新当前智能体和输入参数，重新开始循环
    3. 如果产生了工具调用，则执行这些工具调用，将结果追加后重新开始循环
3. 如果超过传入的`max_turns`限制，则抛出[`MaxTurnsExceeded`][agents.exceptions.MaxTurnsExceeded]异常

!!! 注意  
    判断大模型输出是否为"最终输出"的规则是：输出符合预期类型的文本内容且不包含任何工具调用。

## 流式处理

流式运行允许您在大模型执行过程中实时接收流事件。流式处理完成后，[`RunResultStreaming`][agents.result.RunResultStreaming]会包含完整的运行信息（包括所有新生成的输出）。您可以通过`.stream_events()`获取流事件详情，详见[流式指南](streaming.md)。

## 运行配置

`run_config`参数支持配置智能体运行的全局设置：

- [`model`][agents.run.RunConfig.model]：设置全局大模型，覆盖各Agent的`model`配置
- [`model_provider`][agents.run.RunConfig.model_provider]：模型提供商（默认为OpenAI），用于查找模型名称
- [`model_settings`][agents.run.RunConfig.model_settings]：覆盖智能体特定设置，例如设置全局`temperature`或`top_p`
- [`input_guardrails`][agents.run.RunConfig.input_guardrails], [`output_guardrails`][agents.run.RunConfig.output_guardrails]：为所有运行添加输入/输出防护规则列表
- [`handoff_input_filter`][agents.run.RunConfig.handoff_input_filter]：应用于所有交接的全局输入过滤器（当交接操作本身未设置过滤器时）。该过滤器允许您编辑传递给新智能体的输入参数，详见[`Handoff.input_filter`][agents.handoffs.Handoff.input_filter]文档
- [`tracing_disabled`][agents.run.RunConfig.tracing_disabled]：禁用整个运行的[追踪功能](tracing.md)
- [`trace_include_sensitive_data`][agents.run.RunConfig.trace_include_sensitive_data]：配置追踪记录是否包含敏感数据（如大模型和工具调用的输入/输出）
- [`workflow_name`][agents.run.RunConfig.workflow_name], [`trace_id`][agents.run.RunConfig.trace_id], [`group_id`][agents.run.RunConfig.group_id]：设置运行的追踪工作流名称、追踪ID和追踪组ID。建议至少设置`workflow_name`。组ID为可选字段，用于关联多个运行的追踪记录
- [`trace_metadata`][agents.run.RunConfig.trace_metadata]：要包含在所有追踪记录中的元数据

## 对话/聊天线程

调用任何运行方法都可能涉及一个或多个智能体的执行（即多次大模型调用），但代表的是聊天对话中的单个逻辑轮次。例如：

1. 用户轮次：用户输入文本
2. 运行器执行：第一个智能体调用大模型→执行工具→交接给第二个智能体→第二个智能体执行更多工具→最终生成输出

在智能体运行结束后，您可以选择向用户展示的内容。例如可以展示智能体生成的每个新条目，或仅显示最终输出。无论采用哪种方式，用户都可能提出后续问题，此时您可以再次调用运行方法。

使用基础方法[`RunResultBase.to_input_list()`][agents.result.RunResultBase.to_input_list]可获取下一轮次的输入参数。

```python
async def main():
    agent = Agent(name="Assistant", instructions="Reply very concisely.")

    with trace(workflow_name="Conversation", group_id=thread_id):
        # First turn
        result = await Runner.run(agent, "What city is the Golden Gate Bridge in?")
        print(result.final_output)
        # San Francisco

        # Second turn
        new_input = result.to_input_list() + [{"role": "user", "content": "What state is it in?"}]
        result = await Runner.run(agent, new_input)
        print(result.final_output)
        # California
```

## 异常处理

SDK在特定情况下会抛出异常，完整列表见[`agents.exceptions`][]。主要包含：

- [`AgentsException`][agents.exceptions.AgentsException]：SDK所有异常的基类
- [`MaxTurnsExceeded`][agents.exceptions.MaxTurnsExceeded]：当运行超过run方法传入的`max_turns`时抛出
- [`ModelBehaviorError`][agents.exceptions.ModelBehaviorError]：当大模型产生无效输出时抛出（如格式错误的JSON或调用不存在的工具）
- [`UserError`][agents.exceptions.UserError]：当SDK使用者编码错误时抛出
- [`InputGuardrailTripwireTriggered`][agents.exceptions.InputGuardrailTripwireTriggered], [`OutputGuardrailTripwireTriggered`][agents.exceptions.OutputGuardrailTripwireTriggered]：当触发[防护规则](guardrails.md)时抛出