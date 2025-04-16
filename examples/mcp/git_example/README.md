# MCP Git 示例

本示例使用 [git MCP 服务器](https://github.com/modelcontextprotocol/servers/tree/main/src/git)，通过 `uvx` 在本地运行。

运行方式：

```
uv run python examples/mcp/git_example/main.py
```

## 实现细节

该示例使用了 `agents.mcp` 中的 `MCPServerStdio` 类，执行命令如下：

```bash
uvx mcp-server-git
```

在运行智能体之前，系统会提示用户提供本地 git 仓库的目录路径。获取路径后，智能体便可调用诸如 `git_log` 等 Git MCP 工具来检查 git 提交日志。

底层实现逻辑：

1. 服务器在子进程中启动，并暴露一系列工具如 `git_log()`
2. 通过 `mcp_agents` 将服务器实例添加到智能体中
3. 每次智能体运行时，都会调用 MCP 服务器通过 `server.list_tools()` 获取工具列表（结果会被缓存）
4. 当大模型选择使用 MCP 工具时，通过 `server.run_tool()` 调用 MCP 服务器执行对应工具