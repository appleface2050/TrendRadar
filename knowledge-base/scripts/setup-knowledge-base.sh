#!/bin/bash
# 设置统一知识库目录
# 使用符号链接将分散的文档集中管理

echo "🔧 设置统一知识库目录..."

# 创建目录结构
mkdir -p /home/shang/git/Indeptrader/knowledge-base/{business,project,research}

# 1. 链接项目文档
if [ -d "/home/shang/git/Indeptrader/docs" ]; then
    echo "📁 链接项目文档..."
    find /home/shang/git/Indeptrader/docs -type f \( -name "*.md" -o -name "*.pdf" -o -name "*.txt" \) \
         -exec ln -sf {} /home/shang/git/Indeptrader/knowledge-base/project/ \;
fi

# 2. 链接研究报告
if [ -d "/home/shang/git/Indeptrader/deep_research_report" ]; then
    echo "📚 链接研究报告..."
    ln -sf /home/shang/git/Indeptrader/deep_research_report/*.md \
          /home/shang/git/Indeptrader/knowledge-base/research/
fi

# 显示目录结构
echo ""
echo "✅ 知识库目录设置完成！"
echo ""
echo "📊 目录结构："
tree -L 2 /home/shang/git/Indeptrader/knowledge-base 2>/dev/null || \
    ls -R /home/shang/git/Indeptrader/knowledge-base
echo ""
echo "💡 现在可以使用以下命令上传所有文档："
echo "python3 /home/shang/git/Indeptrader/scripts/smart-upload.py \\"
echo "  --dir \"/home/shang/git/Indeptrader/knowledge-base\""
