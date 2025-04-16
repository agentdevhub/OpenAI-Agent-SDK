# SDK配置指南

## API密钥与客户端配置

默认情况下，SDK在导入时会自动检查`OPENAI_API_KEY`环境变量以获取大模型请求和追踪所需的密钥。若无法在应用启动前设置该环境变量，可使用[set_default_openai_key()][agents.set_default_openai_key]函数进行密钥配置。

```python
from agents import set_default_openai_key

set_default_openai_key("sk-...")
```

您也可以配置自定义的OpenAI客户端。SDK默认会基于环境变量或上述预设密钥创建`AsyncOpenAI`实例，如需修改此行为，请使用[set_default_openai_client()][agents.set_default_openai_client]函数。

```python
from openai import AsyncOpenAI
from agents import set_default_openai_client

custom_client = AsyncOpenAI(base_url="...", api_key="...")
set_default_openai_client(custom_client)
```

此外，您还可以自定义使用的OpenAI API类型。默认采用OpenAI Responses API，如需切换至Chat Completions API，请调用[set_default_openai_api()][agents.set_default_openai_api]函数。

```python
from agents import set_default_openai_api

set_default_openai_api("chat_completions")
```

## 追踪功能配置

追踪功能默认启用，其默认使用前文所述的OpenAI API密钥（即环境变量或预设密钥）。如需单独设置追踪功能的API密钥，请使用[`set_tracing_export_api_key`][agents.set_tracing_export_api_key]函数。

```python
from agents import set_tracing_export_api_key

set_tracing_export_api_key("sk-...")
```

如需完全禁用追踪功能，可调用[`set_tracing_disabled()`][agents.set_tracing_disabled]函数。

```python
from agents import set_tracing_disabled

set_tracing_disabled(True)
```

## 调试日志配置

SDK内置两个未配置处理器的Python日志记录器。默认情况下，仅警告和错误信息会输出至`stdout`，其他日志将被抑制。

如需启用详细日志输出，请使用[`enable_verbose_stdout_logging()`][agents.enable_verbose_stdout_logging]函数。

```python
from agents import enable_verbose_stdout_logging

enable_verbose_stdout_logging()
```

您也可以通过添加处理器、过滤器、格式化器等自定义日志行为，更多细节请参阅[Python日志指南](https://docs.python.org/3/howto/logging.html)。

```python
import logging

logger = logging.getLogger("openai.agents") # or openai.agents.tracing for the Tracing logger

# To make all logs show up
logger.setLevel(logging.DEBUG)
# To make info and above show up
logger.setLevel(logging.INFO)
# To make warning and above show up
logger.setLevel(logging.WARNING)
# etc

# You can customize this as needed, but this will output to `stderr` by default
logger.addHandler(logging.StreamHandler())
```

### 日志中的敏感数据

部分日志可能包含敏感信息（例如用户数据）。如需禁用此类数据记录，请设置以下环境变量：

禁用大模型输入输出日志记录：
```bash
export OPENAI_AGENTS_DONT_LOG_MODEL_DATA=1
```

禁用工具输入输出日志记录：
```bash
export OPENAI_AGENTS_DONT_LOG_TOOL_DATA=1
```