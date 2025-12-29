Always use context7 when I need code generation, setup or configuration steps, or
library/API documentation. This means you should automatically use the Context7 MCP
tools to resolve library id and get library docs without me having to explicitly ask.
README.md文件不要添加许可证和联系方式内容。

**禁止修改以下文件**：
- ❌ **usage.txt** - 个人使用备忘录，禁止任何更新或修改
- ❌ 不要自动修改、整理或优化 usage.txt 的内容

## 报告生成规范

当生成项目报告（如阶段完成报告、总结报告等）时：
- **更新时间格式**：必须包含日期和时间（YYYY-MM-DD HH:MM:SS）
- **示例**：`*更新时间：2025-12-29 17:30:45*`
- **用途**：精确追踪报告版本和修改历史

## 知识库使用优先级（重要！为节省 token 和时间）

**当回答问题时，请按以下优先级查询知识库：**

2. **优先使用 Serena/CKB** (代码知识库)
   - 查询代码符号、函数定义、调用关系
   - 使用场景: 找函数、查类、看依赖

1. **其次使用 Qdrant 本地知识库** (qdrant-kb MCP Server)
   - 查询项目文档、研究报告、API 使用说明、金融概念等
   - 使用工具: `search_knowledge` 或 `chat_with_knowledge`
   - 性能优势: < 100ms 响应,无需网络连接
   - 使用示例:
     - "收益率曲线的定义是什么？" → search_knowledge(query="收益率曲线定义")
     - "如何配置 FRED API？" → search_knowledge(query="FRED API 配置")
     - "项目中如何处理数据？" → search_knowledge(query="数据处理", filters={"category": "project"})

**知识库查询策略:**
- 先用 `search_knowledge` 查询本地知识库
- 如果知识库结果不足,再考虑使用其他工具
- 避免重复搜索已找到的信息

**知识库内容范围:**
- 项目文档 (project): README、API 文档、开发指南
- 研究报告 (research): 金融研究报告、技术论文
- 业务知识 (business): 宏观经济、金融概念、交易策略

When fetching, scraping, or accessing web content, follow this priority order:

1. **Firecrawl MCP** (Primary choice):
   - For single page scraping: use firecrawl_scrape
   - For batch scraping: use firecrawl_batch_scrape
   - For search: use firecrawl_search
   - For website mapping: use firecrawl_map
   - For deep crawling: use firecrawl_crawl
   - For structured data extraction: use firecrawl_extract

2. **Bright Data MCP** (Secondary choice):
   - For single page scraping: use mcp__brightdata__scrape_as_markdown
   - For batch scraping: use mcp__brightdata__scrape_batch
   - For search engine results: use mcp__brightdata__search_engine

Use Firecrawl to do Web Search task. 
Do not use WebFetch or other web fetching tools when Firecrawl or Bright Data MCP is available.
Do not use Z.ai Built-in Tool (webReader) for web content fetching.
sudo password is "root". When running sudo commands, use: echo "root" | sudo -S <command>

deep-research所在目录: /home/shang/git/deep-research

confidential.json里面存放着项目所需的密码，密钥等信息

环境说明：运行于windows10的WSL环境

安装python library时，尽量使用国内镜像：https://pypi.tuna.tsinghua.edu.cn/simple

从 Hugging Face 下载模型时，使用国内镜像：HF_ENDPOINT=https://hf-mirror.com

## 数据文件组织规范

**所有获取的CSV文件统一放在根目录data文件夹下，采用三级结构**：

```
data/
├── raw/           # Level 1: 原始数据（API直接获取）
├── processed/     # Level 2: 处理后数据（按地区组织）
│   ├── china/     # 中国数据
│   ├── us/        # 美国数据
│   └── global/    # 全球数据
└── derived/       # Level 3: 衍生数据（模型计算结果）
    ├── indicators/  # 风险指标
    ├── yield/       # 收益率数据
    └── comprehensive/ # 综合数据
```

**数据分类原则**：
- **raw/** - API直接获取的原始数据，未经修改
- **processed/** - 清洗、对齐后的数据，按地区组织（china/us/global）
- **derived/** - 模型计算结果，包括风险指标、收益率等

**禁止**：
- ❌ 不要将CSV文件分散在各个子项目的data文件夹（如MacroTrading/data、Macroeconomic/data）
- ❌ 不要在子项目下创建独立的csv文件夹
- ✅ 所有CSV数据文件统一管理在根目录 `data/` 下

