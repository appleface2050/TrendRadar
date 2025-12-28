#!/bin/bash
# Qdrant 知识库服务重启脚本

cd "$(dirname "$0")"

echo "🔄 重启 Qdrant 知识库服务..."
echo ""

# 1. 停止服务
echo "🛑 步骤 1/2: 停止服务..."
if ps aux | grep -v grep | grep "knowledge_base_server.py" > /dev/null; then
    # 读取 PID 并停止
    if [ -f kb_server.pid ]; then
        pid=$(cat kb_server.pid)
        if kill $pid 2>/dev/null; then
            echo "   ✅ 服务已停止 (PID: $pid)"
        fi
        rm kb_server.pid
    else
        # 如果没有 PID 文件，通过进程名停止
        ps aux | grep "knowledge_base_server.py" | grep -v grep | awk '{print $2}' | xargs -r kill
        echo "   ✅ 服务已停止"
    fi

    # 等待服务完全停止
    sleep 3
else
    echo "   ℹ️  服务未运行"
fi

echo ""

# 2. 启动服务
echo "🚀 步骤 2/2: 启动服务..."
nohup python knowledge_base_server.py --port 8000 > kb_server.log 2>&1 &

# 保存 PID
echo $! > kb_server.pid

# 等待服务启动，增加重试机制
echo "   ⏳ 等待服务启动..."
max_retries=12
retry_count=0
while [ $retry_count -lt $max_retries ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        break
    fi
    retry_count=$((retry_count + 1))
    sleep 2
    echo "   ⏱️  等待中... ($retry_count/$max_retries)"
done

# 检查服务是否启动成功
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo ""
    echo "✅ 服务重启成功！"
    echo ""
    echo "📍 服务地址: http://localhost:8000"
    echo "📚 API 文档: http://localhost:8000/docs"
    echo "🔧 健康检查: http://localhost:8000/health"
    echo "📊 统计信息: http://localhost:8000/stats"
    echo ""
    echo "💡 使用示例:"
    echo "   python kb_client.py search --query \"收益率曲线\""
    echo "   python kb_client.py stats"
    echo ""
    echo "📝 日志文件: kb_server.log"
    echo "🛑 停止服务: ./stop_kb_server.sh"
    echo "🔄 重启服务: ./restart_kb_server.sh"
else
    echo ""
    echo "❌ 服务启动超时，请检查日志: tail -f kb_server.log"
    echo ""
    echo "调试信息:"
    echo "   进程状态:"
    ps aux | grep knowledge_base_server.py | grep -v grep || echo "   未找到进程"
    echo ""
    echo "   端口监听:"
    netstat -tuln 2>/dev/null | grep 8000 || echo "   端口 8000 未监听"
    exit 1
fi
