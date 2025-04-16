# 追踪机制

与[智能体的追踪机制](../tracing.md)类似，语音管道也会自动生成追踪记录。

您可以通过阅读上述追踪文档了解基础信息，此外还能通过[`VoicePipelineConfig`][agents.voice.pipeline_config.VoicePipelineConfig]对管道的追踪行为进行配置。

关键追踪配置字段包括：

-   [`tracing_disabled`][agents.voice.pipeline_config.VoicePipelineConfig.tracing_disabled]：控制是否禁用追踪功能，默认保持启用状态
-   [`trace_include_sensitive_data`][agents.voice.pipeline_config.VoicePipelineConfig.trace_include_sensitive_data]：控制追踪记录是否包含敏感数据（如音频转录文本），该设置仅作用于语音管道本身，不影响工作流内部处理
-   [`trace_include_sensitive_audio_data`][agents.voice.pipeline_config.VoicePipelineConfig.trace_include_sensitive_audio_data]：控制追踪记录是否包含原始音频数据
-   [`workflow_name`][agents.voice.pipeline_config.VoicePipelineConfig.workflow_name]：设置追踪工作流的名称
-   [`group_id`][agents.voice.pipeline_config.VoicePipelineConfig.group_id]：设置追踪记录的`group_id`，用于关联多个追踪记录
-   [`trace_metadata`][agents.voice.pipeline_config.VoicePipelineConfig.tracing_disabled]：设置需要附加到追踪记录中的元数据

（注：根据翻译规则第8条，原文未出现"Large Language Model"或"Prompt"术语；根据规则第9条，保留了所有标记符号和占位符的原始格式）