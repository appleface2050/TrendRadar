# 知识库迁移至 BGE-M3-base 实施计划

> **创建时间**: 2025-12-28
> **当前模型**: BAAI/bge-small-zh-v1.5
> **目标模型**: BAAI/bge-m3
> **迁移原因**: 支持多语言、提升专业金融领域检索质量、支持长文档（8192 tokens）

---

## 📋 决策分析

### 当前配置
- **模型**: BAAI/bge-small-zh-v1.5
- **向量维度**: 512
- **序列长度**: 512 tokens
- **语言**: 仅中文
- **向量数量**: 223
- **文档数量**: 1

### BGE-M3-base 优势
- ✅ **多语言支持**: 100+ 种语言（满足主要需求）
- ✅ **长文档处理**: 最大 8192 tokens（vs 当前 512）
- ✅ **三种检索模式**: Dense + Sparse + ColBERT 混合检索
- ✅ **专业领域表现**: 在 MTEB/MIRACL 基准测试中表现优异
- ✅ **向量维度**: 1024（更精准的语义表示）

### 性能权衡
⚠️ **关键冲突**: 用户需要"快速问答（< 100ms 响应）"，但 BGE-M3 由于模型更大，推理速度会慢于 bge-small-zh-v1.5：

- **bge-small-zh-v1.5**: 轻量级，适合 < 100ms 响应
- **BGE-M3-base**: 568M 参数，推理速度较慢，通常 100-300ms

**解决方案**: 使用 FP16 混合精度推理和批处理优化来弥补性能差距

## ✅ 推荐决策：迁移到 BGE-M3-base

**理由**：
1. 用户的**核心需求**是多语言支持，这是 BGE-M3 的独特优势
2. 专业金融领域检索和长文档检索都能从 BGE-M3 获得显著提升
3. 速度差距可通过硬件优化和配置调整来缓解
4. 用户已接受重新索引所有文档

---

## 🎯 实施步骤

### 1. 准备阶段

#### 1.1 备份现有知识库
```bash
# 备份 Qdrant 数据目录
cp -r /home/shang/qdrant_data /home/shang/qdrant_data_backup_$(date +%Y%m%d)
```

#### 1.2 检查硬件资源
```bash
# 检查 GPU 显存
nvidia-smi
# 确认至少有 6GB 可用显存（BGE-M3 运行需求）
```

### 2. 代码修改

#### 2.1 修改核心配置文件
**文件**: `knowledge-base/scripts/qdrant_kb.py`

需要修改的参数：
```python
# 第 59 行：向量维度
VECTOR_SIZE = 1024  # 从 512 改为 1024

# 第 67 行：模型名称
model_name: str = "BAAI/bge-m3"  # 从 BAAI/bge-small-zh-v1.5 改为 BAAI/bge-m3
```

#### 2.2 优化推理性能（关键）
在同一文件中添加性能优化：
```python
# 第 94 行：模型加载时启用 FP16
self.model = SentenceTransformer(
    model_name,
    device=device,
    model_kwargs={'torch_dtype': torch.float16}  # 启用 FP16 加速
)
```

#### 2.3 更新其他相关脚本
需要同步修改的文件：
- `knowledge-base/scripts/knowledge_base_server.py`
- `knowledge-base/scripts/qdrant_mcp_fastapi.py`

### 3. 数据迁移

#### 3.1 清空现有知识库
```bash
# 删除旧集合（向量维度不兼容，必须重建）
python3 -c "
from qdrant_client import QdrantClient
client = QdrantClient(path='/home/shang/qdrant_data')
client.delete_collection('knowledge_base')
"
```

#### 3.2 重新上传文档
使用现有脚本批量上传：
```bash
# 使用 setup-knowledge-base.sh 或手动上传
cd /home/shang/git/Indeptrader/knowledge-base
python3 scripts/qdrant_kb.py upload --dir ./documents
```

### 4. 验证测试

#### 4.1 性能基准测试
```python
# 测试查询速度
import time
kb = QdrantKnowledgeBase(model_name="BAAI/bge-m3")

t0 = time.time()
results = kb.search("收益率曲线倒挂的定义", top_k=5)
latency = (time.time() - t0) * 1000
print(f"查询延迟: {latency:.2f}ms")
```

**目标**:
- 简单查询: < 150ms（可接受）
- 复杂查询: < 300ms

#### 4.2 多语言测试
测试中文、英文、其他语言的检索效果

#### 4.3 长文档测试
测试超过 512 tokens 的文档检索

### 5. MCP 服务器重启
```bash
# 重启 Qdrant MCP FastAPI 服务
pkill -f qdrant_mcp_fastapi.py
nohup python3 knowledge-base/scripts/qdrant_mcp_fastapi.py > /dev/null 2>&1 &
```

---

## 📊 预期效果

### 性能对比

| 指标 | bge-small-zh-v1.5 | BGE-M3-base | 变化 |
|------|-------------------|-------------|------|
| **向量维度** | 512 | 1024 | +100% |
| **序列长度** | 512 | 8192 | +1500% |
| **语言支持** | 中文 | 100+ 语言 | ∞ |
| **检索质量** | 中等 | 优秀 | +15-30% |
| **查询延迟** | ~50ms | ~150ms | +200% |
| **显存占用** | ~2GB | ~5GB | +150% |

### 适用场景评估

| 场景 | 适用度 | 说明 |
|------|--------|------|
| **多语言检索** | ⭐⭐⭐⭐⭐ | 核心优势，完美满足 |
| **专业金融检索** | ⭐⭐⭐⭐⭐ | 语义理解更精准 |
| **长文档检索** | ⭐⭐⭐⭐⭐ | 8192 tokens 够用 |
| **深度分析** | ⭐⭐⭐⭐⭐ | 混合检索能力 |
| **快速问答** | ⭐⭐⭐ | 速度下降，但可接受 |

---

## ⚠️ 风险与缓解

### 风险 1: 查询延迟增加
**影响**: 快速问答场景响应时间从 < 100ms 增加到 ~150ms
**缓解**:
- 启用 FP16 混合精度推理（提速 30-50%）
- 使用批处理优化
- 考虑使用量化版本（bge-m3-GGUF）

### 风险 2: 显存占用增加
**影响**: 从 ~2GB 增加到 ~5GB
**缓解**:
- RTX 3070 Ti 8GB 足够使用
- 如遇 OOM，减小 `batch_size` 参数

### 风险 3: 数据迁移失败
**影响**: 知识库不可用
**缓解**:
- 已备份原始数据
- 可快速回滚到 bge-small-zh-v1.5

---

## 📝 关键文件清单

### 需要修改的文件
1. `/home/shang/git/Indeptrader/knowledge-base/scripts/qdrant_kb.py`
   - 第 59 行: `VECTOR_SIZE = 1024`
   - 第 67 行: `model_name = "BAAI/bge-m3"`
   - 第 94 行: 添加 FP16 支持

2. `/home/shang/git/Indeptrader/knowledge-base/scripts/knowledge_base_server.py`
   - 同步修改模型名称和向量维度

3. `/home/shang/git/Indeptrader/knowledge-base/scripts/qdrant_mcp_fastapi.py`
   - 同步修改模型名称和向量维度

### 需要备份的文件/目录
1. `/home/shang/qdrant_data` - Qdrant 数据目录
2. `/home/shang/git/Indeptrader/knowledge-base/.upload_record.json` - 上传记录

---

## 🚀 执行命令摘要

```bash
# 1. 备份数据
cp -r /home/shang/qdrant_data /home/shang/qdrant_data_backup_$(date +%Y%m%d)

# 2. 修改代码（手动编辑上述 3 个文件）

# 3. 删除旧集合
python3 << EOF
from qdrant_client import QdrantClient
client = QdrantClient(path='/home/shang/qdrant_data')
client.delete_collection('knowledge_base')
print("✅ 旧集合已删除")
EOF

# 4. 重新上传文档（假设文档在 knowledge-base/documents）
cd /home/shang/git/Indeptrader/knowledge-base
python3 scripts/qdrant_kb.py upload --dir ./documents

# 5. 测试新模型
python3 << EOF
from scripts.qdrant_kb import QdrantKnowledgeBase
import time

kb = QdrantKnowledgeBase(model_name="BAAI/bge-m3")

# 测试中文
t0 = time.time()
results = kb.search("收益率曲线倒挂", top_k=3)
print(f"中文查询: {(time.time()-t0)*1000:.2f}ms")

# 测试英文
t0 = time.time()
results = kb.search("yield curve inversion", top_k=3)
print(f"英文查询: {(time.time()-t0)*1000:.2f}ms")
EOF

# 6. 重启 MCP 服务
pkill -f qdrant_mcp_fastapi.py
nohup python3 knowledge-base/scripts/qdrant_mcp_fastapi.py > /dev/null 2>&1 &
```

---

## ✅ 验收标准

1. ✅ 模型成功加载（无报错）
2. ✅ 知识库重新索引完成
3. ✅ 中文查询准确率提升
4. ✅ 英文查询可用（多语言支持）
5. ✅ 长文档（>512 tokens）可检索
6. ✅ 平均查询延迟 < 200ms
7. ✅ MCP 服务正常响应

---

## 📚 参考资料

- BGE-M3 官方文档: https://huggingface.co/BAAI/bge-m3
- BGE-M3 论文: https://arxiv.org/pdf/2402.03216.pdf
- FlagEmbedding GitHub: https://github.com/FlagOpen/FlagEmbedding

---

## 📝 执行记录

> 请在执行后填写以下记录

**执行日期**: ___________

**执行人**: ___________

**执行结果**:
- [ ] 备份完成
- [ ] 代码修改完成
- [ ] 旧集合删除
- [ ] 文档重新上传
- [ ] 性能测试通过
- [ ] 多语言测试通过
- [ ] MCP 服务重启成功

**遇到的问题**: _______________________________________________

**解决方案**: _______________________________________________

**备注**: _______________________________________________
