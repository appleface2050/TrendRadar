# Qdrant 知识库 FastAPI 服务使用指南

## 📖 概述

FastAPI 服务版本将模型加载一次后常驻内存，将搜索时间从 **7 秒**降至 **0.5 秒**以下。

## 🚀 快速开始

### 1. 启动服务

```bash
# 前台运行（开发模式）
cd /home/shang/git/Indeptrader/knowledge-base/scripts
python knowledge_base_server.py

# 后台运行（生产模式）
nohup python knowledge_base_server.py > kb_server.log 2>&1 &

# 查看服务状态
ps aux | grep knowledge_base_server
```

启动后会看到：
```
╔══════════════════════════════════════════════════════════╗
║         Qdrant 知识库 FastAPI 服务                        ║
╚══════════════════════════════════════════════════════════╝

📍 服务地址: http://0.0.0.0:8000
📚 API 文档: http://localhost:8000/docs
🔧 健康检查: http://localhost:8000/health
```

### 2. 使用客户端搜索

```bash
# 基本搜索
python kb_client.py search --query "收益率曲线"

# 返回更多结果
python kb_client.py search --query "收益率曲线" --top-k 10

# 按类别过滤
python kb_client.py search --query "交易策略" --filters '{"category": "project"}'

# 健康检查
python kb_client.py health

# 查看统计信息
python kb_client.py stats
```

### 3. 直接调用 API（使用 curl）

```bash
# 健康检查
curl http://localhost:8000/health

# 搜索
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "收益率曲线", "top_k": 5}'

# 获取统计信息
curl http://localhost:8000/stats
```

## 📊 性能对比

| 方式 | 初始化耗时 | 搜索耗时 | 总耗时 |
|------|-----------|---------|--------|
| **命令行脚本** | 6621ms | 465ms | **7086ms** |
| **FastAPI 服务** | 6621ms (仅启动时一次) | 465ms | **465ms** |

**提速 15 倍！** ✨

## 🔧 API 端点

### POST /search
搜索知识库

**请求体:**
```json
{
  "query": "收益率曲线",
  "top_k": 5,
  "score_threshold": 0.5,
  "filters": {
    "category": "project"
  }
}
```

**响应:**
```json
[
  {
    "score": 0.5838,
    "text": "...",
    "metadata": {
      "file_name": "文档.md",
      "file_type": "markdown",
      "category": "project"
    }
  }
]
```

### GET /health
健康检查

**响应:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "collection_exists": true,
  "vectors_count": 1234
}
```

### GET /stats
统计信息

**响应:**
```json
{
  "model_name": "BAAI/bge-small-zh-v1.5",
  "device": "cuda",
  "vectors_count": 1234,
  "segments_count": 4
}
```

## 🛠️ 高级用法

### 自定义端口和地址

```bash
# 使用自定义端口启动服务
python knowledge_base_server.py --host 127.0.0.1 --port 9000

# 连接到自定义端口
python kb_client.py --url http://localhost:9000 search --query "收益率曲线"
```

### 开发模式（自动重载）

```bash
# 代码修改后自动重启服务
python knowledge_base_server.py --reload
```

### 在浏览器中测试

访问 http://localhost:8000/docs 使用 Swagger UI 交互式测试 API

## 📝 Python 代码集成

```python
import requests

# 搜索
response = requests.post(
    "http://localhost:8000/search",
    json={
        "query": "收益率曲线",
        "top_k": 5
    }
)

results = response.json()
for result in results:
    print(f"Score: {result['score']}")
    print(f"Text: {result['text'][:100]}...")
```

## 🛑 停止服务

```bash
# 如果在后台运行
ps aux | grep knowledge_base_server
kill <PID>

# 或者使用 pkill
pkill -f knowledge_base_server
```

## ⚠️ 注意事项

1. **内存占用**: 服务会常驻内存，占用约 1-2GB（主要是模型）
2. **CUDA 设备**: 默认使用 CUDA，如果需要使用 CPU，修改 `device="cpu"`
3. **并发处理**: FastAPI 支持异步处理，可以同时处理多个搜索请求
4. **日志查看**: 如果使用 nohup 后台运行，日志保存在 `kb_server.log`

## 🔍 故障排查

### 服务无法启动
```bash
# 检查端口是否被占用
netstat -tulpn | grep 8000

# 查看日志
tail -f kb_server.log
```

### 搜索无结果
```bash
# 检查知识库是否有数据
curl http://localhost:8000/stats

# 确认集合存在且向量数量 > 0
```

### 连接拒绝
```bash
# 确认服务正在运行
python kb_client.py health

# 检查防火墙设置
```
