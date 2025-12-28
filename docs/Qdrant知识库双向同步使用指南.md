# Qdrant 知识库双向同步使用指南

> **更新时间**: 2025-12-28
> **版本**: 1.0.0

## 概述

`sync_knowledge_base.py` 是一个专门用于 Qdrant 本地向量知识库的双向同步脚本，能够自动确保知识库与本地文件系统的一致性。

## 核心特性

### ✅ 双向同步
- **删除本地已不存在的文件**：当你删除 `knowledge-base` 目录中的文件后，同步脚本会自动从 Qdrant 中删除对应的向量数据
- **添加本地新文件**：自动将新添加的文件上传到知识库

### ✅ 自动服务管理
- **自动停止服务**：同步前自动停止知识库服务（释放 Qdrant 本地存储锁）
- **自动重启服务**：同步完成后自动重启知识库服务
- **智能检测**：自动检测运行中的服务进程

### ✅ 灵活的同步模式
- **完整同步**（默认）：删除 + 添加
- **仅删除模式**：`--delete-only`
- **仅添加模式**：`--add-only`
- **预览模式**：`--dry-run`（不执行实际操作）
- **禁用自动重启**：`--no-auto-restart`

## 安装位置

```
/home/shang/git/Indeptrader/knowledge-base/scripts/sync_knowledge_base.py
```

## 使用方法

### 1. 完整同步（推荐）

默认会自动停止和重启知识库服务：

```bash
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/sync_knowledge_base.py \
  --dir /home/shang/git/Indeptrader/knowledge-base
```

### 2. 仅删除本地已不存在的文件

当你删除了一些文档，只想同步删除操作：

```bash
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/sync_knowledge_base.py \
  --dir /home/shang/git/Indeptrader/knowledge-base \
  --delete-only
```

### 3. 仅添加新文件

当你添加了一些新文档，只想上传新文件：

```bash
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/sync_knowledge_base.py \
  --dir /home/shang/git/Indeptrader/knowledge-base \
  --add-only
```

### 4. 预览模式

查看将要执行的操作，但不实际修改数据：

```bash
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/sync_knowledge_base.py \
  --dir /home/shang/git/Indeptrader/knowledge-base \
  --dry-run
```

### 5. 禁用自动重启

如果你已经手动停止了知识库服务：

```bash
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/sync_knowledge_base.py \
  --dir /home/shang/git/Indeptrader/knowledge-base \
  --no-auto-restart
```

## 命令行参数

| 参数 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `--dir` | ✅ | - | 本地知识库目录路径 |
| `--storage` | ❌ | `/home/shang/qdrant_data` | Qdrant 数据存储路径 |
| `--qdrant-url` | ❌ | - | Qdrant 服务 URL（例如：http://localhost:6333） |
| `--qdrant-port` | ❌ | `6333` | Qdrant 服务端口 |
| `--model-name` | ❌ | `BAAI/bge-small-zh-v1.5` | 嵌入模型名称 |
| `--device` | ❌ | `cuda` | 计算设备（cuda 或 cpu） |
| `--delete-only` | ❌ | - | 仅删除本地已不存在的文件 |
| `--add-only` | ❌ | - | 仅添加本地新文件 |
| `--dry-run` | ❌ | - | 预览模式，不执行实际操作 |
| `--chunk-size` | ❌ | `500` | 文本块大小 |
| `--quiet` | ❌ | - | 静默模式，减少输出 |
| `--no-auto-restart` | ❌ | - | 禁用自动停止和重启服务 |
| `--start-script` | ❌ | `start_kb_server.sh` | 知识库服务启动脚本路径 |

## 工作流程

### 完整同步流程

```
1. 停止知识库服务
   ├─ 检测运行中的服务进程
   ├─ 停止所有 knowledge_base_server.py 进程
   └─ 等待进程完全退出

2. 扫描和对比
   ├─ 扫描 Qdrant 中的所有文件
   ├─ 扫描本地 knowledge-base 目录
   └─ 对比差异（需要删除 / 需要添加）

3. 执行同步
   ├─ 删除本地已不存在的文件（从 Qdrant）
   └─ 添加本地新文件（上传到 Qdrant）

4. 重启知识库服务
   ├─ 使用启动脚本启动服务
   ├─ 等待服务启动
   └─ 验证服务状态
```

## 输出示例

### 同步开始

```
======================================================================
🔄 Qdrant 知识库双向同步
======================================================================
📁 本地目录: /home/shang/git/Indeptrader/knowledge-base
🗑️  删除模式: 是
📤 添加模式: 是
👀 预览模式: 否
======================================================================

📊 正在扫描 Qdrant 中的文件...
   ✅ Qdrant 中共有 16 个文件

📁 正在扫描本地目录: /home/shang/git/Indeptrader/knowledge-base
   ✅ 本地共有 17 个支持的文件

🔍 对比文件差异...
   需要删除: 2 个文件
   需要添加: 3 个文件
```

### 删除操作

```
🗑️  准备删除 2 个本地已不存在的文件:
   - BigModel_Knowledge_MCP_Server_使用文档.md
   - 智能知识库上传脚本使用指南.md

[1/2] 删除: BigModel_Knowledge_MCP_Server_使用文档.md
   ✅ 成功删除 17 个数据块
[2/2] 删除: 智能知识库上传脚本使用指南.md
   ✅ 成功删除 14 个数据块
```

### 添加操作

```
📤 准备添加 3 个新文件:
   + 构建面向复杂分析的本地知识库系统：架构、实现与演进路线深度指南.md
   + 面向中国A股自营交易的中低频量化因子挖掘：从研究到生产的完整闭环.md
   + 面向宏观、行业与公司对比分析的金融看板：风格、架构与实现路径.md

[1/3] 添加: 构建面向复杂分析的本地知识库系统...
   📄 处理文件: ...
   🔍 解析文档内容...
   📊 切分为 20 个块
   ⬆️  上传到 Qdrant...
   ✅ 上传成功: 20 个块
```

### 同步完成

```
======================================================================
📊 同步完成
======================================================================

🗑️  删除操作:
   总计: 2 个文件
   ✅ 成功: 2 个
   ❌ 失败: 0 个

📤 添加操作:
   总计: 3 个文件
   ✅ 成功: 3 个
   ⏭️  跳过: 0 个
   ❌ 失败: 0 个

======================================================================
```

## 常见使用场景

### 场景 1：删除过时文档

```bash
# 1. 删除 knowledge-base/ 中的过时文档
rm /home/shang/git/Indeptrader/knowledge-base/research/旧报告.md

# 2. 运行同步脚本
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/sync_knowledge_base.py \
  --dir /home/shang/git/Indeptrader/knowledge-base

# 3. 完成！Qdrant 中对应的向量数据已被删除
```

### 场景 2：添加新研究

```bash
# 1. 将新研究报告放到 knowledge-base/research/ 目录
cp ~/Downloads/新研究报告.md /home/shang/git/Indeptrader/knowledge-base/research/

# 2. 运行同步脚本
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/sync_knowledge_base.py \
  --dir /home/shang/git/Indeptrader/knowledge-base

# 3. 完成！新文档已上传到知识库
```

### 场景 3：批量更新

```bash
# 1. 删除多个旧文档，添加多个新文档
rm knowledge-base/research/旧报告1.md
rm knowledge-base/research/旧报告2.md
cp ~/新研究报告1.md knowledge-base/research/
cp ~/新研究报告2.md knowledge-base/research/

# 2. 运行一次同步脚本即可
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/sync_knowledge_base.py \
  --dir /home/shang/git/Indeptrader/knowledge-base

# 3. 完成！自动处理所有删除和添加操作
```

## 技术细节

### 支持的文件类型

- `.md` - Markdown 文件
- `.txt` - 纯文本文件
- `.pdf` - PDF 文档
- `.docx`, `.doc` - Word 文档
- `.xlsx`, `.xls` - Excel 表格
- `.csv` - CSV 文件
- `.ppt`, `.pptx` - PowerPoint 演示文稿

### 元数据分类

脚本会自动根据文件路径识别文档类别：

| 目录路径 | 类别 |
|----------|------|
| `knowledge-base/project/` | `project` |
| `knowledge-base/research/` | `research` |
| `knowledge-base/business/` | `business` |
| 其他 | `other` |

### 去重策略

1. **基于文件路径去重**：检查 Qdrant 中是否已存在相同路径的文件
2. **基于 MD5 哈希去重**：计算文件内容的 MD5 哈希值

### 服务管理

- **停止服务**：使用 `pgrep` 和 `kill` 停止 `knowledge_base_server.py` 进程
- **启动服务**：使用 `start_kb_server.sh` 脚本
- **验证启动**：检查端口 8000 是否开放

## 故障排查

### 问题 1：无法停止服务

**症状**：提示"服务仍在运行"

**解决方案**：
```bash
# 手动停止服务
pkill -9 -f knowledge_base_server.py

# 然后运行同步（使用 --no-auto-restart）
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/sync_knowledge_base.py \
  --dir /home/shang/git/Indeptrader/knowledge-base \
  --no-auto-restart

# 手动启动服务
bash /home/shang/git/Indeptrader/knowledge-base/scripts/start_kb_server.sh
```

### 问题 2：启动脚本不存在

**症状**：提示"启动脚本不存在"

**解决方案**：
```bash
# 检查脚本是否存在
ls -l /home/shang/git/Indeptrader/knowledge-base/scripts/start_kb_server.sh

# 如果不存在，使用 --no-auto-restart 手动管理服务
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/sync_knowledge_base.py \
  --dir /home/shang/git/Indeptrader/knowledge-base \
  --no-auto-restart
```

### 问题 3：Qdrant 存储被锁定

**症状**：RuntimeError: Storage folder is already accessed

**解决方案**：
```bash
# 确保没有其他进程在使用 Qdrant
ps aux | grep qdrant

# 使用 --no-auto-restart 参数
python3 /home/shang/git/Indeptrader/knowledge-base/scripts/sync_knowledge_base.py \
  --dir /home/shang/git/Indeptrader/knowledge-base \
  --no-auto-restart
```

## 性能数据

基于当前环境（WSL2, RTX 3070 Ti, 64GB RAM）：

- **文档数量**：17 个文件
- **总数据点**：~200 个向量块
- **同步耗时**：~30 秒（包括自动停止和重启服务）
- **删除操作**：< 1 秒/文件
- **添加操作**：5-10 秒/文件（取决于文档大小）

## 最佳实践

1. **定期同步**：在添加或删除文档后及时运行同步
2. **使用预览模式**：大规模更新前先用 `--dry-run` 预览
3. **备份重要数据**：删除操作不可逆，建议定期备份 Qdrant 数据
4. **监控服务状态**：同步后确认知识库服务正常运行

## 相关文档

- [知识库构建方案.md](../知识库构建方案.md)
- [知识库文档组织方案.md](../知识库文档组织方案.md)
- [Qdrant 官方文档](https://qdrant.tech/documentation/)

---

**作者**: Indeptrader Team
**最后更新**: 2025-12-28
**版本**: 1.0.0
