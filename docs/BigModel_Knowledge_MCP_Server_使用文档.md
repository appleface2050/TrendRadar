# BigModel.cn 知识库 MCP Server 使用文档

## 概述

BigModel.cn 知识库 MCP Server 是一个为 Claude Code 定制的 Model Context Protocol (MCP) 服务器，让你可以直接在 Claude Code 中查询 BigModel.cn 云端知识库，实现智能知识检索和问答。

### 核心功能

- 🔍 **智能检索**：支持向量检索、关键词检索、混合检索
- 📚 **多格式支持**：PDF, Markdown, DOCX, TXT, PPT, Excel 等
- 🎯 **高精度召回**：基于上下文增强技术，召回率提升 12%-23%
- ⚡ **实时查询**：毫秒级检索响应
- 🔄 **自动同步**：与  知识库和 Deep Research 报告联动

---

## 快速开始

### 前置要求

1. **BigModel.cn 账号**：
   - 访问 https://bigmodel.cn 注册账号
   - 创建知识库并获取知识库 ID
   - 生成 API Key

2. **已配置的知识库**：
   - 知识库 ID：已保存到 `confidential.json`
   - API Key：已保存到 `confidential.json`

### 安装步骤

#### 1. 安装 MCP 库

```bash
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple mcp
```

#### 2. 配置 MCP Server

MCP Server 已自动添加到 Claude Code 配置中。配置文件位于：
- `~/.claude.json` (项目级别)
- 或 `~/.config/claude/claude_desktop_config.json` (全局级别)

配置内容：
```json
{
  "mcpServers": {
    "bigmodel-kb": {
      "command": "python3",
      "args": ["/home/shang/git/Indeptrader/knowledge-base/scripts/bigmodel_mcp.py"]
    }
  }
}
```

#### 3. 验证安装

```bash
# 测试 MCP Server 脚本
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/bigmodel_mcp.py

# 检查 MCP 服务器状态
claude mcp list
```

---

## 使用方法

### 方式一：在 Claude Code 中直接使用（推荐）

在 Claude Code 对话中直接提问：

```
请根据知识库查询：收益率曲线倒挂的定义是什么？
```

```
使用 search_knowledge 工具查询：如何使用 FRED API 获取数据？
```

**可用工具**：

1. **search_knowledge** - 高级检索
   - 参数：
     - `query` (必需): 查询内容
     - `top_k` (可选): 返回结果数量 (1-20)，默认 5
     - `recall_method` (可选): 检索方式
       - `embedding`: 向量检索（语义理解）
       - `keyword`: 关键词检索（精确匹配）
       - `mixed`: 混合检索（默认，推荐）

2. **chat_with_knowledge** - 快速对话
   - 参数：
     - `query` (必需): 你的问题
   - 自动返回最相关的 5 个结果

### 方式二：使用 Python 脚本

#### 创建查询脚本

```python
#!/usr/bin/env python3
"""查询 BigModel.cn 知识库"""

import sys
sys.path.append('/home/shang/git/Indeptrader/scripts')

from bigmodel_kb import BigModelKnowledgeBase

# 初始化知识库客户端
kb = BigModelKnowledgeBase()

# 示例 1：简单查询
result = kb.search_knowledge(
    query="收益率曲线倒挂的定义",
    top_k=5
)
print(result)

# 示例 2：使用向量检索
result = kb.search_knowledge(
    query="宏观经济指标分析",
    top_k=3,
    recall_method="embedding"
)
print(result)

# 示例 3：使用关键词检索
result = kb.search_knowledge(
    query="FRED API",
    top_k=5,
    recall_method="keyword"
)
print(result)
```

#### 运行脚本

```bash
python3 your_query_script.py
```

### 方式三：使用管理脚本

#### 上传文档

```bash
# 上传单个文件
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/bigmodel_kb.py upload \
  --kb-id "2004906251758215168" \
  --file "path/to/document.md"

# 批量上传目录
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/bigmodel_kb.py upload \
  --kb-id "2004906251758215168" \
  --dir "/home/shang/git/Indeptrader/docs"
```

#### 列出文档

在 Web 控制台查看：
1. 访问 https://bigmodel.cn
2. 进入"知识库"
3. 选择 "Inteptrader" 知识库
4. 查看文档列表和状态

#### 删除文档

```bash
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/bigmodel_kb.py delete \
  --kb-id "2004906251758215168" \
  --doc-id "document_id_here"
```

---

## API 参考

### BigModelKnowledgeBase 类

#### 初始化

```python
from bigmodel_kb import BigModelKnowledgeBase

kb = BigModelKnowledgeBase()
```

自动从 `/home/shang/git/Indeptrader/confidential.json` 读取配置。

#### 方法

**search_knowledge(query, top_k=5, recall_method="mixed")**

检索知识库并返回格式化结果。

**参数**：
- `query` (str): 查询内容
- `top_k` (int): 返回结果数量，范围 1-20，默认 5
- `recall_method` (str): 检索方式
  - `"embedding"`: 向量检索
  - `"keyword"`: 关键词检索
  - `"mixed"`: 混合检索（默认）

**返回**：格式化的检索结果字符串

**示例**：
```python
result = kb.search_knowledge(
    query="如何使用 Chart.js 创建图表？",
    top_k=3,
    recall_method="mixed"
)
```

**upload_file(kb_id, file_path)**

上传单个文件到知识库。

**参数**：
- `kb_id` (str): 知识库 ID
- `file_path` (str): 文件路径

**返回**：上传结果字典

**示例**：
```python
result = kb.upload_file(
    kb_id="2004906251758215168",
    file_path="/path/to/document.pdf"
)
```

**upload_directory(kb_id, directory)**

批量上传目录下的所有文件。

**参数**：
- `kb_id` (str): 知识库 ID
- `directory` (str): 目录路径

**返回**：上传结果列表

**支持的文件格式**：
- `.md`, `.txt` - 文本文件
- `.pdf` - PDF 文档
- `.docx`, `.doc` - Word 文档
- `.pptx`, `.ppt` - PowerPoint 演示文稿
- `.xlsx`, `.xls`, `.csv` - Excel 表格

---

## 配置文件

### confidential.json

位置：`/home/shang/git/Indeptrader/confidential.json`

```json
{
    "bigmodel.cn知识库ID": "2004906251758215168",
    "bigmodel.cnAPI Key": "your-api-key-here"
}
```

**注意**：
- 请勿将 `confidential.json` 提交到版本控制系统
- 已在 `.gitignore` 中排除
- API Key 和知识库 ID 需要从 BigModel.cn 控制台获取

---

## 文件结构

```
/home/shang/git/Indeptrader/
├── scripts/
│   ├── bigmodel_kb.py          # 知识库管理脚本
│   └── bigmodel_mcp.py          # MCP Server
├── docs/                        # 文档目录
│   ├── business/                # 业务知识
│   ├── project/                 # 项目文档
│   └── research/                # 研究报告
├── confidential.json            # 配置文件（已排除）
└── 知识库构建方案.md            # 完整知识库构建文档
```

---

## 工作流程

### 典型使用场景

#### 1. 添加新知识

```bash
# Step 1: 准备文档
cp new_document.md /home/shang/git/Indeptrader/docs/business/

# Step 2: 上传到知识库
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/bigmodel_kb.py upload \
  --kb-id "2004906251758215168" \
  --dir "/home/shang/git/Indeptrader/docs/business"

# Step 3: 在 Claude Code 中查询
# "请根据知识库查询：[你的问题]"
```

#### 2. 同步 Deep Research 报告

```bash
# Step 1: 同步到 
# python3 ~/Indeptrader-Knowledge/Scripts/sync-research.py (已废弃)

# Step 2: 上传到 BigModel.cn 知识库
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/bigmodel_kb.py upload \
  --kb-id "2004906251758215168" \
  --dir "/research-reports"
```

#### 3. 代码开发时查询知识

在 Claude Code 中：
```
请使用 search_knowledge 工具查询：项目中如何处理 FRED API 数据？
```

```
根据知识库，收益率曲线的数据处理逻辑在哪里？
```

---

## 故障排查

### 问题 1：MCP Server 连接失败

**症状**：
```bash
$ claude mcp list
bigmodel-kb: ✗ Failed to connect
```

**解决方案**：

1. 检查脚本是否可执行：
```bash
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/bigmodel_mcp.py
```

2. 检查配置文件：
```bash
cat /home/shang/git/Indeptrader/confidential.json
```

3. 重新配置 MCP Server：
```bash
claude mcp remove bigmodel-kb
claude mcp add bigmodel-kb "python3 /home/shang/git/Indeptrader/knowledge-base/scripts/bigmodel_mcp.py"
```

### 问题 2：检索返回空结果

**可能原因**：
1. 知识库中没有相关文档
2. 查询问题与文档内容不匹配
3. 文档正在处理中（需要等待几分钟）

**解决方案**：
1. 在 BigModel.cn Web 控制台检查文档状态
2. 尝试不同的查询关键词
3. 使用 `mixed` 检索方式以获得更好的召回效果

### 问题 3：API 认证失败

**症状**：
```
❌ 错误: 配置文件中未找到 'bigmodel.cnAPI Key'
```

**解决方案**：
1. 确认 `confidential.json` 存在且格式正确
2. 检查 API Key 是否有效
3. 重新获取 API Key：https://bigmodel.cn → API Keys

### 问题 4：文档上传失败

**常见错误**：
- 文件格式不支持
- 文件过大（>100MB）
- 网络连接问题

**解决方案**：
1. 转换文件格式（推荐 PDF）
2. 压缩大文件
3. 检查网络连接
4. 查看详细错误信息

---

## 性能优化

### 检索策略选择

| 场景 | 推荐策略 | 说明 |
|------|---------|------|
| **日常查询** | `mixed` | 平衡语义理解和精确匹配 |
| **专业术语查询** | `keyword` | 精确匹配专业术语、代码 |
| **概念理解** | `embedding` | 理解语义，支持不同表述 |
| **金融数据分析** | `mixed` | 结合指标名称和分析逻辑 |

### 文档组织建议

1. **按主题分类**：
   - `docs/business/` - 业务知识
   - `docs/project/` - 项目文档
   - `docs/research/` - 研究报告

2. **命名规范**：
   - 使用清晰的文件名
   - 避免特殊字符
   - 推荐格式：`主题-子主题-版本.md`

3. **内容结构**：
   - 使用清晰的标题层级
   - 添加摘要和关键词
   - 保持段落简洁

---

## 高级用法

### 与  集成

```bash
# 1. 在  中编辑笔记


# 2. 定期同步到 BigModel.cn
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/bigmodel_kb.py upload \
  --kb-id "2004906251758215168" \
  --dir ""
```

### 自动化工作流

创建定期同步脚本：

```bash
#!/bin/bash
# sync-knowledge-base.sh

echo "🔄 同步知识库..."

# 1. 同步 Deep Research 报告到 
# python3 ~/Indeptrader-Knowledge/Scripts/sync-research.py (已废弃)

# 2. 上传到 BigModel.cn
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/bigmodel_kb.py upload \
  --kb-id "2004906251758215168" \
  --dir "/home/shang/Indeptrader/docs"

echo "✅ 同步完成！"
```

添加到 crontab：
```bash
crontab -e

# 每天凌晨 2 点同步
0 2 * * * /home/shang/git/Indeptrader/knowledge-base/scripts/sync-knowledge-base.sh
```

### 自定义查询参数

```python
# 高精度检索
result = kb.search_knowledge(
    query="宏观经济指标分析",
    top_k=10,
    recall_method="mixed"
)

# 快速关键词查询
result = kb.search_knowledge(
    query="FRED",
    top_k=3,
    recall_method="keyword"
)

# 深度语义理解
result = kb.search_knowledge(
    query="经济衰退的预测指标",
    top_k=5,
    recall_method="embedding"
)
```

---

## 最佳实践

### 1. 知识库维护

- ✅ **定期更新**：每周同步新文档
- ✅ **版本管理**：在文档中标注更新日期
- ✅ **质量优先**：上传高质量、结构化的文档
- ❌ **避免重复**：不要上传重复或过时的文档

### 2. 查询技巧

- ✅ **明确问题**：具体描述你的需求
- ✅ **使用关键词**：包含专业术语和关键概念
- ✅ **多角度查询**：尝试不同的表述方式
- ❌ **避免模糊**：过于宽泛的问题效果不佳

### 3. 协作使用

- ****：用于知识整理和笔记编辑
- **BigModel.cn**：用于云端检索和智能问答
- **Serena/CKB**：用于代码符号搜索
- **Deep Research**：用于深度研究和报告生成

---

## 更新日志

### v1.0.0 (2025-12-27)

- ✅ 初始版本发布
- ✅ 支持知识库检索功能
- ✅ 支持文档上传和管理
- ✅ MCP Server 集成
- ✅ 完整的文档和示例

---

## 相关资源

### 官方文档

- [BigModel.cn 知识库文档](https://docs.bigmodel.cn/cn/guide/tools/knowledge/guide)
- [BigModel.cn API 文档](https://docs.bigmodel.cn/cn/api/introduction)
- [MCP 协议规范](https://modelcontextprotocol.io)

### 项目文档

- [知识库构建方案](./知识库构建方案.md)
- [深度研究报告](../deep_research_report/)

### 技术支持

- BigModel.cn 客服：https://bigmodel.cn
- 项目 Issues：https://github.com/your-repo/issues

---

## 贡献指南

欢迎提交问题和改进建议！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件

---

**作者**: Indeptrader Team
**最后更新**: 2025-12-27
**版本**: 1.0.0
