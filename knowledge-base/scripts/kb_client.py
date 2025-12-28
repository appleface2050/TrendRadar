#!/usr/bin/env python3
"""
Qdrant 知识库 API 客户端

用于调用 FastAPI 知识库服务的命令行工具
"""

import argparse
import json
import sys
from typing import Dict, Any
import requests


class KnowledgeBaseClient:
    """知识库 API 客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """初始化客户端

        Args:
            base_url: API 服务地址
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = 30

    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        response = requests.get(f"{self.base_url}/health", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """搜索知识库

        Args:
            query: 查询文本
            top_k: 返回前 K 个结果
            score_threshold: 相似度阈值
            filters: 元数据过滤条件

        Returns:
            搜索结果
        """
        payload = {
            "query": query,
            "top_k": top_k,
            "score_threshold": score_threshold
        }

        if filters:
            payload["filters"] = filters

        response = requests.post(
            f"{self.base_url}/search",
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        response = requests.get(f"{self.base_url}/stats", timeout=self.timeout)
        response.raise_for_status()
        return response.json()


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='Qdrant 知识库 API 客户端',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 搜索知识库
  python kb_client.py search --query "收益率曲线"

  # 返回前 10 个结果
  python kb_client.py search --query "收益率曲线" --top-k 10

  # 按类别过滤
  python kb_client.py search --query "交易策略" --filters '{"category": "project"}'

  # 健康检查
  python kb_client.py health

  # 查看统计信息
  python kb_client.py stats
        """
    )

    parser.add_argument(
        '--url',
        default='http://localhost:8000',
        help='API 服务地址（默认: http://localhost:8000）'
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # search 命令
    search_parser = subparsers.add_parser('search', help='搜索知识库')
    search_parser.add_argument('--query', required=True, help='查询文本')
    search_parser.add_argument('--top-k', type=int, default=5, help='返回前 K 个结果')
    search_parser.add_argument('--threshold', type=float, default=0.5, help='相似度阈值')
    search_parser.add_argument('--filters', help='过滤条件（JSON 格式）')

    # health 命令
    health_parser = subparsers.add_parser('health', help='健康检查')

    # stats 命令
    stats_parser = subparsers.add_parser('stats', help='统计信息')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 初始化客户端
    client = KnowledgeBaseClient(base_url=args.url)

    # 执行命令
    if args.command == 'search':
        try:
            # 解析过滤条件
            filters = None
            if args.filters:
                filters = json.loads(args.filters)

            # 执行搜索
            import time
            t0 = time.time()
            results = client.search(
                query=args.query,
                top_k=args.top_k,
                score_threshold=args.threshold,
                filters=filters
            )
            t1 = time.time()

            # 显示结果
            print(f"\n🔍 搜索结果: '{args.query}' (耗时 {(t1-t0)*1000:.2f}ms)\n")
            print("=" * 80)

            for i, result in enumerate(results, 1):
                print(f"\n[{i}] 相关度: {result['score']:.4f}")
                print(f"    文件: {result['metadata'].get('file_name', 'Unknown')}")

                # 显示文件类型和类别
                file_type = result['metadata'].get('file_type', '')
                category = result['metadata'].get('category', '')
                if file_type or category:
                    print(f"    类型: {file_type} | 类别: {category}")

                # 显示内容预览
                text = result['text']
                preview = text[:300] + "..." if len(text) > 300 else text
                print(f"    内容: {preview}")

            print("\n" + "=" * 80)
            print(f"共找到 {len(results)} 个结果\n")

        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到服务 {args.url}")
            print(f"   请确保服务已启动: python knowledge_base_server.py")
            sys.exit(1)
        except requests.exceptions.HTTPStatusError as e:
            print(f"❌ 请求失败: {e.response.status_code}")
            print(f"   {e.response.text}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 错误: {e}")
            sys.exit(1)

    elif args.command == 'health':
        try:
            health = client.health_check()
            print("\n🏥 服务健康状态\n")
            print("=" * 40)
            print(f"状态: {health['status']}")
            print(f"模型已加载: {health['model_loaded']}")
            print(f"集合存在: {health['collection_exists']}")
            print(f"向量数量: {health['vectors_count']}")
            print("=" * 40 + "\n")
        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到服务 {args.url}")
            print(f"   请确保服务已启动: python knowledge_base_server.py")
            sys.exit(1)

    elif args.command == 'stats':
        try:
            stats = client.get_stats()
            print("\n📊 知识库统计信息\n")
            print("=" * 40)
            print(f"嵌入模型: {stats['model_name']}")
            print(f"计算设备: {stats['device']}")
            print(f"存储路径: {stats['storage_path']}")
            print(f"集合名称: {stats['collection_name']}")
            print(f"向量维度: {stats['vector_size']}")
            print(f"向量数量: {stats['vectors_count']}")
            print(f"分段数量: {stats['segments_count']}")
            print(f"状态: {stats['status']}")
            print("=" * 40 + "\n")
        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到服务 {args.url}")
            print(f"   请确保服务已启动: python knowledge_base_server.py")
            sys.exit(1)


if __name__ == '__main__':
    main()
