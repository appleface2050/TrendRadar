#!/bin/bash
# Qdrant 知识库服务停止脚本

cd "$(dirname "$0")"

# 检查服务是否在运行
if ! ps aux | grep -v grep | grep "knowledge_base_server.py" > /dev/null; then
    echo "⚠️  服务未运行"
    exit 0
fi

echo "🛑 停止 Qdrant 知识库服务..."

# 读取 PID 并停止
if [ -f kb_server.pid ]; then
    pid=$(cat kb_server.pid)
    if kill $pid 2>/dev/null; then
        echo "✅ 服务已停止 (PID: $pid)"
    fi
    rm kb_server.pid
else
    # 如果没有 PID 文件，通过进程名停止
    ps aux | grep "knowledge_base_server.py" | grep -v grep | awk '{print $2}' | xargs -r kill
    echo "✅ 服务已停止"
fi

sleep 1

# 确认服务已停止
if ps aux | grep -v grep | grep "knowledge_base_server.py" > /dev/null; then
    echo "⚠️  警告: 服务可能仍在运行"
    ps aux | grep "knowledge_base_server.py" | grep -v grep
else
    echo "✅ 确认: 服务已完全停止"
fi
