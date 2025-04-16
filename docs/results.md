# 运行结果

当您调用 `Runner.run` 方法时，您将获得以下两种结果之一：

- 若调用 `run` 或 `run_sync`，则返回 [`RunResult`][agents.result.RunResult]
- 若调用 `run_streamed`，则返回 [`RunResultStreaming`][agents.result.RunResultStreaming]

这两种结果类型均继承自 [`RunResultBase`][agents.result.RunResultBase]，该基类包含了大部分实用信息。

## 最终输出

[`final_output`][agents.result.RunResultBase.final_output] 属性包含最后执行代理的最终输出，其类型可能是：

- 若最后执行的代理未定义 `output_type`，则返回 `str`
- 若代理定义了输出类型，则返回 `last_agent.output_type` 类型的对象

!!! 注意  
    `final_output` 属于 `Any` 类型。由于存在交接(handoffs)机制，我们无法进行静态类型标注——当发生交接时，任何代理都可能成为最后一个执行的代理，因此我们无法静态预知所有可能的输出类型。

## 下一轮输入

您可以使用 [`result.to_input_list()`][agents.result.RunResultBase.to_input_list] 方法将运行结果转换为输入列表，该方法会将您提供的原始输入与代理运行期间生成的条目进行拼接。这一特性使得以下操作变得便捷：
- 将某次代理运行的输出作为另一次运行的输入
- 在循环运行时追加新的用户输入

## 最后执行的代理

[`last_agent`][agents.result.RunResultBase.last_agent] 属性记录了最后执行的代理实例。根据应用场景不同，该信息通常对处理用户下一次输入很有价值。例如：
- 当您设有前端分流代理（将任务交接给特定语言代理）时
- 可以存储最后执行的代理实例
- 下次用户发送消息时直接复用该代理

## 新增条目

[`new_items`][agents.result.RunResultBase.new_items] 属性包含运行期间生成的新条目，这些条目均为 [`RunItem`][agents.items.RunItem] 类型（封装了大模型生成的原始条目）。具体包括：

- [`MessageOutputItem`][agents.items.MessageOutputItem]：大模型生成的消息，原始条目即消息内容
- [`HandoffCallItem`][agents.items.HandoffCallItem]：大模型调用交接工具的记录，原始条目为工具调用项
- [`HandoffOutputItem`][agents.items.HandoffOutputItem]：发生代理交接的记录，原始条目为工具响应，可通过该条目获取源/目标代理
- [`ToolCallItem`][agents.items.ToolCallItem]：大模型调用工具的记录
- [`ToolCallOutputItem`][agents.items.ToolCallOutputItem]：工具调用的响应记录，可通过该条目获取工具输出
- [`ReasoningItem`][agents.items.ReasoningItem]：大模型生成的推理过程记录

## 其他信息

### 防护规则结果

[`input_guardrail_results`][agents.result.RunResultBase.input_guardrail_results] 和 [`output_guardrail_results`][agents.result.RunResultBase.output_guardrail_results] 属性包含防护规则的执行结果（如存在）。这些结果有时包含值得记录或存储的有用信息，因此我们将其开放访问。

### 原始响应

[`raw_responses`][agents.result.RunResultBase.raw_responses] 属性包含大模型生成的 [`ModelResponse`][agents.items.ModelResponse] 响应数据。

### 原始输入

[`input`][agents.result.RunResultBase.input] 属性保存了您最初传递给 `run` 方法的输入数据。虽然大多数情况下不需要直接访问，但我们仍保留该属性以备特殊需求。