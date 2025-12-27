#!/bin/bash
# 自动同步知识库脚本
# 建议：添加到 crontab 中每天运行一次

LOG_FILE="/tmp/indeptrader-logs/knowledge-sync.log"
mkdir -p "$(dirname "$LOG_FILE")"

{
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
  echo "🔄 开始同步知识库..."
  echo ""

  # 1. 重新建立知识库符号链接
  echo "🔗 更新知识库符号链接..."
  /home/shang/git/Indeptrader/knowledge-base/scripts/setup-knowledge-base.sh
  echo ""

  # 2. 智能上传到 BigModel.cn 知识库
  echo "☁️ 上传到 BigModel.cn..."
  python3 /home/shang/git/Indeptrader/knowledge-base/scripts/smart-upload.py \
    --dir "/home/shang/git/Indeptrader/knowledge-base"
  echo ""

  echo "✅ 同步完成！"
  echo ""
} | tee -a "$LOG_FILE"
