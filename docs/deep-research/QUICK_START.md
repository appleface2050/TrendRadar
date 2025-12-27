# Deep Research 快速参考

## 🚀 常用命令

### 启动服务
```bash
cd ~/git/deep-research && pnpm dev
```

### 后台运行
```bash
cd ~/git/deep-research && nohup pnpm dev > /tmp/deep-research.log 2>&1 &
```

### 查看日志
```bash
tail -f /tmp/deep-research.log
```

### 检查 MCP 状态
```bash
claude mcp list
```

### 重启服务
```bash
pkill -f "next dev"
cd ~/git/deep-research && pnpm dev
```

## 🔑 关键配置

**文件位置**: `~/git/deep-research/.env.local`

```bash
DEEPSEEK_API_KEY=***REMOVED***
FIRECRAWL_API_KEY=***REMOVED***

MCP_AI_PROVIDER=deepseek
MCP_SEARCH_PROVIDER=firecrawl
MCP_THINKING_MODEL=deepseek-reasoner
MCP_TASK_MODEL=deepseek-chat
```

## 📍 服务地址

- **Web UI**: http://localhost:3000
- **MCP**: http://127.0.0.1:3000/api/mcp

## 🔧 故障排查

**端口被占用?**
```bash
lsof -ti:3000 | xargs kill -9
```

**MCP 断开?**
```bash
claude mcp remove deep-research
claude mcp add --transport http deep-research http://127.0.0.1:3000/api/mcp
```

## 📖 完整文档

查看 [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) 了解详细信息
