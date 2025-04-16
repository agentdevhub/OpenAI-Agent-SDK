# MCP 文件系统示例

本示例使用[filesystem MCP服务器](https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem)，通过`npx`在本地运行。

运行方式：

```
uv run python examples/mcp/filesystem_example/main.py
```

## 实现细节

该示例使用来自`agents.mcp`的`MCPServerStdio`类，并执行以下命令：

```bash
npx -y "@modelcontextprotocol/server-filesystem" <samples_directory>
```

仅授予该示例访问同级目录`sample_files`的权限，该目录包含一些示例数据。

底层实现原理：

1. 服务器在子进程中启动，并暴露一系列工具如`list_directory()`、`read_file()`等
2. 通过`mcp_agents`将服务器实例添加到Agent中
3. 每次Agent运行时，都会调用MCP服务器通过`server.list_tools()`获取工具列表
4. 当大模型选择使用MCP工具时，通过`server.run_tool()`调用MCP服务器执行该工具