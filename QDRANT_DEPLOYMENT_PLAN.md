# Qdrant 本地知识库部署方案（轻量级嵌入式模式）

## 一、项目背景

**项目需求：**
- 构建本地向量数据库知识库系统
- 使用 Qdrant Client 嵌入式模式（无需独立服务器）
- 实现文档的智能检索和语义搜索
- 集成 Claude Code MCP Server

**核心目标：**
- ✅ 完全本地化，数据自主可控
- ✅ 零依赖部署（无需 Docker 或独立服务器）
- ✅ 轻量级架构，适合个人和小团队
- ✅ 快速响应，低资源占用
- ✅ 支持文档的智能检索和去重

**技术选型说明：**
采用 Qdrant Client 的嵌入式模式（本地持久化），而非 Docker 服务器部署。这种方案更适合个人知识库场景，具有部署简单、资源占用低、易于维护等优势。

## 二、技术架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────┐
│          Indeptrader 项目 (WSL2)                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌────────────────────────────────────────────┐    │
│  │  Python 应用进程                            │    │
│  │                                             │    │
│  │  ┌──────────────────────────────────────┐  │    │
│  │  │  QdrantKnowledgeBase                  │  │    │
│  │  │  (qdrant_kb.py)                       │  │    │
│  │  │                                       │  │    │
│  │  │  - QdrantClient (embedded mode)      │  │    │
│  │  │  - BGE-M3 嵌入模型                    │  │    │
│  │  │  - 文档分块 & 向量化                  │  │    │
│  │  │  - 智能去重（MD5 + 向量相似度）       │  │    │
│  │  └──────────────────────────────────────┘  │    │
│  │                     ↓                        │    │
│  │  ┌──────────────────────────────────────┐  │    │
│  │  │  本地存储                             │  │    │
│  │  │  /home/shang/qdrant_data/            │  │    │
│  │  │  - collection 数据                   │  │    │
│  │  │  - 索引文件                          │  │    │
│  │  └──────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────┘  │
│                                                      │
│  MCP 集成:                                           │
│  - Claude Code ←→ Qdrant MCP Server                │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 2.2 向量嵌入方案

**当前方案：BGE-M3 本地模型**
- 模型: `BAAI/bge-m3-base`
- 向量维度: 1024
- 支持中文和英文
- 优势:
  - 无需网络调用，响应快
  - 零 API 成本
  - 数据隐私和安全
  - 支持中英文混合检索

**备选方案：云端 API**
- DeepSeek Embedding API
- OpenAI Embedding API
- 适用场景: 需要更高质量的向量表示

### 2.3 方案对比：嵌入式 vs Docker

| 特性 | 嵌入式模式（当前方案） | Docker 服务器模式 |
|------|---------------------|------------------|
| **部署复杂度** | ✅ 极简（仅需 Python） | ⚠️ 需要配置 Docker |
| **资源占用** | ✅ 低（进程内运行） | ⚠️ 较高（独立容器 2-4GB） |
| **启动速度** | ✅ 即时启动 | ⚠️ 容器启动耗时 |
| **并发访问** | ❌ 不支持 | ✅ 支持多进程/多用户 |
| **Web UI** | ❌ 不支持 | ✅ 支持（需额外容器） |
| **性能** | ⚠️ 受限（单进程） | ✅ 更好（独立服务优化） |
| **适用规模** | < 10K 文档 | 支持 100K+ 文档 |
| **可维护性** | ✅ 简单 | ⚠️ 需要容器运维 |
| **备份恢复** | ✅ 文件级备份 | ⚠️ 需要快照机制 |

**推荐场景：**
- ✅ **嵌入式模式**：个人知识库、小团队、单机使用
- ✅ **Docker 模式**：多用户环境、大规模数据、生产部署

## 三、目录结构

```
# 数据目录（项目外，用户主目录）
/home/shang/qdrant_data/              # [重要] Qdrant 本地存储数据
└── [自动生成]                        # Collection 数据和索引

# 项目目录
/home/shang/git/Indeptrader/
├── knowledge-base/
│   ├── scripts/
│   │   ├── qdrant_kb.py              # [已完成] 核心知识库类
│   │   └── test_qdrant.py            # [已完成] 测试脚本
│   ├── business/                     # 商业文档
│   ├── project/                      # 项目文档
│   └── research/                     # 研究文档
└── QDRANT_DEPLOYMENT_PLAN.md         # 本文档
```

**数据存储说明：**
- Qdrant 数据存储在用户主目录的 `qdrant_data/`（项目外）
- 绝对路径：`/home/shang/qdrant_data/`
- 数据包含：Collection 数据、向量索引、元数据
- 代码初始化时会自动创建该目录（如果不存在）
- 可通过 `storage_path` 参数自定义路径

**为什么放在用户主目录？**
- ✅ 完全与项目代码分离
- ✅ 方便备份和管理（独立的数据位置）
- ✅ 符合数据与代码分离的最佳实践
- ✅ 避免数据文件被误提交到 Git
- ✅ 多个项目可以共享同一个知识库

## 四、核心实现

### 4.1 已实现文件

#### 1. `knowledge-base/scripts/qdrant_kb.py` ✅

**功能特性：**
- ✅ Qdrant Client 嵌入式模式初始化
- ✅ BGE-M3 嵌入模型支持
- ✅ 文档解析（支持 PDF、Markdown、Word、Excel 等）
- ✅ 智能文档分块（按段落，可配置大小）
- ✅ 文档向量化（使用 BGE-M3）
- ✅ 智能去重（MD5 + 文件路径）
- ✅ 语义搜索（支持元数据过滤）
- ✅ 文档管理（上传、删除、列表）

**核心类：**
```python
class QdrantKnowledgeBase:
    """Qdrant 本地向量知识库管理类"""

    COLLECTION_NAME = "knowledge_base"
    VECTOR_SIZE = 1024  # BGE-M3
    SIMILARITY_THRESHOLD = 0.95

    def __init__(self, storage_path="/home/shang/qdrant_data", model_name="BAAI/bge-m3-base")
    def upload_document(file_path, skip_duplicates=True)
    def upload_directory(directory, recursive=True)
    def search(query, top_k=5, score_threshold=0.5, filters=None)
    def delete_document(file_path)
    def list_documents(category=None, file_type=None)
    def get_collection_info()
```

**命令行接口：**
```bash
# 上传单个文件
python3 knowledge-base/scripts/qdrant_kb.py upload --file document.pdf

# 批量上传目录
python3 knowledge-base/scripts/qdrant_kb.py upload --dir knowledge-base/

# 搜索知识库
python3 knowledge-base/scripts/qdrant_kb.py search --query "Python 异步编程"

# 列出文档
python3 knowledge-base/scripts/qdrant_kb.py list --category project

# 删除文档
python3 knowledge-base/scripts/qdrant_kb.py delete --file document.pdf
```

#### 2. `knowledge-base/scripts/test_qdrant.py` ✅

测试脚本，用于验证知识库功能。

### 4.2 Collection 设计

**Collection 结构：**
```python
{
    "collection_name": "knowledge_base",
    "vector_size": 1024,  # BGE-M3
    "distance": "Cosine",
    "payload": {
        "text": "原始文本块",
        "metadata": {
            "file_path": "/absolute/path/to/file.pdf",
            "file_name": "file.pdf",
            "file_size": 12345,
            "file_type": "pdf",
            "category": "project",  # business/project/research/other
            "md5": "abc123...",
            "upload_time": "2025-12-28T10:30:00",
            "last_modified": "2025-12-28T10:30:00",
            "chunk_index": 0,
            "total_chunks": 10,
            "chunk_text": "摘要（前500字符）..."
        }
    }
}
```

**文档分块策略：**
- `max_chunk_size`: 500 字符（可配置）
- 按段落分块（保留语义完整性）
- 支持多种文档格式：`.md`, `.txt`, `.pdf`, `.docx`, `.xlsx`, `.csv`

### 4.3 去重机制

**三级去重策略：**

1. **文件路径去重**（默认启用）
   - 基于文件绝对路径
   - 适合检测重新上传的相同文件

2. **MD5 内容去重**（默认启用）
   - 基于文件 MD5 hash
   - 适合检测内容相同但文件名不同的文件

3. **向量相似度去重**（可选，SIMILARITY_THRESHOLD = 0.95）
   - 基于向量余弦相似度
   - 适合检测高度相似的文档内容

## 五、部署步骤

### Phase 1: 环境准备 ✅ (已完成)

**1.1 安装 Python 依赖**
```bash
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    qdrant-client \
    sentence-transformers \
    unstructured[all-in-one]
```

**1.2 验证安装**
```bash
# 检查 qdrant-client
python3 -c "import qdrant_client; print(qdrant_client.__version__)"

# 检查 sentence-transformers
python3 -c "import sentence_transformers; print(sentence_transformers.__version__)"
```

### Phase 2: 初始化知识库 ✅ (已完成)

**2.1 创建测试脚本**
```bash
cd /home/shang/git/Indeptrader
python3 knowledge-base/scripts/qdrant_kb.py upload --dir knowledge-base/
```

**2.2 验证知识库**
```bash
# 查看已上传文档
python3 knowledge-base/scripts/qdrant_kb.py list

# 测试搜索
python3 knowledge-base/scripts/qdrant_kb.py search --query "测试查询"
```

### Phase 3: MCP 集成 (待实施)

**3.1 创建 MCP Server**
文件：`knowledge-base/scripts/qdrant_mcp.py`

```python
#!/usr/bin/env python3
"""
Qdrant MCP Server for Claude Code

提供工具:
- search_knowledge: 搜索知识库
- chat_with_knowledge: 基于知识库的对话
"""

from mcp.server import Server
from qdrant_kb import QdrantKnowledgeBase

app = Server("qdrant-knowledge-base")

# 初始化知识库（数据存储在用户主目录）
kb = QdrantKnowledgeBase(storage_path="/home/shang/qdrant_data")

@app.tool()
def search_knowledge(query: str, top_k: int = 5) -> str:
    """搜索知识库

    Args:
        query: 查询文本
        top_k: 返回前 K 个结果

    Returns:
        搜索结果（JSON 格式）
    """
    results = kb.search(query, top_k=top_k)
    return json.dumps(results, ensure_ascii=False, indent=2)

@app.tool()
def chat_with_knowledge(question: str) -> str:
    """基于知识库回答问题

    Args:
        question: 用户问题

    Returns:
        基于检索内容的回答
    """
    # 搜索相关文档
    results = kb.search(question, top_k=3)

    # 构建上下文
    context = "\n\n".join([r["text"] for r in results])

    # TODO: 调用 LLM 生成回答
    # 这里可以集成 DeepSeek 或其他 LLM API

    return f"找到 {len(results)} 个相关文档:\n\n{context}"

if __name__ == "__main__":
    app.run()
```

**3.2 更新 MCP 配置**

文件：`~/.config/claude-code/mcp_config.json`

```json
{
  "mcpServers": {
    "qdrant-kb": {
      "command": "python3",
      "args": [
        "/home/shang/git/Indeptrader/knowledge-base/scripts/qdrant_mcp.py"
      ],
      "cwd": "/home/shang/git/Indeptrader"
    }
  }
}
```

**3.3 重启 Claude Code**
- 关闭 Claude Code
- 重新打开以加载 MCP 配置

### Phase 4: 测试验证 (待实施)

**4.1 功能测试**
```bash
# 测试基本搜索
python3 knowledge-base/scripts/qdrant_kb.py search --query "Python 装饰器"

# 测试元数据过滤
python3 knowledge-base/scripts/qdrant_kb.py search --query "API" --category project
```

**4.2 MCP 集成测试**
在 Claude Code 中测试：
```
请使用 search_knowledge 工具搜索 "向量数据库"
```

**4.3 性能测试**
```python
import time
from qdrant_kb import QdrantKnowledgeBase

kb = QdrantKnowledgeBase()

# 测试搜索性能
start = time.time()
results = kb.search("测试查询", top_k=5)
latency = time.time() - start

print(f"搜索延迟: {latency*1000:.2f}ms")
```

## 六、备份和恢复策略

### 6.1 数据备份

**方案 1：文件级备份（推荐）**

由于 Qdrant 数据存储在本地文件系统，备份非常简单：

```bash
#!/bin/bash
# 文件: devops/backup_qdrant_kb.sh

BACKUP_ROOT="/home/shang/backups/qdrant_kb"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SOURCE_DIR="/home/shang/qdrant_data"  # 用户主目录

# 创建备份目录
mkdir -p ${BACKUP_ROOT}

# 创建压缩备份
tar -czf ${BACKUP_ROOT}/qdrant_kb_${TIMESTAMP}.tar.gz -C ${SOURCE_DIR} .

# 清理 30 天前的备份
find ${BACKUP_ROOT} -name "qdrant_kb_*.tar.gz" -mtime +30 -delete

echo "✅ 备份完成: qdrant_kb_${TIMESTAMP}.tar.gz"
```

**设置定时任务：**
```bash
# 每天凌晨 2 点备份
crontab -e
0 2 * * * /home/shang/git/Indeptrader/devops/backup_qdrant_kb.sh
```

**方案 2：云同步备份**
```bash
# 使用 rsync 同步到云存储
rsync -avz /home/shang/qdrant_data/ \
    user@backup-server:/backups/qdrant_kb/
```

### 6.2 数据恢复

```bash
#!/bin/bash
# 文件: devops/restore_qdrant_kb.sh

BACKUP_FILE=$1  # 备份文件路径

if [ -z "$BACKUP_FILE" ]; then
    echo "❌ 请指定备份文件"
    echo "用法: ./restore_qdrant_kb.sh <backup_file.tar.gz>"
    exit 1
fi

# 备份当前数据
TARGET_DIR="/home/shang/qdrant_data"  # 用户主目录
if [ -d "$TARGET_DIR" ]; then
    mv ${TARGET_DIR} ${TARGET_DIR}_backup_$(date +%Y%m%d_%H%M%S)
fi

# 恢复数据
mkdir -p ${TARGET_DIR}
tar -xzf ${BACKUP_FILE} -C ${TARGET_DIR}

echo "✅ 恢复完成"
```

**使用方法：**
```bash
./devops/restore_qdrant_kb.sh /home/shang/backups/qdrant_kb/qdrant_kb_20251228_020000.tar.gz
```

### 6.3 版本控制建议

**建议将以下内容加入 Git：**
- ✅ `knowledge-base/scripts/qdrant_kb.py`
- ✅ `knowledge-base/scripts/test_qdrant.py`
- ✅ `knowledge-base/scripts/qdrant_mcp.py`（待创建）
- ✅ 备份和恢复脚本

**建议排除 Git：**
- ❌ `qdrant_data/`（数据文件）

**更新 `.gitignore`：**
```bash
# Qdrant 本地数据（项目根目录）
qdrant_data/
```

## 七、使用指南

### 7.1 日常使用

**上传新文档：**
```bash
# 单个文件
python3 knowledge-base/scripts/qdrant_kb.py upload --file new_doc.pdf

# 整个目录（增量上传）
python3 knowledge-base/scripts/qdrant_kb.py upload --dir knowledge-base/
```

**搜索知识：**
```bash
# 基本搜索
python3 knowledge-base/scripts/qdrant_kb.py search --query "Python 异步编程"

# 返回更多结果
python3 knowledge-base/scripts/qdrant_kb.py search --query "Docker" --top-k 10
```

**管理文档：**
```bash
# 列出所有文档
python3 knowledge-base/scripts/qdrant_kb.py list

# 按类别筛选
python3 knowledge-base/scripts/qdrant_kb.py list --category project

# 删除文档
python3 knowledge-base/scripts/qdrant_kb.py delete --file outdated.pdf
```

### 7.2 Python API 使用

```python
from knowledge_base.scripts.qdrant_kb import QdrantKnowledgeBase

# 初始化知识库（数据存储在用户主目录）
kb = QdrantKnowledgeBase(
    storage_path="/home/shang/qdrant_data",
    model_name="BAAI/bge-m3-base"
)

# 上传文档
result = kb.upload_document("document.pdf")
print(f"上传了 {result['chunks']} 个文本块")

# 搜索
results = kb.search("如何使用 Python 装饰器？", top_k=5)
for i, r in enumerate(results, 1):
    print(f"[{i}] 相关度: {r['score']:.4f}")
    print(f"    文件: {r['metadata']['file_name']}")
    print(f"    内容: {r['text'][:200]}...")

# 按类别搜索
results = kb.search(
    "API 设计",
    filters={"category": "project"}
)

# 删除文档
kb.delete_document("old_document.pdf")
```

### 7.3 Claude Code 集成使用

在 Claude Code 中，通过 MCP 工具访问知识库：

```
我: 请搜索知识库中关于 "向量数据库" 的内容

Claude: [调用 search_knowledge 工具]
找到 5 个相关文档：
1. [score: 0.89] Qdrant 部署方案.md
   内容：...
```

## 八、性能优化

### 8.1 优化建议

**1. 调整分块大小**
```python
# 针对长文档，增大分块大小
kb.upload_document(file_path, chunk_size=800)

# 针对短文档，减小分块大小
kb.upload_document(file_path, chunk_size=300)
```

**2. 调整相似度阈值**
```python
# 提高精度（减少结果）
results = kb.search(query, score_threshold=0.7)

# 提高召回率（增加结果）
results = kb.search(query, score_threshold=0.3)
```

**3. 批量上传优化**
```python
# 对于大量文档，使用批量上传
results = kb.upload_directory(
    "knowledge-base/",
    skip_duplicates=True  # 跳过已上传文档
)
```

### 8.2 性能基准

**预期性能指标（BGE-M3，CPU 模式）：**
- 向量维度: 1024
- 单文档处理时间: 1-5 秒（取决于文档大小）
- 检索响应时间: 50-200ms
- 内存占用: 1-2GB（Python 进程）
- 磁盘占用: 初始约 500MB（模型 + 数据），每 1000 文档约增加 100MB

**影响因素：**
- 文档大小和数量
- 分块策略
- 硬件性能（CPU/内存）
- 向量维度

## 九、故障排除

### 9.1 常见问题

**Q1: 模型下载失败**
```bash
# 手动下载模型
export HF_ENDPOINT=https://hf-mirror.com
python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3-base')"
```

**Q2: 存储路径权限错误**
```bash
# 检查权限
ls -la qdrant_data/

# 修复权限
chmod -R 755 qdrant_data/
```

**Q3: 内存不足**
```python
# 使用更小的模型
kb = QdrantKnowledgeBase(model_name="paraphrase-multilingual-MiniLM-L12-v2")  # 384 维

# 或使用 CPU 模式
kb = QdrantKnowledgeBase(device="cpu")
```

**Q4: 搜索结果不相关**
```python
# 调整相似度阈值
results = kb.search(query, score_threshold=0.6)

# 使用不同的嵌入模型
kb = QdrantKnowledgeBase(model_name="BAAI/bge-large-zh-v1.5")
```

### 9.2 调试模式

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

kb = QdrantKnowledgeBase()
kb.search("测试查询")
```

## 十、未来扩展方向

### 10.1 短期优化（1-2 周）

- [ ] 实现 MCP Server 集成
- [ ] 添加增量更新功能
- [ ] 优化分块策略
- [ ] 添加更多文档类型支持
- [ ] 实现文档版本管理

### 10.2 中期优化（1-2 月）

- [ ] 集成 LLM 问答功能（RAG）
- [ ] 支持多种嵌入模型切换
- [ ] 添加文档标签系统
- [ ] 实现相似文档推荐
- [ ] Web UI 管理界面

### 10.3 长期优化（3-6 月）

- [ ] GPU 加速（如果需要）
- [ ] 迁移到 Docker（如果数据量增长）
- [ ] 多模态支持（图片、表格）
- [ ] 分布式部署（如果需要）

### 10.4 迁移到 Docker 方案

如果未来需要迁移到 Docker 服务器模式，步骤如下：

**1. 导出数据**
```python
from qdrant_client import QdrantClient

# 连接到嵌入式实例
local_client = QdrantClient(path="/home/shang/qdrant_data")

# 创建快照（如果支持）或导出 Collection
# TODO: Qdrant Client 嵌入式模式可能不支持快照
# 替代方案：通过 API 重新上传所有文档
```

**2. 部署 Docker Qdrant**
```bash
# 按照 Docker 方案部署
cd docker/qdrant
docker-compose up -d
```

**3. 重新上传数据**
```python
# 连接到 Docker 实例
docker_client = QdrantClient(host="localhost", port=6333)

# 重新上传所有文档
kb = QdrantKnowledgeBase(client=docker_client)
kb.upload_directory("knowledge-base/", skip_duplicates=True)
```

**注意：** API 兼容，代码无需修改，只需初始化参数不同。

## 十一、总结

### 核心优势

**✅ 轻量级架构**
- 无需 Docker 或独立服务器
- 部署简单，一条命令即可
- 适合个人和小团队

**✅ 完全本地化**
- 数据隐私和安全
- 无网络依赖
- 零 API 成本

**✅ 功能完整**
- 智能去重（MD5 + 路径 + 向量相似度）
- 多格式文档支持
- 元数据过滤
- 语义搜索

**✅ 易于维护**
- 文件级备份
- 简单的恢复流程
- 代码易读易扩展

### 技术栈

- **向量数据库**: Qdrant Client (嵌入式模式)
- **嵌入模型**: BGE-M3 (BAAI/bge-m3-base)
- **文档解析**: unstructured
- **Python 版本**: 3.8+

### 适用场景

✅ **推荐使用：**
- 个人知识库
- 小团队文档管理（< 10K 文档）
- 单机使用
- 快速原型开发

❌ **不推荐使用：**
- 大规模生产环境（> 50K 文档）
- 多用户并发访问
- 需要高可用性和容错

### 成功标准

- ✅ 所有文档成功上传
- ✅ 搜索结果准确且相关
- ✅ 响应时间 < 500ms
- ✅ MCP 集成正常工作
- ✅ 备份和恢复机制完善

---

**文档版本:** v2.0 (嵌入式模式)
**最后更新:** 2025-12-28
**维护者:** Indeptrader Project
