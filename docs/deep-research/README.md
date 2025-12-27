# Deep Research MCP 部署文档

**部署日期**: 2025-12-27
**项目地址**: ~/git/deep-research
**文档目录**: /home/shang/git/Indeptrader/docs/deep-research

---

## 📚 文档导航

### 1. [DEPLOYMENT_CONVERSATION.md](./DEPLOYMENT_CONVERSATION.md) ⭐ 推荐
**完整的部署对话记录**

包含从开始到结束的完整对话过程，包括：
- 每一步的决策和理由
- 遇到的问题和解决方案
- 关键配置和命令
- 经验总结和后续建议

**适用场景**: 回忆部署过程、理解决策逻辑、学习部署经验

---

### 2. [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) 📖
**完整部署技术指南**

包含详细的技术文档和部署步骤：
- 项目介绍和当前配置
- 详细部署步骤
- 所有配置说明和可选值
- 使用方法和 API 示例
- 故障排查方案
- 进阶配置（PM2、Docker、Nginx）

**适用场景**: 重新部署、修改配置、深入理解、故障排查

---

### 3. [QUICK_START.md](./QUICK_START.md) ⚡
**快速参考卡片**

包含最常用的命令和配置：
- 常用命令速查
- 关键配置位置
- 服务地址
- 快速故障排查

**适用场景**: 日常使用、快速查找命令、应急处理

---

## 🎯 快速定位

### 我想...

**🔍 回顾部署过程**
→ 阅读 [DEPLOYMENT_CONVERSATION.md](./DEPLOYMENT_CONVERSATION.md)

**🚀 重新部署或修改配置**
→ 参考 [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

**⚡ 查找常用命令**
→ 查看 [QUICK_START.md](./QUICK_START.md)

**🔧 解决服务问题**
→ [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) 中的"故障排查"章节

**📱 使用 Web UI**
→ 访问 http://localhost:3000

**🤖 使用 MCP 集成**
→ Claude Code 中已自动可用

---

## 📋 当前配置

### 服务地址
- **Web UI**: http://localhost:3000
- **MCP API**: http://127.0.0.1:3000/api/mcp

### 配置文件
- **环境变量**: ~/git/deep-research/.env.local
- **MCP 配置**: ~/.claude.json

### 技术栈
- **AI Provider**: DeepSeek
- **Thinking Model**: deepseek-reasoner
- **Task Model**: deepseek-chat
- **Search Provider**: Firecrawl

---

## 🔗 相关链接

- [Deep Research GitHub](https://github.com/u14app/deep-research)
- [DeepSeek API 文档](https://platform.deepseek.com/api-docs/)
- [Firecrawl 文档](https://docs.firecrawl.dev/)
- [Claude Code 文档](https://code.anthropic.com/docs)

---

## 📝 文档更新日志

- **2025-12-27**: 初始创建，包含完整部署记录、技术指南和快速参考

---

**文档位置**: `/home/shang/git/Indeptrader/docs/deep-research/`
**项目位置**: `~/git/deep-research`
