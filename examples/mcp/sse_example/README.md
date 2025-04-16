# MCP SSE 示例

本示例在 [server.py](server.py) 中使用了一个本地 SSE 服务器。

通过以下命令运行示例：

```
uv run python examples/mcp/sse_example/main.py
```

## 实现细节

该示例使用了来自 `agents.mcp` 的 `MCPServerSse` 类。服务器以子进程形式运行在 `https://localhost:8000/sse` 端口。