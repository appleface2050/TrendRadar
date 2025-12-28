# Qdrant 本地知识库使用指南

## 一、部署概况

**部署时间：** 2025-12-28
**部署模式：** Qdrant Client 嵌入式模式（本地持久化）
**状态：** ✅ 已成功部署并正常运行

## 二、技术配置

### 2.1 核心组件

| 组件 | 版本/型号 | 说明 |
|------|----------|------|
| **向量数据库** | Qdrant Client（嵌入式模式） | 无需独立服务器 |
| **嵌入模型** | BAAI/bge-small-zh-v1.5 | 512 维向量，支持中英文 |
| **文档解析** | unstructured[md] | 支持 Markdown 文档 |
| **存储路径** | `/home/shang/qdrant_data` | 用户主目录，独立于项目代码 |

### 2.2 与原计划的调整

**原计划配置：**
- 嵌入模型：`BAAI/bge-m3-base`（1024 维）
- 向量维度：1024

**实际部署配置：**
- 嵌入模型：`BAAI/bge-small-zh-v1.5`（512 维）
- 向量维度：512

**调整原因：**
1. `BAAI/bge-m3-base` 在国内网络环境下载失败
2. 使用 HuggingFace 镜像（`hf-mirror.com`）测试后确认 `BAAI/bge-small-zh-v1.5` 可用
3. `bge-small-zh-v1.5` 性能优异，适合中文场景

## 三、当前状态

### 3.1 数据统计

```
存储位置：/home/shang/qdrant_data/
数据大小：1.2MB
文档数量：13 个
文本块数：169 个
文档类型：Markdown (.md)
分类：project（项目）、research（研究）
```

### 3.2 已上传文档列表

**Project 分类（7 个）：**
- DEPLOYMENT_CONVERSATION.md
- DEPLOYMENT_GUIDE.md
- MCP_Top100_Summary.md
- QUICK_START.md
- README.md
- claude-skills-guide.md
- 知识库Token节省演示.md
- 知识库文档组织方案.md

**Research 分类（3 个）：**
- 构建面向复杂分析的本地知识库系统：架构、实现与演进路线深度指南.md
- 面向中国A股自营交易的中低频量化因子挖掘：从研究到生产的完整闭环.md
- 面向宏观、行业与公司对比分析的金融看板：风格、架构与实现路径.md

### 3.3 自动去重

系统成功跳过了 3 个重复文档（基于 MD5 内容哈希）：
- 面向宏观、行业与公司对比分析的金融看板：风格、架构与实现路径.md
- 构建面向复杂分析的本地知识库系统：架构、实现与演进路线深度指南.md
- 面向中国A股自营交易的中低频量化因子挖掘：从研究到生产的完整闭环.md

## 四、使用方法

### 4.1 命令行接口

**前置条件：**

程序会自动从项目根目录的 `settings.py` 文件读取 `HF_ENDPOINT` 配置，无需手动设置环境变量。

如需自定义配置，可编辑 `settings.py`：
```bash
HF_ENDPOINT="https://hf-mirror.com"
```

#### 搜索文档

```bash
# 基本搜索
python3 knowledge-base/scripts/qdrant_kb.py search --query "向量数据库"

# 返回前 10 个结果
python3 knowledge-base/scripts/qdrant_kb.py search --query "MCP 服务器" --top-k 10

# 按类别搜索
python3 knowledge-base/scripts/qdrant_kb.py search --query "API" --category project
```

#### 列出文档

```bash
# 列出所有文档
python3 knowledge-base/scripts/qdrant_kb.py list

# 按类别筛选
python3 knowledge-base/scripts/qdrant_kb.py list --category project
python3 knowledge-base/scripts/qdrant_kb.py list --category research
```

#### 上传文档

```bash
# 上传单个文件
python3 knowledge-base/scripts/qdrant_kb.py upload --file new_doc.md

# 批量上传目录（自动跳过重复文档）
python3 knowledge-base/scripts/qdrant_kb.py upload --dir knowledge-base/

# 指定存储路径
python3 knowledge-base/scripts/qdrant_kb.py upload --dir knowledge-base/ --storage /custom/path
```

#### 删除文档

```bash
# 删除指定文档
python3 knowledge-base/scripts/qdrant_kb.py delete --file outdated.md
```

### 4.2 Python API 使用

```python
from knowledge_base.scripts.qdrant_kb import QdrantKnowledgeBase

# 初始化知识库
kb = QdrantKnowledgeBase(
    storage_path="/home/shang/qdrant_data",
    model_name="BAAI/bge-small-zh-v1.5",
    device="cuda"  # 或 "cpu"
)

# 搜索文档
results = kb.search("向量数据库", top_k=5)
for i, result in enumerate(results, 1):
    print(f"[{i}] 相关度: {result['score']:.4f}")
    print(f"    文件: {result['metadata']['file_name']}")
    print(f"    内容: {result['text'][:100]}...")

# 按类别搜索
results = kb.search("MCP", filters={"category": "project"})

# 上传文档
result = kb.upload_document("new_doc.md")
print(f"上传了 {result['chunks']} 个文本块")

# 批量上传目录
results = kb.upload_directory("knowledge-base/", skip_duplicates=True)

# 删除文档
kb.delete_document("old_doc.md")

# 获取集合信息
info = kb.get_collection_info()
print(f"文档总数: {info['total_documents']}")
print(f"文本块总数: {info['total_chunks']}")
```

## 五、部署细节

### 5.1 依赖安装

```bash
# 核心依赖
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    qdrant-client \
    sentence-transformers

# Markdown 解析支持
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple "unstructured[md]"

# 完整安装（支持所有格式）
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple "unstructured[all-in-one]"
```

### 5.2 代码修复记录

**问题 1：API 变更**
```python
# 原代码（不兼容新版 qdrant-client）
results = self.client.search(
    collection_name=self.COLLECTION_NAME,
    query_vector=query_vector.tolist(),
    ...
)

# 修复后
results = self.client.query_points(
    collection_name=self.COLLECTION_NAME,
    query=query_vector.tolist(),
    ...
).points
```

**问题 2：模型配置调整**
```python
# 原配置
VECTOR_SIZE = 1024
model_name: str = "BAAI/bge-m3-base"

# 调整后
VECTOR_SIZE = 512
model_name: str = "BAAI/bge-small-zh-v1.5"
```

## 六、数据管理

### 6.1 备份

**方法 1：直接备份目录**
```bash
# 创建备份
tar -czf qdrant_kb_backup_$(date +%Y%m%d).tar.gz /home/shang/qdrant_data/

# 恢复备份
tar -xzf qdrant_kb_backup_20251228.tar.gz -C /home/shang/
```

**方法 2：使用备份脚本**
```bash
# 创建定期备份脚本
cat > devops/backup_qdrant_kb.sh << 'EOF'
#!/bin/bash
BACKUP_ROOT="/home/shang/backups/qdrant_kb"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SOURCE_DIR="/home/shang/qdrant_data"

mkdir -p ${BACKUP_ROOT}
tar -czf ${BACKUP_ROOT}/qdrant_kb_${TIMESTAMP}.tar.gz -C ${SOURCE_DIR} .

# 清理 30 天前的备份
find ${BACKUP_ROOT} -name "qdrant_kb_*.tar.gz" -mtime +30 -delete

echo "✅ 备份完成: qdrant_kb_${TIMESTAMP}.tar.gz"
EOF

chmod +x devops/backup_qdrant_kb.sh

# 设置定时任务（每天凌晨 2 点备份）
crontab -e
0 2 * * * /home/shang/git/Indeptrader/devops/backup_qdrant_kb.sh
```

### 6.2 数据迁移

**迁移到新位置：**
```bash
# 停止使用知识库的所有进程

# 复制数据到新位置
cp -r /home/shang/qdrant_data /new/path/qdrant_data

# 更新代码中的存储路径
kb = QdrantKnowledgeBase(storage_path="/new/path/qdrant_data")
```

## 七、故障排除

### 7.1 常见问题

**Q1: 模型下载失败**

程序已自动配置 HuggingFace 镜像（`https://hf-mirror.com`），如仍有问题：

```bash
# 检查 settings.py 中的配置
cat settings.py

# 或临时覆盖环境变量
HF_ENDPOINT=https://hf-mirror.com python3 knowledge-base/scripts/qdrant_kb.py search --query "测试"
```

**Q2: 搜索无结果**
```bash
# 检查集合是否为空
python3 knowledge-base/scripts/qdrant_kb.py list

# 重新上传文档
python3 knowledge-base/scripts/qdrant_kb.py upload --dir knowledge-base/
```

**Q3: 向量维度不匹配**
```python
# 删除旧数据，重新初始化
rm -rf /home/shang/qdrant_data

# 重新上传文档
python3 knowledge-base/scripts/qdrant_kb.py upload --dir knowledge-base/
```

**Q4: 内存不足**
```python
# 使用 CPU 模式
kb = QdrantKnowledgeBase(device="cpu")

# 或使用更小的模型
kb = QdrantKnowledgeBase(model_name="paraphrase-multilingual-MiniLM-L12-v2")
```

### 7.2 调试模式

```python
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)

kb = QdrantKnowledgeBase()
results = kb.search("测试查询")
```

## 八、性能参考

**基于 BAAI/bge-small-zh-v1.5 (512 维)：**

| 指标 | 数值 |
|------|------|
| 单文档处理时间 | 1-3 秒 |
| 搜索响应时间 | 50-150ms |
| 内存占用 | 1-2GB（Python 进程） |
| 磁盘占用 | 1.2MB（13 个文档） |
| 平均每文档增量 | ~100KB |

## 九、架构说明

```
┌─────────────────────────────────────────────────────┐
│          Indeptrader 项目 (WSL2)                    │
├─────────────────────────────────────────────────────┤
│                                                      │
│  Python 应用进程                                     │
│  ┌────────────────────────────────────────────┐    │
│  │  QdrantKnowledgeBase (qdrant_kb.py)        │    │
│  │                                             │    │
│  │  - QdrantClient (embedded mode)            │    │
│  │  - BAAI/bge-small-zh-v1.5 嵌入模型         │    │
│  │  - 文档分块 (500 字符/块)                  │    │
│  │  - 智能去重 (MD5 + 文件路径)               │    │
│  └────────────────────────────────────────────┘    │
│                     ↓                                │
│  ┌────────────────────────────────────────────┐    │
│  │  本地存储                                   │    │
│  │  /home/shang/qdrant_data/                  │    │
│  │  - collection 数据 (1.2MB)                  │    │
│  │  - 索引文件                                │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**数据流：**
```
文档 → 解析 → 分块 → 向量化 → Qdrant 存储
                ↓
            MD5 去重检查
```

## 十、下一步计划

### 10.1 MCP Server 集成（待实施）

**目标：** 在 Claude Code 中直接访问知识库

**步骤：**
1. 创建 `knowledge-base/scripts/qdrant_mcp.py`
2. 实现 MCP 工具：`search_knowledge`, `chat_with_knowledge`
3. 更新 Claude Code MCP 配置文件

### 10.2 功能优化

- [ ] 添加增量更新功能（检测文件变化）
- [ ] 优化分块策略（可配置块大小）
- [ ] 支持更多文档格式（PDF、Word）
- [ ] 添加文档标签系统
- [ ] 实现 RAG 问答功能

## 十一、参考资料

- **核心代码：** [knowledge-base/scripts/qdrant_kb.py](knowledge-base/scripts/qdrant_kb.py)
- **部署方案：** [QDRANT_DEPLOYMENT_PLAN.md](QDRANT_DEPLOYMENT_PLAN.md)
- **Qdrant 官方文档：** https://qdrant.tech/documentation/
- **BGE 模型：** https://huggingface.co/BAAI/bge-small-zh-v1.5

## 十二、快速参考

**配置文件：**
```bash
# HF_ENDPOINT 配置已存储在 settings.py
# 程序会自动加载，无需手动设置
```

**常用命令：**
```bash
# 搜索
python3 knowledge-base/scripts/qdrant_kb.py search --query "关键词"

# 列表
python3 knowledge-base/scripts/qdrant_kb.py list

# 上传
python3 knowledge-base/scripts/qdrant_kb.py upload --dir knowledge-base/

# 删除
python3 knowledge-base/scripts/qdrant_kb.py delete --file filename.md
```

**数据位置：**
```bash
# 数据目录
/home/shang/qdrant_data/

# 上传记录
knowledge-base/.upload_record.json
```

---

**文档版本：** v1.0
**最后更新：** 2025-12-28
**维护者：** Indeptrader Project
