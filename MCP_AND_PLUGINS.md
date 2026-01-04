# MCP 服务器和插件使用指南

**更新时间：2026-01-04 00:00:00**

本文档记录了 Indeptrader 项目中配置的所有 Model Context Protocol (MCP) 服务器和插件的功能、使用方法和状态。

## 目录

- [MCP 服务器列表](#mcp-服务器列表)
- [优先级使用指南](#优先级使用指南)
- [详细功能说明](#详细功能说明)
- [Claude Code Skills 插件](#claude-code-skills-插件)
- [其他可用的 MCP 服务器](#其他可用的-mcp-服务器)
- [配置管理](#配置管理)

---

## MCP 服务器列表

### ✅ 已连接的服务器

| 服务器名称 | 类型 | 状态 | 主要用途 |
|----------|------|------|---------|
| **qdrant-kb** | 本地 Python | 🟢 运行中 | 本地向量知识库查询 |
| **ckb** | npm | 🟢 运行中 | 代码知识库和符号搜索 |
| **firecrawl** | npm | 🟢 运行中 | 网页抓取、搜索和数据提取 |
| **tavily** | npx remote | 🟢 运行中 | 网页搜索和爬虫 |
| **brightdata** | SSE | 🟢 运行中 | 高级网页抓取 |
| **claude-mem** | Plugin | 🟢 运行中 | 对话记忆管理 |

### ❌ 未连接的服务器

| 服务器名称 | 状态 | 说明 |
|----------|------|------|
| **serena** | 🔴 连接失败 | 代码知识库（被 ckb 替代） |
| **deep-research** | 🔴 连接失败 | 深度研究服务器 |

---

## 优先级使用指南

### 1. 代码查询 (CKB 优先)

**查询代码结构、函数定义、调用关系时：**

```
优先级：CKB (serena) > Grep/Glob
```

**使用场景：**
- 查找函数定义和实现
- 查看类继承关系
- 追踪函数调用链
- 分析代码依赖关系
- 获取代码架构概览

**常用工具：**
- `mcp__ckb__searchSymbols` - 搜索符号
- `mcp__ckb__explainSymbol` - 解释符号
- `mcp__ckb__getCallGraph` - 获取调用图
- `mcp__ckb__findReferences` - 查找引用

### 2. 知识库查询 (Qdrant 优先)

**查询项目文档、研究报告、金融概念时：**

```
优先级：Qdrant 本地知识库 > 网络搜索
```

**优势：**
- ⚡ 响应时间 < 100ms
- 📦 无需网络连接
- 💾 本地向量检索

**使用场景：**
- 查询项目文档和 API 说明
- 查找研究报告和技术论文
- 理解金融概念和交易策略
- 获取开发指南和配置说明

**常用工具：**
- `mcp__qdrant-kb__search_knowledge` - 搜索知识库
- `mcp__qdrant-kb__chat_with_knowledge` - 对话式查询
- `mcp__qdrant-kb__list_knowledge_documents` - 列出文档

### 3. 网页搜索和抓取 (Firecrawl 优先)

**进行 Web 搜索和内容抓取时：**

```
优先级：Firecrawl > Tavily > Bright Data
```

**Firecrawl (首选)：**
- 🔍 Web 搜索：`mcp__firecrawl__firecrawl_search`
- 📄 单页抓取：`mcp__firecrawl__firecrawl_scrape`
- 🌐 网站地图：`mcp__firecrawl__firecrawl_map`
- 🕷️ 深度爬取：`mcp__firecrawl__firecrawl_crawl`
- 📊 结构化提取：`mcp__firecrawl__firecrawl_extract`
- 🤖 AI 代理：`mcp__firecrawl__firecrawl_agent`

**Tavily (备选)：**
- 🔍 Web 搜索：`mcp__tavily__tavily_search`
- 📄 内容提取：`mcp__tavily__tavily_extract`
- 🌐 网站地图：`mcp__tavily__tavily_map`
- 🕷️ 网站爬取：`mcp__tavily__tavily_crawl`

**Bright Data (高级抓取)：**
- 📄 单页抓取：`mcp__brightdata__scrape_as_markdown`
- 📦 批量抓取：`mcp__brightdata__scrape_batch`
- 🔍 搜索引擎：`mcp__brightdata__search_engine`

### 4. 记忆管理 (Claude Mem)

**跨会话记忆存储和检索：**

```
工作流程：search → timeline → get_observations
```

**常用工具：**
- `mcp__plugin_claude-mem_mcp-search__search` - 搜索记忆
- `mcp__plugin_claude-mem_mcp-search__timeline` - 获取时间线上下文
- `mcp__plugin_claude-mem_mcp-search__get_observations` - 获取完整记忆详情

---

## 详细功能说明

### 1. Qdrant 本地知识库 (qdrant-kb)

**启动方式：**
```bash
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/qdrant_mcp_fastapi.py
```

**主要功能：**
- 向量相似度搜索
- 元数据过滤（按类别、文件类型）
- 对话式问答
- 知识库统计

**数据分类：**
- `project` - 项目文档
- `research` - 研究报告
- `business` - 业务知识
- `other` - 其他文档

**示例用法：**
```python
# 搜索特定主题
search_knowledge(
    query="收益率曲线的定义",
    top_k=5,
    filters={"category": "business"}
)

# 快速对话
chat_with_knowledge(query="如何配置 FRED API？")
```

### 2. 代码知识库 (CKB)

**启动方式：**
```bash
npx @tastehub/ckb mcp
```

**主要功能：**
- 符号搜索和解释
- 调用图分析
- 引用查找
- 架构概览
- 热点分析
- 影响分析

**常用操作：**
- 搜索函数/类：`searchSymbols(query="function_name")`
- 查看调用关系：`getCallGraph(symbolId="xxx")`
- 查找引用：`findReferences(symbolId="xxx")`
- 架构分析：`getArchitecture(depth=2)`

### 3. Firecrawl

**启动方式：**
```bash
npx -y firecrawl-mcp
```

**主要功能：**
- **Web 搜索**：智能搜索并提取内容
- **网页抓取**：获取完整页面内容（Markdown/HTML）
- **网站地图**：发现网站所有 URL
- **深度爬取**：遍历整个网站
- **结构化提取**：LLM 驱动的数据提取
- **AI 代理**：自主研究代理

**特色功能：**
- 支持 `branding` 格式提取品牌标识（颜色、字体、UI 组件）
- 高级选项：缓存、代理位置、移动端模拟
- PDF 解析支持
- 批量操作优化

**示例用法：**
```python
# Web 搜索
firecrawl_search(
    query="最新 AI 研究论文 2025",
    limit=5,
    sources=["web", "news"]
)

# 网页抓取
firecrawl_scrape(
    url="https://example.com",
    formats=["markdown"],
    maxAge=172800000  # 使用缓存加速
)

# 网站地图
firecrawl_map(url="https://example.com")

# 深度爬取
firecrawl_crawl(
    url="https://example.com/blog/*",
    limit=20,
    maxDiscoveryDepth=5
)

# 结构化提取
firecrawl_extract(
    urls=["https://example.com/product1"],
    prompt="提取产品名称、价格和描述",
    schema={
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "price": {"type": "number"},
            "description": {"type": "string"}
        }
    }
)
```

### 4. Tavily

**启动方式：**
```bash
npx -y mcp-remote https://mcp.tavily.com/mcp/?tavilyApiKey=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
```

**主要功能：**
- **Web 搜索**：实时信息搜索
- **内容提取**：从 URL 提取文本
- **网站地图**：发现网站结构
- **网站爬取**：多页面爬取

**搜索深度选项：**
- `basic` - 基础搜索
- `advanced` - 深度搜索
- `fast` - 低延迟优化
- `ultra-fast` - 极速搜索

**主题类型：**
- `general` - 通用搜索
- `news` - 新闻搜索
- `finance` - 金融搜索

### 5. Bright Data

**连接方式：**
```bash
SSE: https://mcp.brightdata.com/sse?token=ed327c0d-f5a4-40e0-9c44-df28a0b277cc
```

**主要功能：**
- 高级网页抓取（绕过机器人检测和 CAPTCHA）
- 批量抓取
- 搜索引擎结果抓取（Google/Bing/Yandex）

**使用场景：**
- 需要抓取受保护的网站
- 批量处理多个 URL
- 获取搜索引擎结果

### 6. Claude Mem (记忆插件)

**存储位置：**
```bash
/home/shang/.claude/plugins/cache/thedotmack/claude-mem/8.5.5/scripts/mcp-server.cjs
```

**主要功能：**
- 跨会话记忆存储
- 三层检索工作流（search → timeline → get_observations）
- Token 优化（先索引后详情）

**最佳实践：**
1. 使用 `search` 获取索引和 ID
2. 使用 `timeline` 获取上下文
3. 使用 `get_observations` 获取完整详情

---

## Claude Code Skills 插件

Skills 是 Claude Code 的扩展功能，提供专业化的工作流和工具集成。

### 已安装的插件包

#### 1. document-skills@anthropic-agent-skills

**版本：** 69c0b1a06741
**安装时间：** 2025-12-27
**作用域：** 项目级 (/home/shang)

**包含的 Skills：**

| Skill 名称 | 功能描述 |
|-----------|---------|
| **algorithmic-art** | 使用 p5.js 创建算法艺术，支持种子随机和交互参数 |
| **brand-guidelines** | 应用 Anthropic 官方品牌颜色和排版样式 |
| **canvas-design** | 创建精美的视觉艺术作品（PNG/PDF） |
| **doc-coauthoring** | 文档协作工作流指南 |
| **docx** | Word 文档创建、编辑、分析（支持修订、评论） |
| **frontend-design** | 创建高质量前端界面设计 |
| **internal-comms** | 撰写公司内部通讯（状态报告、更新等） |
| **mcp-builder** | 构建 MCP 服务器的指南 |
| **pdf** | PDF 处理工具（提取文本、表格、表单、合并拆分） |
| **pptx** | PowerPoint 演示文稿创建和编辑 |
| **skill-creator** | 创建有效技能的指南 |
| **slack-gif-creator** | 创建 Slack 优化的动画 GIF |
| **theme-factory** | 应用主题样式到文档 |
| **web-artifacts-builder** | 构建复杂的多组件 HTML artifacts |
| **webapp-testing** | 使用 Playwright 测试本地 Web 应用 |
| **xlsx** | Excel 电子表格处理（公式、格式、数据分析） |

#### 2. example-skills@anthropic-agent-skills

**版本：** unknown
**安装时间：** 2025-12-27
**作用域：** 项目级 (/home/shang)

**说明：** 包含与 document-skills 相同的技能集合，作为示例和参考实现。

#### 3. claude-mem@thedotmack

**版本：** 8.5.5
**安装时间：** 2026-01-04
**作用域：** 用户级 (全局)

**功能：** 跨会话记忆管理和检索（详见上文 "6. Claude Mem" 章节）

### Skills 工作原理

**调用方式：**
- 当用户请求需要特定技能的任务时，Claude 会自动识别并使用相应的 Skill
- 例如：用户说"创建一个 PPT"，会自动触发 `pptx` skill
- 用户也可以明确指定：`/pptx` 或 `use pptx skill`

**Skill 配置文件：**
每个 skill 都有独立的配置文件，通常位于：
```
~/.claude/plugins/cache/anthropic-agent-skills/document-skills/<version>/skills/<skill-name>/
```

**常用 Skills 示例：**

```bash
# 创建演示文稿
/pptx "创建一个关于金融分析的报告"

# 处理 PDF
/pdf "提取这个 PDF 中的表格数据"

# 文档协作
/doc-coauthoring "帮我写一份技术规范"

# 内部通讯
/internal-comms "写一份项目状态更新"

# Excel 处理
/xlsx "分析这个电子表格的数据"

# 前端设计
/frontend-design "创建一个交易仪表盘界面"
```

### Skills 管理

**查看已安装的 Skills：**
```bash
ls ~/.claude/plugins/cache/anthropic-agent-skills/document-skills/*/skills/
```

**Skills 配置文件：**
```bash
~/.claude/plugins/installed_plugins.json
```

**官方文档：**
- Skills 开发指南位于各 skill 的 `SKILL.md` 文件
- 通用规范在 `spec/agent-skills-spec.md`

---

## 其他可用的 MCP 服务器

### 4.5v-mcp (图像分析)

**功能：**
- 图像内容分析和理解
- 前端代码复刻（描述布局、样式、组件）

**工具：**
- `mcp__4_5v_mcp__analyze_image` - 分析图像 URL

### web_reader (网页阅读器)

**功能：**
- 将 URL 转换为大模型友好的输入格式
- 支持 Markdown/Text 输出
- 图片处理选项

**工具：**
- `mcp__web_reader__webReader`

---

## 配置管理

### 查看所有 MCP 服务器状态

```bash
claude mcp list
```

### 添加新的 MCP 服务器

```bash
claude mcp add <server-name>
```

### 移除 MCP 服务器

```bash
claude mcp remove <server-name>
```

### 配置文件位置

MCP 服务器配置存储在：
```bash
/home/shang/.claude/settings.json
```

---

## 故障排除

### Serena 连接失败

**问题：** Serena 代码知识库无法连接

**解决方案：**
- 使用 CKB 作为替代
- CKB 提供类似且更强大的功能

### Deep-research 连接失败

**问题：** Deep-research 服务器无法连接

**解决方案：**
- 检查服务是否在 http://127.0.0.1:3000 运行
- 启动服务：`cd /home/shang/git/deep-research && <启动命令>`

### Qdrant 知识库无响应

**问题：** qdrant-kb 查询超时

**解决方案：**
1. 检查 FastAPI 服务是否运行：
   ```bash
   ps aux | grep qdrant_mcp_fastapi
   ```

2. 查看服务日志：
   ```bash
   journalctl -u qdrant-kb -f
   ```

3. 重启服务：
   ```bash
   systemctl restart qdrant-kb
   ```

---

## 性能优化建议

### 1. 减少网络请求

- 优先使用本地知识库（Qdrant）而非网络搜索
- 使用 Firecrawl 的 `maxAge` 参数启用缓存
- 批量操作时使用 `batch` 工具而非多次单独调用

### 2. Token 优化

- Claude Mem 使用三层工作流，避免一次性获取所有详情
- 使用 `limit` 参数控制返回结果数量
- 使用元数据过滤减少无关结果

### 3. 响应时间优化

- 代码查询：CKB (< 500ms)
- 知识库查询：Qdrant (< 100ms)
- 网页抓取：Firecrawl (最快选项)

---

## 最佳实践

### 知识库查询策略

```
1. 优先使用 search_knowledge 查询本地知识库
2. 如果本地知识库结果不足，使用 timeline 获取上下文
3. 最后才考虑使用网络搜索工具
```

### 网页抓取策略

```
1. 单个页面：使用 firecrawl_scrape
2. 多个页面：使用 firecrawl_extract (批量)
3. 整个网站：先用 firecrawl_map 发现 URL，再选择性抓取
4. 研究任务：使用 firecrawl_agent 自主搜索
```

### 代码查询策略

```
1. 查找具体函数/类：使用 searchSymbols
2. 理解调用关系：使用 getCallGraph
3. 查找所有引用：使用 findReferences
4. 理解整体架构：使用 getArchitecture
```

---

## 相关文档

- [Qdrant 部署方案](QDRANT_DEPLOYMENT_PLAN.md)
- [Qdrant 使用指南](knowledge-base/QDRANT_使用指南.md)
- [知识库构建方案](knowledge-base/project/知识库构建方案.md)

---

**最后更新：** 2026-01-04
**维护者：** Claude Code
