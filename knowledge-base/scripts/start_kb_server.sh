#!/bin/bash
# Qdrant 知识库服务快速启动脚本

cd "$(dirname "$0")"

# 检查服务是否已经在运行
if ps aux | grep -v grep | grep "knowledge_base_server.py" > /dev/null; then
    echo "⚠️  服务已在运行"
    echo "如需重启，请先运行: ./stop_kb_server.sh"
    exit 1
fi

# 启动服务
echo "🚀 启动 Qdrant 知识库服务..."
nohup python knowledge_base_server.py --port 8000 > kb_server.log 2>&1 &

# 保存 PID
echo $! > kb_server.pid

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务是否启动成功
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 服务启动成功！"
    echo ""
    echo "📍 服务地址: http://localhost:8000"
    echo "📚 API 文档: http://localhost:8000/docs"
    echo "🔧 健康检查: http://localhost:8000/health"
    echo ""
    echo "💡 使用示例:"
    echo "   python kb_client.py search --query \"收益率曲线\""
    echo "   python kb_client.py stats"
    echo ""
    echo "📝 日志文件: kb_server.log"
    echo "🛑 停止服务: ./stop_kb_server.sh"
else
    echo "❌ 服务启动失败，请检查日志: tail -f kb_server.log"
    exit 1
fi
