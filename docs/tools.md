# 工具集

工具让智能体能够执行各类操作：包括获取数据、运行代码、调用外部API，甚至操作计算机。Agent SDK 提供三类工具：

-   **托管工具**：这些工具与大模型一同运行在LLM服务器上。OpenAI提供的托管工具包括信息检索、网络搜索和计算机操作。
-   **函数调用工具**：允许将任意Python函数转化为工具使用。
-   **智能体工具化**：可将智能体作为工具调用，实现智能体间的相互调用而无需移交控制权。

## 托管工具

使用[`OpenAIResponsesModel`][agents.models.openai_responses.OpenAIResponsesModel]时，OpenAI提供以下内置工具：

-   [`WebSearchTool`][agents.tool.WebSearchTool]：支持智能体执行网络搜索
-   [`FileSearchTool`][agents.tool.FileSearchTool]：支持从OpenAI向量数据库检索信息
-   [`ComputerTool`][agents.tool.ComputerTool]：支持自动化计算机操作任务

```python
from agents import Agent, FileSearchTool, Runner, WebSearchTool

agent = Agent(
    name="Assistant",
    tools=[
        WebSearchTool(),
        FileSearchTool(
            max_num_results=3,
            vector_store_ids=["VECTOR_STORE_ID"],
        ),
    ],
)

async def main():
    result = await Runner.run(agent, "Which coffee shop should I go to, taking into account my preferences and the weather today in SF?")
    print(result.final_output)
```

## 函数工具

可将任意Python函数转化为工具，Agent SDK会自动完成工具配置：

-  工具名称默认使用函数名（支持自定义）
-  工具描述自动取自函数文档字符串（支持自定义）
-  根据函数参数自动生成输入参数结构
-  各参数描述默认取自函数文档字符串（可禁用）

我们使用Python的`inspect`模块提取函数签名，配合[`griffe`](https://mkdocstrings.github.io/griffe/)解析文档字符串，以及`pydantic`生成参数结构。

```python
import json

from typing_extensions import TypedDict, Any

from agents import Agent, FunctionTool, RunContextWrapper, function_tool


class Location(TypedDict):
    lat: float
    long: float

@function_tool  # (1)!
async def fetch_weather(location: Location) -> str:
    # (2)!
    """Fetch the weather for a given location.

    Args:
        location: The location to fetch the weather for.
    """
    # In real life, we'd fetch the weather from a weather API
    return "sunny"


@function_tool(name_override="fetch_data")  # (3)!
def read_file(ctx: RunContextWrapper[Any], path: str, directory: str | None = None) -> str:
    """Read the contents of a file.

    Args:
        path: The path to the file to read.
        directory: The directory to read the file from.
    """
    # In real life, we'd read the file from the file system
    return "<file contents>"


agent = Agent(
    name="Assistant",
    tools=[fetch_weather, read_file],  # (4)!
)

for tool in agent.tools:
    if isinstance(tool, FunctionTool):
        print(tool.name)
        print(tool.description)
        print(json.dumps(tool.params_json_schema, indent=2))
        print()

```

1.  函数参数支持任意Python类型，函数本身支持同步/异步
2.  若存在文档字符串，将自动提取工具描述和参数说明
3.  函数可选择接收`context`参数（必须作为首个参数）。同时支持覆盖配置项，如工具名称、描述、文档字符串风格等
4.  经装饰器处理的函数可直接传入工具列表

??? note "展开查看输出示例"

    ```
    fetch_weather
    获取指定位置的天气信息
    {
    "$defs": {
      "Location": {
        "properties": {
          "lat": {
            "title": "Lat",
            "type": "number"
          },
          "long": {
            "title": "Long",
            "type": "number"
          }
        },
        "required": [
          "lat",
          "long"
        ],
        "title": "Location",
        "type": "object"
      }
    },
    "properties": {
      "location": {
        "$ref": "#/$defs/Location",
        "description": "需要查询天气的地理位置"
      }
    },
    "required": [
      "location"
    ],
    "title": "fetch_weather_args",
    "type": "object"
    }

    fetch_data
    读取文件内容
    {
    "properties": {
      "path": {
        "description": "待读取文件的路径",
        "title": "Path",
        "type": "string"
      },
      "directory": {
        "anyOf": [
          {
            "type": "string"
          },
          {
            "type": "null"
          }
        ],
        "default": null,
        "description": "文件所在目录",
        "title": "Directory"
      }
    },
    "required": [
      "path"
    ],
    "title": "fetch_data_args",
    "type": "object"
    }
    ```

### 自定义函数工具

若不希望直接使用Python函数，可手动创建[`FunctionTool`][agents.tool.FunctionTool]，需提供以下要素：

-   `name`
-   `description`
-   `params_json_schema`（参数的JSON结构定义）
-   `on_invoke_tool`（异步执行函数，接收上下文和JSON格式参数，返回字符串格式结果）

```python
from typing import Any

from pydantic import BaseModel

from agents import RunContextWrapper, FunctionTool



def do_some_work(data: str) -> str:
    return "done"


class FunctionArgs(BaseModel):
    username: str
    age: int


async def run_function(ctx: RunContextWrapper[Any], args: str) -> str:
    parsed = FunctionArgs.model_validate_json(args)
    return do_some_work(data=f"{parsed.username} is {parsed.age} years old")


tool = FunctionTool(
    name="process_user",
    description="Processes extracted user data",
    params_json_schema=FunctionArgs.model_json_schema(),
    on_invoke_tool=run_function,
)
```

### 自动参数与文档解析

如前所述，系统会自动解析函数签名生成工具结构，并通过文档字符串提取描述信息。注意事项：

1. 签名解析通过`inspect`模块实现，利用类型注解推断参数类型，并动态构建Pydantic模型。支持Python原生类型、Pydantic模型、TypedDict等多种类型。
2. 使用`griffe`解析文档字符串，支持`google`、`sphinx`和`numpy`格式。系统会自动检测格式（可能不准确），也可通过`function_tool`显式指定。设置`use_docstring_info`为`False`可禁用文档解析。

结构提取代码详见[`agents.function_schema`][]。

## 智能体工具化

在某些工作流中，可能需要中心智能体协调多个专业智能体（而非移交控制权）。此时可将智能体建模为工具使用。

```python
from agents import Agent, Runner
import asyncio

spanish_agent = Agent(
    name="Spanish agent",
    instructions="You translate the user's message to Spanish",
)

french_agent = Agent(
    name="French agent",
    instructions="You translate the user's message to French",
)

orchestrator_agent = Agent(
    name="orchestrator_agent",
    instructions=(
        "You are a translation agent. You use the tools given to you to translate."
        "If asked for multiple translations, you call the relevant tools."
    ),
    tools=[
        spanish_agent.as_tool(
            tool_name="translate_to_spanish",
            tool_description="Translate the user's message to Spanish",
        ),
        french_agent.as_tool(
            tool_name="translate_to_french",
            tool_description="Translate the user's message to French",
        ),
    ],
)

async def main():
    result = await Runner.run(orchestrator_agent, input="Say 'Hello, how are you?' in Spanish.")
    print(result.final_output)
```

## 函数工具错误处理

通过`@function_tool`创建函数工具时，可传入`failure_error_function`参数。该函数用于在工具调用失败时向大模型返回错误响应：

-  默认情况下（未传参时），执行`default_tool_error_function`向大模型返回通用错误信息
-  传入自定义函数时，将执行该函数并返回响应
-  显式传入`None`时，所有工具调用错误将重新抛出。可能是模型生成无效JSON导致的`ModelBehaviorError`，或代码执行触发的`UserError`等

若手动创建`FunctionTool`对象，则需在`on_invoke_tool`函数内自行处理错误。