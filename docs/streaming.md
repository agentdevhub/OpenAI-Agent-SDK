# 流式传输

流式传输功能允许您在智能体运行过程中实时订阅更新状态。这一特性非常适合向终端用户展示进度更新和部分响应结果。

要实现流式传输，您可以调用 [`Runner.run_streamed()`][agents.run.Runner.run_streamed] 方法，该方法会返回一个 [`RunResultStreaming`][agents.result.RunResultStreaming] 对象。调用 `result.stream_events()` 将获得 [`StreamEvent`][agents.stream_events.StreamEvent] 对象的异步流，具体事件类型说明如下。

## 原始响应事件

[`RawResponsesStreamEvent`][agents.stream_events.RawResponsesStreamEvent] 是从大模型直接传递的原始事件，采用 OpenAI Responses API 格式。每个事件都包含类型（如 `response.created`、`response.output_text.delta` 等）和数据字段。如果您希望在大模型生成响应时立即将消息流式传输给用户，这类事件非常有用。

例如，以下代码可以逐令牌输出大模型生成的文本：

```python
import asyncio
from openai.types.responses import ResponseTextDeltaEvent
from agents import Agent, Runner

async def main():
    agent = Agent(
        name="Joker",
        instructions="You are a helpful assistant.",
    )

    result = Runner.run_streamed(agent, input="Please tell me 5 jokes.")
    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            print(event.data.delta, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
```

## 运行项事件与智能体事件

[`RunItemStreamEvent`][agents.stream_events.RunItemStreamEvent] 属于更高层级的事件，会在某个项目完全生成时发出通知。通过这类事件，您可以按"消息已生成"、"工具已运行"等粒度推送进度更新，而非逐令牌更新。类似的，[`AgentUpdatedStreamEvent`][agents.stream_events.AgentUpdatedStreamEvent] 会在当前智能体发生变化时（例如发生控制权移交）提供更新通知。

例如，以下代码会忽略原始事件，仅向用户流式传输更新内容：

```python
import asyncio
import random
from agents import Agent, ItemHelpers, Runner, function_tool

@function_tool
def how_many_jokes() -> int:
    return random.randint(1, 10)


async def main():
    agent = Agent(
        name="Joker",
        instructions="First call the `how_many_jokes` tool, then tell that many jokes.",
        tools=[how_many_jokes],
    )

    result = Runner.run_streamed(
        agent,
        input="Hello",
    )
    print("=== Run starting ===")

    async for event in result.stream_events():
        # We'll ignore the raw responses event deltas
        if event.type == "raw_response_event":
            continue
        # When the agent updates, print that
        elif event.type == "agent_updated_stream_event":
            print(f"Agent updated: {event.new_agent.name}")
            continue
        # When items are generated, print them
        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                print("-- Tool was called")
            elif event.item.type == "tool_call_output_item":
                print(f"-- Tool output: {event.item.output}")
            elif event.item.type == "message_output_item":
                print(f"-- Message output:\n {ItemHelpers.text_message_output(event.item)}")
            else:
                pass  # Ignore other event types

    print("=== Run complete ===")


if __name__ == "__main__":
    asyncio.run(main())
```