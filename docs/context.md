# 上下文管理

"Context"（上下文）是一个多义术语。在开发过程中，您可能需要关注以下两类主要上下文：

1. **代码本地上下文**：指工具函数运行时、回调函数（如`on_handoff`）执行期间、生命周期钩子等场景中所需的数据和依赖项
2. **大模型可见上下文**：指大模型生成响应时所能感知的数据

## 本地上下文

这类上下文通过[`RunContextWrapper`][agents.run_context.RunContextWrapper]类及其内部的[`context`][agents.run_context.RunContextWrapper.context]属性来实现。其工作机制如下：

1. 创建任意Python对象（常用模式是使用dataclass或Pydantic对象）
2. 将该对象传递给各种运行方法（例如`Runner.run(..., **context=whatever**))`）
3. 所有工具调用、生命周期钩子等都会接收到一个包装器对象`RunContextWrapper[T]`，其中`T`表示您可以通过`wrapper.context`访问的上下文对象类型

**最关键**的注意事项：同一代理运行过程中的所有代理、工具函数、生命周期钩子等必须使用相同类型的上下文对象。

上下文对象的典型用途包括：
- 运行业务的上下文数据（如用户名/用户ID等用户信息）
- 依赖项（如日志记录器对象、数据获取器等）
- 辅助函数

!!! danger "注意"
    上下文对象**不会**发送给大模型。它纯粹是本地对象，您可以对其进行读写操作或调用其方法。

```python
import asyncio
from dataclasses import dataclass

from agents import Agent, RunContextWrapper, Runner, function_tool

@dataclass
class UserInfo:  # (1)!
    name: str
    uid: int

@function_tool
async def fetch_user_age(wrapper: RunContextWrapper[UserInfo]) -> str:  # (2)!
    return f"User {wrapper.context.name} is 47 years old"

async def main():
    user_info = UserInfo(name="John", uid=123)

    agent = Agent[UserInfo](  # (3)!
        name="Assistant",
        tools=[fetch_user_age],
    )

    result = await Runner.run(  # (4)!
        starting_agent=agent,
        input="What is the age of the user?",
        context=user_info,
    )

    print(result.final_output)  # (5)!
    # The user John is 47 years old.

if __name__ == "__main__":
    asyncio.run(main())
```

1. 这是上下文对象示例。我们使用了dataclass，但您可以使用任意类型
2. 这是一个工具函数示例。可以看到它接收`RunContextWrapper[UserInfo]`参数，其实现会读取上下文数据
3. 我们用泛型`UserInfo`标记代理，以便类型检查器能捕获错误（例如尝试传入使用不同上下文类型的工具）
4. 上下文对象被传递给`run`函数
5. 代理正确调用工具并获取年龄信息

## 代理/大模型上下文

当调用大模型时，它**唯一**能获取的数据来自对话历史记录。这意味着如果您想让大模型感知新数据，必须通过以下方式将其加入对话历史：

1. 添加到Agent的`instructions`。这也被称为"系统提示词"或"开发者消息"。系统提示词可以是静态字符串，也可以是接收上下文并输出字符串的动态函数。这种策略适用于始终需要的信息（例如用户名或当前日期）
2. 调用`Runner.run`函数时添加到`input`。这与`instructions`策略类似，但允许您在[命令链](https://cdn.openai.com/spec/model-spec-2024-05-08.html#follow-the-chain-of-command)较低层级添加消息
3. 通过函数工具暴露。这适用于_按需获取_上下文——大模型可自主决定何时需要数据，并通过调用工具获取
4. 使用检索或网络搜索。这些特殊工具能从文件/数据库（检索）或互联网（网络搜索）获取相关数据，对于生成基于相关上下文数据的"接地气"响应非常有用