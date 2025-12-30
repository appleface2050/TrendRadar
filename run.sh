#!/bin/bash

# TrendRadar 启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 设置 Python 路径
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# 运行 TrendRadar
python -m trendradar "$@"
