#!/bin/bash
# 10年期与2年期国债收益率利差分析系统 - HTTP服务器启动脚本

echo "=================================="
echo "  10Y-2Y 利差分析系统"
echo "=================================="
echo ""

# 检查端口是否已被占用
if lsof -Pi :8088 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  端口 8088 已被使用"
    echo ""
    echo "停止现有服务器？(y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo "正在停止现有服务器..."
        pkill -f "python -m http.server 8088"
        sleep 1
    else
        echo "使用其他端口？"
        read -r port
        port=${port:-8082}
    fi
fi

PORT=${port:-8088}

echo "🚀 启动 HTTP 服务器（端口 $PORT）..."
echo ""
cd "$(dirname "$0")"
python -m http.server $PORT &
SERVER_PID=$!

# 等待服务器启动
sleep 2

# 检查服务器是否成功启动
if curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/ | grep -q "200"; then
    echo "✅ 服务器启动成功！"
    echo ""
    echo "📊 请在浏览器中访问："
    echo "   http://localhost:$PORT/display/10y2y_spread.html"
    echo ""
    echo "💡 提示："
    echo "   - 按 Ctrl+C 停止服务器"
    echo "   - 或运行: pkill -f 'python -m http.server $PORT'"
    echo ""
    echo "按 Ctrl+C 退出..."

    # 保持脚本运行
    wait $SERVER_PID
else
    echo "❌ 服务器启动失败"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi
