# 金融研究智能体示例

本示例展示了如何利用Agents SDK构建一个功能更完善的金融研究智能体。其模式与`research_bot`示例类似，但配备了更多专业化的子智能体并增加了验证环节。

工作流程如下：

1. **规划阶段**：规划智能体将终端用户的请求转化为适用于金融分析的搜索关键词列表——包括近期新闻、财报电话会议、公司文件、行业评论等。
2. **搜索阶段**：搜索智能体使用内置的`WebSearchTool`获取每个关键词的简明摘要。（如果已建立PDF或10-K文件索引，还可添加`FileSearchTool`）
3. **专项分析**：将其他智能体（如基本面分析师和风险分析师）作为工具暴露，使撰写者能够内联调用并整合其输出结果。
4. **报告撰写**：资深撰写智能体将搜索片段与各专项分析摘要整合成长篇Markdown报告，并附上简短的高管摘要。
5. **验证阶段**：最终验证智能体将审核报告是否存在明显矛盾或未标注的引用来源。

可通过以下命令运行示例：

```bash
python -m examples.financial_research_agent.main
```

并输入类似查询：

```
Write up an analysis of Apple Inc.'s most recent quarter.
```

### 初始提示词

撰写智能体加载的指令类似：

```
You are a senior financial analyst. You will be provided with the original query
and a set of raw search summaries. Your job is to synthesize these into a
long‑form markdown report (at least several paragraphs) with a short executive
summary. You also have access to tools like `fundamentals_analysis` and
`risk_analysis` to get short specialist write‑ups if you want to incorporate them.
Add a few follow‑up questions for further research.
```

您可以根据自身数据源和偏好的报告结构调整这些提示词和子智能体。