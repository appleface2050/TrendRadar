#!/usr/bin/env python3
"""
测试 Qdrant 知识库基本功能

功能:
1. 加载本地 BGE-M3 模型
2. 测试向量化功能
3. 测试文档上传
4. 测试检索功能
"""

import sys
import os
from pathlib import Path

# 添加 scripts 目录到路径
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from qdrant_kb import QdrantKnowledgeBase

# 本地 BGE-M3 模型路径
LOCAL_MODEL_PATH = "~/.cache/huggingface/hub/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181"


def test_embedding():
    """测试嵌入模型"""
    print("\n" + "="*60)
    print("测试 1: 嵌入模型")
    print("="*60)

    # 展开波浪号路径
    model_path = Path(LOCAL_MODEL_PATH).expanduser()

    kb = QdrantKnowledgeBase(
        storage_path="./test_qdrant_data",
        model_path=str(model_path)
    )

    # 测试文本
    test_text = "收益率曲线倒挂是经济衰退的重要先行指标"

    # 生成向量
    print(f"\n📝 测试文本: {test_text}")
    print(f"🔄 生成向量...")

    embedding = kb.model.encode(test_text, normalize_embeddings=True)

    print(f"✅ 向量维度: {embedding.shape}")
    print(f"✅ 前5个值: {embedding[:5]}")

    return kb


def test_upload(kb: QdrantKnowledgeBase):
    """测试文档上传"""
    print("\n" + "="*60)
    print("测试 2: 文档上传")
    print("="*60)

    # 创建测试文档
    test_file = "/tmp/test_kb_document.md"
    test_content = """
# 收益率曲线倒挂

收益率曲线倒挂是指长期国债收益率低于短期国债收益率的现象。

## 定义

正常情况下，长期收益率应该高于短期收益率，以补偿投资者的时间风险和通胀风险。当这种关系反转时，称为收益率曲线倒挂。

## 经济意义

收益率曲线倒挂被视为经济衰退的重要先行指标：

1. **历史记录**: 自1950年代以来，美国每次经济衰退前都出现过收益率曲线倒挂
2. **预测能力**: 倒挂出现后，经济衰退通常在6-24个月内发生
3. **市场信心**: 反映市场对未来经济前景的悲观预期

## 常见指标

- 2年期 vs 10年期国债收益率
- 3个月期 vs 10年期国债收益率

## 注意事项

虽然收益率曲线倒挂是强有力的预测指标，但：
- 不是100%准确（存在假阳性）
- 从倒挂到衰退的时间间隔变化较大
- 需要结合其他经济指标综合判断
"""

    # 写入测试文件
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_content)

    print(f"\n📄 创建测试文档: {test_file}")
    print(f"📊 文档大小: {len(test_content)} 字符")

    # 上传文档
    result = kb.upload_document(test_file, skip_duplicates=False)

    if result['success']:
        print(f"\n✅ 上传成功!")
        print(f"   文本块数: {result['chunks']}")
        print(f"   元数据: {result['metadata']}")
    else:
        print(f"\n❌ 上传失败: {result.get('error')}")
        return None

    return test_file


def test_search(kb: QdrantKnowledgeBase):
    """测试检索功能"""
    print("\n" + "="*60)
    print("测试 3: 检索功能")
    print("="*60)

    # 测试查询
    queries = [
        "什么是收益率曲线倒挂?",
        "收益率曲线倒挂能预测经济衰退吗?",
        "倒挂后多久会发生衰退?",
    ]

    for query in queries:
        print(f"\n🔍 查询: {query}")
        results = kb.search(query, top_k=2)

        print(f"📊 找到 {len(results)} 个结果:")
        for i, result in enumerate(results, 1):
            print(f"\n  [{i}] 相关度: {result['score']:.4f}")
            print(f"      内容: {result['text'][:150]}...")

        print()


def test_list(kb: QdrantKnowledgeBase):
    """测试列表功能"""
    print("\n" + "="*60)
    print("测试 4: 列表功能")
    print("="*60)

    documents = kb.list_documents()

    print(f"\n📚 知识库中的文档（共 {len(documents)} 个）:\n")
    for doc in documents:
        print(f"  📄 {doc['file_name']}")
        print(f"     类型: {doc['file_type']} | 类别: {doc['category']}")
        print(f"     块数: {doc['chunks']} | 路径: {doc['file_path']}")
        print()


def test_metadata_filter(kb: QdrantKnowledgeBase):
    """测试元数据过滤"""
    print("\n" + "="*60)
    print("测试 5: 元数据过滤")
    print("="*60)

    # 测试按类别过滤
    print("\n🔍 查询（仅限 markdown 文件）:")
    results = kb.search(
        "收益率曲线",
        top_k=3,
        filters={"file_type": "markdown"}
    )

    for i, result in enumerate(results, 1):
        print(f"\n  [{i}] 相关度: {result['score']:.4f}")
        print(f"      类型: {result['metadata']['file_type']}")
        print(f"      内容: {result['text'][:100]}...")


def test_duplicate_detection(kb: QdrantKnowledgeBase):
    """测试重复检测"""
    print("\n" + "="*60)
    print("测试 6: 重复检测")
    print("="*60)

    test_file = "/tmp/test_kb_document.md"

    print(f"\n📄 尝试重复上传同一文件...")
    result1 = kb.upload_document(test_file, skip_duplicates=True)
    print(f"   第一次: {'✅ 成功' if result1['success'] and not result1.get('skipped') else '⏭️  跳过' if result1.get('skipped') else '❌ 失败'}")

    result2 = kb.upload_document(test_file, skip_duplicates=True)
    print(f"   第二次: {'✅ 成功' if result2['success'] and not result2.get('skipped') else '⏭️  跳过' if result2.get('skipped') else '❌ 失败'}")

    if result2.get('skipped'):
        print(f"   原因: {result2.get('reason')}")


def test_delete(kb: QdrantKnowledgeBase):
    """测试删除功能"""
    print("\n" + "="*60)
    print("测试 7: 删除功能")
    print("="*60)

    test_file = "/tmp/test_kb_document.md"

    print(f"\n🗑️  删除测试文档...")
    result = kb.delete_document(test_file)

    if result['success']:
        print(f"✅ 删除成功: {result['deleted_points']} 个数据块")
    else:
        print(f"❌ 删除失败: {result.get('error')}")

    # 验证删除
    print(f"\n🔍 验证删除结果...")
    documents = kb.list_documents()
    print(f"✅ 剩余文档数: {len(documents)}")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Qdrant 知识库功能测试")
    print("="*60)
    print("\n⚠️  注意:")
    print("  - 使用本地 BGE-M3 模型（无需下载）")
    print("  - 测试数据将保存在 ./test_qdrant_data/")
    print("  - 测试完成后可删除测试数据\n")

    # 直接开始测试（无交互模式）
    import time
    time.sleep(1)

    try:
        # 测试 1: 嵌入模型
        kb = test_embedding()

        # 测试 2: 文档上传
        test_file = test_upload(kb)
        if not test_file:
            print("\n❌ 上传测试失败，终止后续测试")
            return

        # 测试 3: 检索功能
        test_search(kb)

        # 测试 4: 列表功能
        test_list(kb)

        # 测试 5: 元数据过滤
        test_metadata_filter(kb)

        # 测试 6: 重复检测
        test_duplicate_detection(kb)

        # 测试 7: 删除功能
        test_delete(kb)

        print("\n" + "="*60)
        print("✅ 所有测试完成!")
        print("="*60)
        print("\n💡 提示:")
        print("  - 查看测试数据: ./test_qdrant_data/")
        print("  - 删除测试数据: rm -rf ./test_qdrant_data/")
        print()

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
