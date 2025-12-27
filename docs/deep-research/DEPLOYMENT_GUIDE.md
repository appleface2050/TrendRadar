# Deep Research MCP 部署指南

## 📖 项目简介

**Deep Research** 是一个使用任何大语言模型进行深度研究的工具，支持 SSE API 和 MCP 服务器。

- **GitHub**: https://github.com/u14app/deep-research
- **在线演示**: https://research.u14.app
- **部署日期**: 2025-12-27

## 🎯 当前配置

### 技术栈
- **AI Provider**: DeepSeek
- **Thinking Model**: deepseek-reasoner
- **Task Model**: deepseek-chat
- **Search Provider**: Firecrawl
- **Transport**: HTTP (StreamableHTTP)

### 服务地址
- **Web UI**: http://localhost:3000
- **MCP API**: http://127.0.0.1:3000/api/mcp

## 📋 部署步骤

### 1. 克隆项目

```bash
git clone https://github.com/u14app/deep-research.git ~/git/deep-research
cd ~/git/deep-research
```

### 2. 安装 pnpm

```bash
# 使用 sudo 安装 pnpm（需要 root 权限）
echo "root" | sudo -S npm install -g pnpm

# 验证安装
pnpm --version
```

### 3. 安装项目依赖

```bash
cd ~/git/deep-research
pnpm install
```

### 4. 配置环境变量

创建 `.env.local` 文件：

```bash
cat > .env.local << 'EOF'
# DeepSeek API Key
DEEPSEEK_API_KEY=***REMOVED***

# Firecrawl API Key
FIRECRAWL_API_KEY=***REMOVED***

# MCP Server Configuration
MCP_AI_PROVIDER=deepseek
MCP_SEARCH_PROVIDER=firecrawl
MCP_THINKING_MODEL=deepseek-reasoner
MCP_TASK_MODEL=deepseek-chat
EOF
```

### 5. 启动服务

```bash
# 开发模式（前台运行）
pnpm dev

# 或者后台运行
pnpm dev > /tmp/deep-research.log 2>&1 &
```

### 6. 配置 MCP 客户端

```bash
# 添加到 Claude Code
claude mcp add --transport http deep-research http://127.0.0.1:3000/api/mcp

# 验证连接
claude mcp list
```

## 🔧 配置说明

### MCP 环境变量

| 变量名 | 说明 | 可选值 |
|--------|------|--------|
| `MCP_AI_PROVIDER` | AI 提供商 | google, openai, anthropic, deepseek, xai, mistral, azure, openrouter, openaicompatible, pollinations, ollama |
| `MCP_SEARCH_PROVIDER` | 搜索提供商 | model, tavily, firecrawl, exa, bocha, searxng |
| `MCP_THINKING_MODEL` | 思考模型 | deepseek-reasoner, gemini-2.0-flash-thinking-exp, etc. |
| `MCP_TASK_MODEL` | 任务模型 | deepseek-chat, gemini-2.0-flash-exp, etc. |

### DeepSeek 模型选择

- **思考模型** (用于复杂推理):
  - `deepseek-reasoner` - DeepSeek R1 推理模型

- **任务模型** (用于快速输出):
  - `deepseek-chat` - DeepSeek V3 聊天模型
  - `deepseek-coder` - DeepSeek 代码模型

### 其他支持的 AI 提供商

```bash
# Google Gemini (推荐免费使用)
MCP_AI_PROVIDER=google
MCP_THINKING_MODEL=gemini-2.0-flash-thinking-exp
MCP_TASK_MODEL=gemini-2.0-flash-exp
GOOGLE_GENERATIVE_AI_API_KEY=your-api-key

# Anthropic Claude
MCP_AI_PROVIDER=anthropic
MCP_THINKING_MODEL=claude-sonnet-4-20250514
MCP_TASK_MODEL=claude-haiku-4-20250514
ANTHROPIC_API_KEY=your-api-key

# OpenAI
MCP_AI_PROVIDER=openai
MCP_THINKING_MODEL=o1-preview
MCP_TASK_MODEL=gpt-4o
OPENAI_API_KEY=your-api-key
```

### 其他支持的搜索引擎

```bash
# Tavily (需要 API Key)
MCP_SEARCH_PROVIDER=tavily
TAVILY_API_KEY=your-api-key

# Exa (需要 API Key)
MCP_SEARCH_PROVIDER=exa
EXA_API_KEY=your-api-key

# SearXNG (需要自建实例)
MCP_SEARCH_PROVIDER=searxng
SEARXNG_API_BASE_URL=http://localhost:8080
```

## 🎮 使用方法

### Web UI 使用

1. 访问 http://localhost:3000
2. 输入研究主题
3. 选择模型和搜索引擎
4. 开始深度研究
5. 查看实时生成的报告

### MCP 集成使用

在 Claude Code 中，deep-research 工具现在可用：

```typescript
// 示例：在代码中使用 MCP 工具
// deep-research 会执行深度研究并返回报告
```

### API 端点

#### POST /api/mcp
MCP 服务器端点（StreamableHTTP）

#### POST /api/sse
Server-Sent Events API

```bash
curl -X POST http://localhost:3000/api/sse \
  -H "Content-Type: application/json" \
  -d '{
    "query": "AI trends for 2025",
    "provider": "deepseek",
    "thinkingModel": "deepseek-reasoner",
    "taskModel": "deepseek-chat",
    "searchProvider": "firecrawl",
    "language": "zh-CN",
    "maxResult": 5
  }'
```

## 🔍 验证部署

### 检查服务状态

```bash
# 检查服务是否运行
curl http://localhost:3000/api/mcp

# 查看 Claude MCP 列表
claude mcp list

# 查看日志
tail -f /tmp/deep-research.log
```

### 测试 MCP 连接

```bash
# 应该看到 deep-research 显示为 Connected
claude mcp list
```

## 🛠️ 故障排查

### 服务无法启动

```bash
# 检查端口占用
netstat -tlnp | grep 3000

# 查看错误日志
tail -50 /tmp/deep-research.log
```

### MCP 连接失败

```bash
# 1. 确认服务正在运行
curl http://localhost:3000

# 2. 检查环境变量是否正确配置
cat ~/git/deep-research/.env.local

# 3. 重启服务
pkill -f "next dev"
cd ~/git/deep-research && pnpm dev
```

### API 调用失败

```bash
# 验证 API 密钥
curl https://api.deepseek.com/v1/models \
  -H "Authorization: Bearer ***REMOVED***"

curl https://api.firecrawl.dev/v1/status \
  -H "Authorization: Bearer ***REMOVED***"
```

## 🔄 进阶配置

### 使用 PM2 管理进程

```bash
# 安装 PM2
npm install -g pm2

# 启动服务
cd ~/git/deep-research
pm2 start pnpm --name "deep-research" -- run dev

# 设置开机自启
pm2 startup
pm2 save

# 查看状态
pm2 status

# 查看日志
pm2 logs deep-research
```

### Docker 部署

```bash
# 拉取镜像
docker pull xiangfa/deep-research:latest

# 运行容器
docker run -d --name deep-research \
  -p 3333:3000 \
  -e DEEPSEEK_API_KEY=***REMOVED*** \
  -e FIRECRAWL_API_KEY=***REMOVED*** \
  -e MCP_AI_PROVIDER=deepseek \
  -e MCP_SEARCH_PROVIDER=firecrawl \
  -e MCP_THINKING_MODEL=deepseek-reasoner \
  -e MCP_TASK_MODEL=deepseek-chat \
  xiangfa/deep-research

# 查看日志
docker logs -f deep-research
```

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name research.yourdomain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## 📚 相关资源

- [Deep Research GitHub](https://github.com/u14app/deep-research)
- [DeepSeek API 文档](https://platform.deepseek.com/api-docs/)
- [Firecrawl 文档](https://docs.firecrawl.dev/)
- [Claude Code MCP 文档](https://code.anthropic.com/docs)

## 📝 更新日志

- **2025-12-27**: 初始部署，使用 DeepSeek + Firecrawl 配置

---

**生成日期**: 2025-12-27
**部署环境**: WSL2 Ubuntu
**Node 版本**: 18.18.0+
