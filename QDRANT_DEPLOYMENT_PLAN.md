# Qdrant 本地部署方案

## 一、项目背景

**项目需求：**
- 构建本地向量数据库知识库系统
- 使用 Docker 部署 Qdrant
- 配置数据持久化
- 提供 Web UI 管理界面
- 集成 Claude Code MCP Server

**核心目标：**
- 完全本地化，数据自主可控
- 无 API 调用成本
- 响应速度快
- 支持文档的智能检索

## 二、技术架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────┐
│          Indeptrader 项目 (WSL2)                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────────┐      ┌──────────────────┐   │
│  │  Qdrant Docker   │      │  Qdrant Web UI   │   │
│  │  (port 6333)     │◄────►│  (port 6335)     │   │
│  │  Vector DB       │      │  Management      │   │
│  └────────┬─────────┘      └──────────────────┘   │
│           │                                        │
│           │ REST API                               │
│           ▼                                        │
│  ┌──────────────────────────────────────────┐     │
│  │  Python Scripts                          │     │
│  │  - qdrant_mcp.py (MCP Server)            │     │
│  │  - qdrant_upload.py (Smart Upload)       │     │
│  │  - qdrant_client.py (Client Wrapper)     │     │
│  │  - embedding_models.py (Embedding)       │     │
│  └──────────────────────────────────────────┘     │
│                                                      │
│  Data Persistence:                                  │
│  /home/shang/data/qdrant/storage  │
└─────────────────────────────────────────────────────┘
```

### 2.2 向量嵌入方案

**推荐方案：本地嵌入模型**
- 模型: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- 向量维度: 384
- 支持中文和英文
- 模型大小: 约 470MB
- 优势: 无需网络调用，响应快，成本低

**备选方案：云端 API**
- DeepSeek Embedding API
- OpenAI Embedding API
- 适用场景: 需要更高质量的向量表示

## 三、目录结构

**重要说明:** Qdrant 数据目录（storage、snapshots、backups）放在项目外的 `/home/shang/data/qdrant/`，以保持项目代码库的整洁。

```
/home/shang/git/Indeptrader/
├── docker/
│   ├── qdrant/
│   │   ├── docker-compose.yml       # Qdrant 主服务
│   │   ├── .env                     # 环境变量
│   │   └── README.md
│   └── qdrant-webui/
│       ├── docker-compose.yml       # Web UI
│       └── README.md
├── knowledge-base/
│   ├── qdrant/                      # [新建] Qdrant 专用目录
│   │   ├── scripts/
│   │   │   ├── qdrant_client.py     # Qdrant 客户端封装
│   │   │   ├── qdrant_mcp.py        # MCP Server
│   │   │   ├── qdrant_upload.py     # 智能上传脚本
│   │   │   └── embedding_models.py  # 嵌入模型
│   │   ├── .upload_record.json      # Qdrant 上传记录
│   │   └── README.md                # Qdrant 使用文档
│   ├── business/
│   ├── project/
│   └── research/
└── devops/                          # [新建] DevOps 脚本目录
    ├── backup_qdrant.sh             # 备份脚本
    └── restore_qdrant.sh            # 恢复脚本

# 数据目录（项目外）
/home/shang/data/qdrant/
├── storage/                         # Qdrant 持久化数据
├── snapshots/                       # 快照备份
└── backups/                         # 压缩备份
```

## 四、Docker 配置

### 4.1 Qdrant Docker Compose

**文件:** `docker/qdrant/docker-compose.yml`

```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:v1.12.0
    container_name: indepctrader-qdrant
    ports:
      - "6333:6333"  # HTTP API
      - "6334:6334"  # gRPC API
    volumes:
      - /home/shang/data/qdrant/storage:/qdrant/storage:cached
    environment:
      - QDRANT__SERVICE__HTTP_PORT=6333
      - QDRANT__SERVICE__GRPC_PORT=6334
      - QDRANT__LOG_LEVEL=INFO
      - QDRANT__SERVICE__MAX_REQUEST_SIZE_MB=32
      - QDRANT__STORAGE__PERFORMANCE__MAX_OPTIMIZATION_THREADS=2
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - qdrant-network

networks:
  qdrant-network:
    driver: bridge
```

### 4.2 Qdrant Web UI Docker Compose

**文件:** `docker/qdrant-webui/docker-compose.yml`

```yaml
version: '3.8'

services:
  qdrant-webui:
    image: qdrant/qdrant-web-ui:latest
    container_name: indepctrader-qdrant-webui
    ports:
      - "6335:8080"
    environment:
      - QDRANT_HOST=http://indepctrader-qdrant:6333
    depends_on:
      - qdrant
    restart: unless-stopped
    networks:
      - qdrant-network

networks:
  qdrant-network:
    external: true
```

注意: 需要先启动 Qdrant，再启动 Web UI（或使用 `external: true` 引用网络）

### 4.3 环境变量配置

**文件:** `docker/qdrant/.env`

```bash
# Qdrant 版本
QDRANT_VERSION=v1.12.0

# 端口配置
QDRANT_HTTP_PORT=6333
QDRANT_GRPC_PORT=6334

# 数据持久化路径
QDRANT_STORAGE_PATH=/qdrant/storage
QDRANT_SNAPSHOTS_PATH=/qdrant/storage/snapshots

# 性能配置
QDRANT_MAX_OPTIMIZATION_THREADS=2
QDRANT_MAX_REQUEST_SIZE_MB=32

# 内存限制
QDRANT_MEMORY_LIMIT=4G

# Web UI
QDRANT_WEBUI_PORT=6335

# 嵌入模型配置
EMBEDDING_MODEL=local  # local | deepseek | openai
EMBEDDING_MODEL_NAME=paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_VECTOR_SIZE=384

# Collection 配置
COLLECTION_NAME=indepctrader_kb
```

## 五、Qdrant Collection 设计

### 5.1 Collection 结构

```python
{
    "collection_name": "indepctrader_kb",
    "vector_size": 384,
    "distance": "Cosine",
    "payload_schema": {
        "doc_name": "string",           # 文档名称
        "doc_path": "string",           # 文档路径
        "doc_type": "string",           # 文档类型: md/pdf/txt
        "category": "string",           # 分类: business/project/research
        "file_hash": "string",          # 文件 MD5 hash
        "upload_time": "string",        # 上传时间
        "file_size": "integer",         # 文件大小
        "chunk_index": "integer",       # 分块索引
        "chunk_text": "string",         # 分块文本内容
        "source": "string"              # 来源: bigmodel/local
    }
}
```

### 5.2 HNSW 索引配置

```python
hnsw_config = {
    "m": 16,                # 每个节点的最大连接数
    "ef_construct": 100,    # 构建索引时的搜索范围
}

optimizer_config = {
    "indexing_threshold": 20000,  # 达到 20000 个向量后开始索引
}
```

### 5.3 文档分块策略

```python
CHUNK_CONFIG = {
    "max_chunk_size": 500,        # 最大分块大小（字符数）
    "chunk_overlap": 50,          # 分块重叠（字符数）
    "chunk_by_paragraph": True,   # 按段落分块
    "min_chunk_size": 100,        # 最小分块大小
}
```

## 六、核心代码实现

### 6.1 关键文件清单

**需要新建的文件：**

1. `knowledge-base/qdrant/scripts/qdrant_client.py`
   - Qdrant 客户端封装
   - 提供 Collection 管理、CRUD 操作
   - 嵌入模型管理

2. `knowledge-base/qdrant/scripts/qdrant_mcp.py`
   - MCP Server 实现
   - 提供 Claude Code 集成接口
   - 工具: `search_knowledge`, `chat_with_knowledge`

3. `knowledge-base/qdrant/scripts/qdrant_upload.py`
   - 智能上传脚本
   - 支持 hash 检查、增量上传
   - 文档分块和向量化

4. `knowledge-base/qdrant/scripts/embedding_models.py`
   - 嵌入模型抽象层
   - 支持本地模型（sentence-transformers）
   - 支持云端 API（DeepSeek/OpenAI）

5. `docker/qdrant/docker-compose.yml`
   - Qdrant Docker 配置

6. `docker/qdrant/.env`
   - 环境变量配置

7. `docker/qdrant-webui/docker-compose.yml`
   - Web UI Docker 配置

8. `devops/backup_qdrant.sh`
   - Qdrant 备份脚本

9. `devops/restore_qdrant.sh`
   - Qdrant 恢复脚本

**需要修改的文件：**

1. `~/.config/claude-code/mcp_config.json` (MCP 配置)
   - 添加 Qdrant MCP Server 配置
   - 路径: `knowledge-base/qdrant/scripts/qdrant_mcp.py`

**注意:** 无需修改 `.gitignore`，因为数据目录在项目外

### 6.2 核心类设计

**QdrantKnowledgeBase 类** (`qdrant_client.py`)

```python
class QdrantKnowledgeBase:
    """Qdrant 知识库客户端"""

    def __init__(self, host="localhost", port=6333, collection_name="indepctrader_kb"):
        # 初始化 Qdrant 客户端
        # 初始化嵌入模型
        pass

    def create_collection(self):
        """创建 Collection"""
        pass

    def upload_document(self, file_path: str, category: str = "project"):
        """上传文档并索引

        步骤:
        1. 读取文件内容
        2. 文档分块（按段落）
        3. 生成嵌入向量
        4. 上传到 Qdrant
        """
        pass

    def search(self, query: str, top_k: int = 5, category: str = None):
        """检索知识库

        返回格式与 BigModel 一致
        """
        pass

    def delete_document(self, doc_name: str):
        """删除文档（所有分块）"""
        pass

    def get_collection_info(self):
        """获取 Collection 信息"""
        pass
```

**EmbeddingModel 类** (`embedding_models.py`)

```python
class EmbeddingModel:
    """嵌入模型基类"""

    def encode(self, text: str) -> List[float]:
        """编码文本为向量"""
        pass

class LocalEmbeddingModel(EmbeddingModel):
    """本地 sentence-transformers 模型"""

    def __init__(self, model_name="paraphrase-multilingual-MiniLM-L12-v2"):
        # 加载模型
        pass

class DeepSeekEmbeddingModel(EmbeddingModel):
    """DeepSeek Embedding API"""

    def __init__(self, api_key: str):
        # 初始化 API 客户端
        pass
```

### 6.3 上传记录格式扩展

**Qdrant 专用格式** (`knowledge-base/qdrant/.upload_record.json`):

```json
{
    "文档名称.md": {
        "hash": "md5hash",
        "document_id": "uuid-v4",
        "upload_time": "2025-12-27T22:26:02",
        "file_size": 19284,
        "file_mtime": 1766825707.895223,

        // Qdrant 新增字段
        "vector_db": "qdrant",
        "collection": "indepctrader_kb",
        "chunks_count": 12,
        "embedding_model": "paraphrase-multilingual-MiniLM-L12-v2",
        "point_ids": ["uuid-1", "uuid-2", ...]
    }
}
```

## 七、部署步骤

### Phase 1: 准备环境 (1-2 小时)

**1.1 创建目录结构**
```bash
# 项目内目录
mkdir -p knowledge-base/qdrant/scripts
mkdir -p devops
mkdir -p docker/qdrant
mkdir -p docker/qdrant-webui

# 项目外数据目录
mkdir -p /home/shang/data/qdrant/storage
mkdir -p /home/shang/data/qdrant/snapshots
mkdir -p /home/shang/data/qdrant/backups
```

**1.2 安装 Python 依赖**
```bash
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    qdrant-client \
    sentence-transformers \
    pypdf \
    python-docx \
    openpyxl
```

**1.3 创建 Docker 配置文件**
- 创建 `docker/qdrant/docker-compose.yml`
- 创建 `docker/qdrant/.env`
- 创建 `docker/qdrant-webui/docker-compose.yml`

### Phase 2: 部署 Qdrant (30 分钟)

**2.1 启动 Qdrant**
```bash
cd docker/qdrant
docker-compose up -d
```

**2.2 验证服务**
```bash
# 检查容器状态
docker ps | grep qdrant

# 检查健康状态
curl http://localhost:6333/health

# 查看版本信息
curl http://localhost:6333/
```

**2.3 启动 Web UI**
```bash
cd docker/qdrant-webui
docker-compose up -d
```

**2.4 访问 Web UI**
- 浏览器打开: `http://localhost:6335`
- 确认可以连接到 Qdrant

### Phase 3: 开发核心代码 (2-3 天)

**3.1 实现 `embedding_models.py`**
- 本地模型类
- API 模型类（可选）
- 测试编码功能

**3.2 实现 `qdrant_client.py`**
- Qdrant 客户端封装
- Collection 管理
- CRUD 操作
- 测试基本功能

**3.3 实现 `qdrant_upload.py`**
- 智能上传逻辑
- hash 检查
- 文档分块
- 向量化
- 测试上传单个文档

**3.4 实现 `qdrant_mcp.py`**
- MCP Server
- 实现知识库检索接口
- 测试工具调用

### Phase 4: 数据迁移 (1 天)

**4.1 创建 Collection**
```bash
python3 -c "
from knowledge_base.qdrant.scripts.qdrant_client import QdrantKnowledgeBase
kb = QdrantKnowledgeBase()
kb.create_collection()
print('✅ Collection 创建成功')
"
```

**4.2 运行智能上传**
```bash
python3 knowledge-base/qdrant/scripts/qdrant_upload.py \
    --dir knowledge-base \
    --delete-old
```

**4.3 验证上传结果**
- 在 Web UI 中查看 Collection 统计
- 确认向量数量
- 运行测试查询

### Phase 5: 更新 MCP 配置 (5 分钟)

**5.1 备份现有配置**
```bash
cp ~/.config/claude-code/mcp_config.json \
   ~/.config/claude-code/mcp_config.json.backup
```

**5.2 更新配置**
```json
{
  "mcpServers": {
    "qdrant-kb": {
      "command": "python3",
      "args": [
        "knowledge-base/qdrant/scripts/qdrant_mcp.py"
      ]
    }
  }
}
```

**5.3 重启 Claude Code**
- 关闭 Claude Code
- 重新打开

### Phase 6: 测试验证 (1-2 周)

**6.1 功能测试**
- 测试 `search_knowledge` 工具
- 测试 `chat_with_knowledge` 工具
- 验证检索结果的准确性和完整性

**6.2 性能测试**
- 测试响应时间
- 测试并发查询
- 监控资源使用

**6.3 优化调整**
- 根据测试结果调优参数
- 优化分块策略
- 改进检索质量

## 八、备份和恢复策略

### 8.1 自动备份

**备份脚本:** `devops/backup_qdrant.sh`

```bash
#!/bin/bash
# 文件路径: /home/shang/git/Indeptrader/devops/backup_qdrant.sh

BACKUP_DIR="/home/shang/data/qdrant/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建快照
curl -X POST "http://localhost:6333/collections/indepctrader_kb/snapshots"

# 复制到备份目录
docker cp indepctrader-qdrant:/qdrant/storage/snapshots/${SNAPSHOT_NAME} \
    ${BACKUP_DIR}/${SNAPSHOT_NAME}

# 压缩
gzip ${BACKUP_DIR}/${SNAPSHOT_NAME}

# 清理旧备份（保留 7 天）
find ${BACKUP_DIR} -name "qdrant_snapshot_*.gz" -mtime +7 -delete
```

**定时任务:**
```bash
# 每天凌晨 2 点备份
crontab -e
0 2 * * * /home/shang/git/Indeptrader/devops/backup_qdrant.sh
```

### 8.2 灾难恢复

**恢复脚本:** `devops/restore_qdrant.sh`

```bash
#!/bin/bash
# 文件路径: /home/shang/git/Indeptrader/devops/restore_qdrant.sh

SNAPSHOT_FILE=$1

# 停止 Qdrant
cd docker/qdrant
docker-compose down

# 备份当前数据
mv /home/shang/data/qdrant/storage \
   /home/shang/data/qdrant/storage_backup_$(date +%Y%m%d)

# 创建新存储目录
mkdir -p /home/shang/data/qdrant/storage

# 解压快照
gunzip -c /home/shang/data/qdrant/backups/${SNAPSHOT_FILE} > \
    /home/shang/data/qdrant/storage/snapshot

# 启动 Qdrant
docker-compose up -d
```

## 九、关键文件路径总结

### 必须创建的文件（按优先级）

1. `docker/qdrant/docker-compose.yml`
2. `docker/qdrant/.env`
3. `docker/qdrant-webui/docker-compose.yml`
4. `knowledge-base/qdrant/scripts/embedding_models.py`
5. `knowledge-base/qdrant/scripts/qdrant_client.py`
6. `knowledge-base/qdrant/scripts/qdrant_upload.py`
7. `knowledge-base/qdrant/scripts/qdrant_mcp.py`
8. `devops/backup_qdrant.sh`
9. `devops/restore_qdrant.sh`

### 必须修改的文件

1. `~/.config/claude-code/mcp_config.json` - 更新 MCP Server 路径

**注意:** 无需修改 `.gitignore`，因为数据目录在项目外

## 十、预期效果

**优势:**
- ✅ 完全本地化，无需网络
- ✅ 数据隐私和安全
- ✅ 无 API 调用成本
- ✅ 响应速度快（本地推理）
- ✅ 可完全控制和定制

**性能指标:**
- 向量维度: 384
- 单文档处理时间: 1-3 秒（取决于文档大小）
- 检索响应时间: < 100ms
- 内存占用: 2-4GB（Docker 容器）
- 磁盘占用: 初始约 500MB（模型 + 数据）

## 十一、风险评估

**主要风险:**

1. **向量质量风险**
   - 风险: 本地模型可能不如云端模型
   - 缓解: 选择高质量的嵌入模型，通过测试验证效果

2. **性能风险**
   - 风险: WSL2 环境性能可能受限
   - 缓解: 优化资源配置，必要时使用云端嵌入 API

3. **数据丢失风险**
   - 风险: Docker 容器删除
   - 缓解: 定期备份快照，使用数据卷持久化

4. **兼容性风险**
   - 风险: MCP 接口变化
   - 缓解: 保持接口兼容性，充分测试

## 十二、后续优化方向

**短期优化（1-2 周）:**
- 调优分块策略
- 优化搜索参数
- 添加更多文档类型支持

**中期优化（1-2 月）:**
- 实现增量更新
- 添加文档版本管理
- 集成其他嵌入模型

**长期优化（3-6 月）:**
- GPU 加速（如果需要）
- 分布式部署
- 多模态支持（图片、表格）

## 十三、总结

本方案提供了完整的本地 Qdrant 部署架构，从 Docker 配置到代码实现，再到数据迁移和备份恢复，覆盖了所有关键环节。

**核心优势:**
- 完全本地化，数据自主可控
- 无 API 成本，长期使用更经济
- 响应速度快，用户体验好

**实施建议:**
- 分阶段实施，逐步验证
- 充分测试，确保稳定
- 定期备份，保障数据安全

**预期时间表:**
- Phase 1-2: 环境准备 (1-2 小时)
- Phase 3: 代码开发 (2-3 天)
- Phase 4: 数据迁移 (1 天)
- Phase 5-6: 测试验证 (1-2 周)

**成功标准:**
- Qdrant 服务稳定运行
- 所有文档成功迁移
- 检索效果满足需求
- Claude Code MCP 集成正常
