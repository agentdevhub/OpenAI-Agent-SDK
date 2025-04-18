# 语音流式交互演示

这是一个互动演示，您可以与智能体进行对话交流。该演示使用了语音管道的内置轮次检测功能，当您停止说话时，智能体会立即响应。

运行方式：

```
python -m examples.voice.streamed.main
```

## 实现原理

1. 我们创建了一个`VoicePipeline`，并配置了`SingleAgentVoiceWorkflow`。这是一个以Assistant智能体为起点的工作流，包含工具调用和任务转交功能。
2. 从终端捕获音频输入。
3. 使用录制的音频运行管道，该流程会：
    1. 将音频转录为文本
    2. 将转录文本输入工作流，由智能体进行处理
    3. 将智能体输出流式传输至文本转语音模型
4. 播放生成的语音。

您可以尝试以下示例：

-   给我讲个笑话（智能体会讲一个笑话）
-   东京天气如何？（将调用`get_weather`工具后进行语音播报）
-   Hola, como estas?（将转交给西班牙语智能体处理）