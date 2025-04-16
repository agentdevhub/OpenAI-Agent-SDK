# 静态语音演示

本演示通过录制音频后运行语音处理流程实现。

运行方式：

```
python -m examples.voice.static.main
```

## 工作原理

1. 我们创建了一个`VoicePipeline`，并配置了自定义工作流。该工作流会运行Agent，但如果你说出特定暗语，它也会触发一些定制响应。
2. 当用户说话时，音频会被传送到语音处理流程。当用户停止说话时，Agent开始运行。
3. 语音处理流程对音频执行以下操作：
    1. 将音频转录为文字
    2. 将转录文本输入工作流，由工作流执行Agent
    3. 将Agent输出流式传输至文本转语音模型
4. 播放生成的语音

建议尝试的示例：

-   Tell me a joke（助手会讲一个笑话）
-   What's the weather in Tokyo?（将调用`get_weather`工具后进行语音播报）
-   Hola, como estas?（将转接至西班牙语Agent）
-   Tell me about dogs.（将返回硬编码的"你猜中了暗语"消息）