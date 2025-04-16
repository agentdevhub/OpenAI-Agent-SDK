# 追踪功能

Agents SDK 内置了追踪功能，能够全面记录智能体运行期间的所有事件：包括大模型生成内容、工具调用、交接流程、防护机制触发以及自定义事件等。通过 [Traces 控制面板](https://platform.openai.com/traces)，您可以在开发和生产环境中调试、可视化监控工作流程。

!!!注意

    追踪功能默认启用。如需禁用可通过以下两种方式：

    1. 通过设置环境变量 `OPENAI_AGENTS_DISABLE_TRACING=1` 全局关闭追踪功能
    2. 针对单次运行禁用追踪：将 [`agents.run.RunConfig.tracing_disabled`][] 设为 `True`

***对于使用 OpenAI API 并执行零数据保留（ZDR）政策的组织，追踪功能不可用。***

## 追踪与跨度

-   **Traces（追踪记录）** 表示一个完整"工作流"的端到端操作，由多个 Span 组成。追踪记录包含以下属性：
    -   `workflow_name`：表示逻辑工作流或应用名称，例如"代码生成"或"客户服务"
    -   `trace_id`：追踪记录的唯一标识符。若未提供将自动生成，必须符合 `trace_<32_alphanumeric>` 格式
    -   `group_id`：可选分组 ID，用于关联同一会话中的多个追踪记录（例如聊天线程 ID）
    -   `disabled`：若为 True，则该追踪记录不会被保存
    -   `metadata`：追踪记录的元数据（可选）
-   **Spans（跨度）** 表示具有起止时间的操作单元。跨度包含：
    -   `started_at` 和 `ended_at` 时间戳
    -   所属追踪记录的 `trace_id`
    -   指向父级跨度的 `parent_id`（如存在）
    -   记录跨度详情的 `span_data`。例如 `AgentSpanData` 包含智能体信息，`GenerationSpanData` 包含大模型生成信息等

## 默认追踪项

SDK 默认追踪以下内容：

-   整个 `Runner.{run, run_sync, run_streamed}()` 会被包裹在 `trace()` 中
-   每次智能体运行时会被包裹在 `agent_span()`
-   大模型生成内容会被包裹在 `generation_span()`
-   函数工具调用会被分别包裹在 `function_span()`
-   防护机制触发会被包裹在 `guardrail_span()`
-   交接流程会被包裹在 `handoff_span()`
-   语音输入（语音转文字）会被包裹在 `transcription_span()`
-   语音输出（文字转语音）会被包裹在 `speech_span()`
-   相关音频跨度可能归属于同一个 `speech_group_span()`

默认追踪记录命名为"Agent trace"。使用 `trace` 可自定义名称，或通过 [`RunConfig`][agents.run.RunConfig] 配置名称及其他属性。

此外，您可以设置 [自定义追踪处理器](#custom-tracing-processors) 将追踪数据推送至其他目标（作为替代或补充存储）。

## 高阶追踪

若需将多次 `run()` 调用归入同一条追踪记录，可使用 `trace()` 包裹相关代码。

```python
from agents import Agent, Runner, trace

async def main():
    agent = Agent(name="Joke generator", instructions="Tell funny jokes.")

    with trace("Joke workflow"): # (1)!
        first_result = await Runner.run(agent, "Tell me a joke")
        second_result = await Runner.run(agent, f"Rate this joke: {first_result.final_output}")
        print(f"Joke: {first_result.final_output}")
        print(f"Rating: {second_result.final_output}")
```

1. 由于两次 `Runner.run` 调用被包裹在 `with trace()` 中，这些独立运行将被整合到总体追踪记录而非创建两条独立记录。

## 创建追踪记录

使用 [`trace()`][agents.tracing.trace] 函数可创建追踪记录。追踪记录需要显式启停，有两种操作方式：

1. **推荐方案**：将追踪记录作为上下文管理器使用（即 `with trace(...) as my_trace`），系统会自动在适当时机启停
2. 也可手动调用 [`trace.start()`][agents.tracing.Trace.start] 和 [`trace.finish()`][agents.tracing.Trace.finish]

当前追踪记录通过 Python 的 [`contextvar`](https://docs.python.org/3/library/contextvars.html) 实现状态跟踪，天然支持并发场景。若手动启停追踪记录，需向 `start()`/`finish()` 传递 `mark_as_current` 和 `reset_current` 参数来更新当前追踪状态。

## 创建跨度

通过各类 [`*_span()`][agents.tracing.create] 方法可创建跨度。通常无需手动创建，系统提供 [`custom_span()`][agents.tracing.custom_span] 函数用于跟踪自定义跨度信息。

跨度自动归属于当前追踪记录，并嵌套在最近的当前跨度下，其层级关系通过 Python 的 [`contextvar`](https://docs.python.org/3/library/contextvars.html) 实现跟踪。

## 敏感数据处理

部分跨度可能捕获敏感数据：

`generation_span()` 存储大模型生成内容的输入输出，`function_span()` 存储函数调用的输入输出。这些数据可能包含敏感信息，可通过 [`RunConfig.trace_include_sensitive_data`][agents.run.RunConfig.trace_include_sensitive_data] 禁用采集。

同理，音频跨度默认包含输入输出音频的 base64 编码 PCM 数据，可通过配置 [`VoicePipelineConfig.trace_include_sensitive_audio_data`][agents.voice.pipeline_config.VoicePipelineConfig.trace_include_sensitive_audio_data] 禁用音频数据采集。

## 自定义追踪处理器

追踪功能的顶层架构如下：

-   初始化时创建全局 [`TraceProvider`][agents.tracing.setup.TraceProvider] 负责生成追踪记录
-   为 `TraceProvider` 配置 [`BatchTraceProcessor`][agents.tracing.processors.BatchTraceProcessor]，通过 [`BackendSpanExporter`][agents.tracing.processors.BackendSpanExporter] 将追踪记录/跨度批量发送至 OpenAI 后端

如需定制该默认配置（例如发送到其他后端或修改导出行为），有两种方案：

1. [`add_trace_processor()`][agents.tracing.add_trace_processor] 可添加**额外**的追踪处理器，在数据就绪时接收追踪信息（不影响向 OpenAI 后端发送数据）
2. [`set_trace_processors()`][agents.tracing.set_trace_processors] 可**替换**默认处理器（除非包含 `TracingProcessor` 处理器，否则不会向 OpenAI 后端发送数据）

## 第三方追踪处理器列表

-   [Weights & Biases](https://weave-docs.wandb.ai/guides/integrations/openai_agents)
-   [Arize-Phoenix](https://docs.arize.com/phoenix/tracing/integrations-tracing/openai-agents-sdk)
-   [MLflow（自托管/开源版）](https://mlflow.org/docs/latest/tracing/integrations/openai-agent)
-   [MLflow（Databricks 托管版）](https://docs.databricks.com/aws/en/mlflow/mlflow-tracing#-automatic-tracing)
-   [Braintrust](https://braintrust.dev/docs/guides/traces/integrations#openai-agents-sdk)
-   [Pydantic Logfire](https://logfire.pydantic.dev/docs/integrations/llms/openai/#openai-agents)
-   [AgentOps](https://docs.agentops.ai/v1/integrations/agentssdk)
-   [Scorecard](https://docs.scorecard.io/docs/documentation/features/tracing#openai-agents-sdk-integration)
-   [Keywords AI](https://docs.keywordsai.co/integration/development-frameworks/openai-agent)
-   [LangSmith](https://docs.smith.langchain.com/observability/how_to_guides/trace_with_openai_agents_sdk)
-   [Maxim AI](https://www.getmaxim.ai/docs/observe/integrations/openai-agents-sdk)
-   [Comet Opik](https://www.comet.com/docs/opik/tracing/integrations/openai_agents)
-   [Langfuse](https://langfuse.com/docs/integrations/openaiagentssdk/openai-agents)
-   [Langtrace](https://docs.langtrace.ai/supported-integrations/llm-frameworks/openai-agents-sdk)
-   [Okahu-Monocle](https://github.com/monocle2ai/monocle)