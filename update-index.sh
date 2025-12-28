#!/bin/bash
# SCIP 索引更新脚本
# 使用方法: ./update-index.sh

set -e

PROJECT_DIR="/home/shang/git/Indeptrader"
SCIP_FILE="$PROJECT_DIR/.scip/index.scip"

echo "🔄 开始更新 SCIP 索引..."
echo "📁 项目目录: $PROJECT_DIR"

cd "$PROJECT_DIR"

# 检查 scip-typescript 是否安装
if ! command -v scip-typescript &> /dev/null; then
    echo "❌ scip-typescript 未安装"
    echo "📦 安装命令: npm install -g @sourcegraph/scip-cli"
    exit 1
fi

# 创建 .scip 目录
mkdir -p .scip

# 生成索引
echo "⚙️  正在生成索引..."
scip-typescript index --infer-tsconfig --output "$SCIP_FILE" .

# 获取文件大小
SIZE=$(du -h "$SCIP_FILE" | cut -f1)
LINES=$(wc -l < "$SCIP_FILE")

echo "✅ 索引更新完成!"
echo "📊 索引文件: $SCIP_FILE"
echo "📏 文件大小: $SIZE"
echo "📄 总行数: $LINES"

# 可选：提交到 Git
read -p "是否提交到 Git? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git add .scip/index.scip
    echo "📤 已添加到 Git 暂存区"
fi
