#!/bin/bash

# TrendRadar 启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 添加 miniconda3 到 PATH（cron 环境需要）
export PATH="/home/shang/miniconda3/bin:$PATH"

# 设置 Python 路径
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# 检测是否在 cron 环境中运行，如果是则禁用浏览器打开
if [ -n "$CRON" ] || pgrep -f "cron" > /dev/null 2>&1; then
    export DOCKER_CONTAINER=true
fi

# 运行 TrendRadar
python -m trendradar "$@"
