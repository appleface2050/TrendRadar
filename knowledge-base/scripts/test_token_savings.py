#!/usr/bin/env python3
"""
Qdrant 知识库 Token 节省效果测试脚本

测试场景：
1. 模拟用户查询关于"知识库系统架构"的问题
2. 对比两种方案：
   - 方案A：直接将所有文档发给 LLM（无知识库）
   - 方案B：使用知识库搜索，只发送相关片段
3. 计算 token 节省比例
"""

import os
import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入 qdrant_kb 会自动从 settings.py 加载 HF_ENDPOINT
from qdrant_kb import QdrantKnowledgeBase


def estimate_tokens(text: str) -> int:
    """
    估算文本的 token 数量
    使用简化规则：中文约 1.5 字符/token，英文约 4 字符/token
    """
    if not text:
        return 0

    # 统计中文字符
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    # 统计非中文字符（主要是英文和标点）
    non_chinese = len(text) - chinese_chars

    # 估算 token 数
    tokens = chinese_chars / 1.5 + non_chinese / 4
    return int(tokens)


def test_token_savings():
    """测试 token 节省效果"""

    print("=" * 80)
    print("Qdrant 知识库 Token 节省效果测试")
    print("=" * 80)
    print()

    # 初始化知识库
    print("📦 初始化知识库...")
    kb = QdrantKnowledgeBase(
        storage_path="/home/shang/qdrant_data",
        model_name="BAAI/bge-small-zh-v1.5",
        device="cuda"
    )
    print("✅ 知识库初始化完成\n")

    # 获取知识库统计信息
    print("=" * 80)
    print("📊 知识库统计信息")
    print("=" * 80)
    collection_info = kb.get_collection_info()
    documents = kb.list_documents(limit=1000)
    print(f"文档总数: {len(documents)}")
    print(f"文本块总数: {collection_info['vectors_count']}")
    print()

    # 读取所有文档的原始内容
    print("=" * 80)
    print("📄 方案 A：无知识库（直接读取所有文档）")
    print("=" * 80)

    knowledge_base_path = Path("/home/shang/git/Indeptrader/knowledge-base")
    all_documents = []

    # 读取所有 markdown 文件
    for md_file in knowledge_base_path.rglob("*.md"):
        # 跳过一些临时文件
        if any(x in md_file.name for x in ['__', 'node_modules']):
            continue

        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                all_documents.append({
                    'file': str(md_file.relative_to(knowledge_base_path)),
                    'content': content
                })
        except Exception as e:
            print(f"⚠️  无法读取 {md_file}: {e}")

    # 计算所有文档的总大小
    total_content = "\n\n".join([f"文件: {doc['file']}\n\n{doc['content']}" for doc in all_documents])
    total_size = len(total_content)
    total_tokens = estimate_tokens(total_content)

    print(f"文档数量: {len(all_documents)}")
    print(f"总字符数: {total_size:,}")
    print(f"估算 Token 数: {total_tokens:,}")
    print(f"平均每文档: {total_size // len(all_documents):,} 字符")
    print()

    # 测试查询
    query = "知识库系统的架构设计和实现方案"
    print("=" * 80)
    print(f"🔍 用户查询: \"{query}\"")
    print("=" * 80)
    print()

    # 使用知识库搜索
    print("=" * 80)
    print("📊 方案 B：使用 Qdrant 知识库")
    print("=" * 80)

    results = kb.search(query, top_k=5)

    # 组织搜索结果
    search_results_text = f"查询: {query}\n\n相关文档片段:\n\n"
    for i, result in enumerate(results, 1):
        metadata = result['metadata']
        search_results_text += f"[{i}] {metadata['file_name']} (相关度: {result['score']:.4f})\n"
        search_results_text += f"{result['text']}\n\n"

    search_size = len(search_results_text)
    search_tokens = estimate_tokens(search_results_text)

    print(f"返回结果数: {len(results)}")
    print(f"总字符数: {search_size:,}")
    print(f"估算 Token 数: {search_tokens:,}")
    print()

    # 计算节省效果
    print("=" * 80)
    print("💡 Token 节省效果分析")
    print("=" * 80)

    saved_tokens = total_tokens - search_tokens
    savings_ratio = (saved_tokens / total_tokens) * 100 if total_tokens > 0 else 0

    print(f"方案 A（无知识库）Token 数: {total_tokens:,}")
    print(f"方案 B（使用知识库）Token 数: {search_tokens:,}")
    print(f"节省 Token 数: {saved_tokens:,}")
    print(f"节省比例: {savings_ratio:.2f}%")
    print()

    # 计算成本节省（以 Claude Sonnet 4.5 为例）
    # 输入价格: $3/1M tokens
    cost_per_million_tokens = 3.0
    cost_without_kb = (total_tokens / 1_000_000) * cost_per_million_tokens
    cost_with_kb = (search_tokens / 1_000_000) * cost_per_million_tokens
    cost_savings = cost_without_kb - cost_with_kb

    print("=" * 80)
    print("💰 成本节省分析（基于 Claude Sonnet 4.5）")
    print("=" * 80)
    print(f"方案 A 单次查询成本: ${cost_without_kb:.6f}")
    print(f"方案 B 单次查询成本: ${cost_with_kb:.6f}")
    print(f"单次查询节省: ${cost_savings:.6f}")
    print()

    # 年度节省估算（假设每天 100 次查询）
    daily_queries = 100
    annual_savings = cost_savings * daily_queries * 365
    print(f"年度节省估算（每天 {daily_queries} 次查询）: ${annual_savings:.2f}")
    print()

    # 展示搜索结果详情
    print("=" * 80)
    print("📋 搜索结果详情")
    print("=" * 80)
    for i, result in enumerate(results, 1):
        metadata = result['metadata']
        print(f"\n[{i}] {metadata['file_name']}")
        print(f"    相关度: {result['score']:.4f}")
        print(f"    分类: {metadata.get('category', 'N/A')}")
        print(f"    内容预览: {result['text'][:150]}...")
        print()

    # 保存测试报告
    report = {
        "test_date": "2025-12-28",
        "query": query,
        "knowledge_base": {
            "total_documents": len(documents),
            "total_chunks": collection_info['vectors_count']
        },
        "scenario_a": {
            "description": "无知识库（读取所有文档）",
            "document_count": len(all_documents),
            "total_chars": total_size,
            "estimated_tokens": total_tokens
        },
        "scenario_b": {
            "description": "使用 Qdrant 知识库",
            "results_count": len(results),
            "total_chars": search_size,
            "estimated_tokens": search_tokens
        },
        "savings": {
            "tokens_saved": saved_tokens,
            "savings_ratio": f"{savings_ratio:.2f}%",
            "cost_per_query_usd": float(cost_savings),
            "annual_savings_usd": float(annual_savings)
        }
    }

    report_path = Path("/tmp/qdrant_token_savings_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("=" * 80)
    print(f"📄 测试报告已保存至: {report_path}")
    print("=" * 80)
    print()

    # 结论
    print("=" * 80)
    print("🎯 结论")
    print("=" * 80)
    print(f"""
通过使用 Qdrant 本地知识库系统：

1. **Token 效率提升**: 从 {total_tokens:,} tokens 降低到 {search_tokens:,} tokens
2. **节省比例**: {savings_ratio:.2f}%
3. **成本节省**: 每次查询节省 ${cost_savings:.6f}
4. **年度价值**: 假设每天 {daily_queries} 次查询，年度节省约 ${annual_savings:.2f}
5. **响应质量**: 返回最相关的 {len(results)} 个文档片段，而非全部 {len(all_documents)} 个文档

**核心价值**：
- ✅ 大幅减少 LLM 上下文窗口占用
- ✅ 降低 API 调用成本
- ✅ 提升查询响应速度
- ✅ 返回更精准的相关内容
""")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_token_savings()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
