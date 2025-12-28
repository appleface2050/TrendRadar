#!/usr/bin/env python3
"""
Qdrant 本地向量知识库管理类

功能特性:
- 本地向量存储（Qdrant 持久化模式）
- BGE-M3 中文嵌入模型
- 元数据过滤（按类别、类型、标签、日期）
- 自动去重（基于文件路径、MD5、向量相似度）
- 支持多种文档格式（PDF、Markdown、Word、Excel）
"""

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import time

# 自动从 settings.py 加载 HF_ENDPOINT
try:
    import sys
    project_root = Path(__file__).parent.parent.parent
    settings_path = project_root / "settings.py"
    if settings_path.exists():
        with open(settings_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('HF_ENDPOINT='):
                    # 提取值（去除引号）
                    value = line.split('=', 1)[1].strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    os.environ['HF_ENDPOINT'] = value
                    break
except Exception as e:
    # 如果读取失败，使用默认值或保持不变
    pass

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue, Range
)
from sentence_transformers import SentenceTransformer
from unstructured.partition.auto import partition


class QdrantKnowledgeBase:
    """Qdrant 本地向量知识库管理类"""

    # 集合名称
    COLLECTION_NAME = "knowledge_base"

    # 向量维度（BAAI/bge-small-zh-v1.5）
    VECTOR_SIZE = 512

    # 相似度阈值（用于去重）
    SIMILARITY_THRESHOLD = 0.95

    def __init__(
        self,
        storage_path: str = "/home/shang/qdrant_data",
        model_name: str = "BAAI/bge-small-zh-v1.5",
        device: str = "cuda"
    ):
        """初始化知识库

        Args:
            storage_path: Qdrant 数据存储路径
            model_name: 嵌入模型名称
            device: 计算设备（cuda 或 cpu）
        """
        import time

        print(f"🚀 初始化 Qdrant 知识库...")
        print(f"   存储路径: {storage_path}")
        print(f"   嵌入模型: {model_name}")
        print(f"   计算设备: {device}")

        # 初始化 Qdrant 客户端（本地持久化模式）
        t0 = time.time()
        self.client = QdrantClient(path=storage_path)
        self.storage_path = storage_path
        t1 = time.time()
        print(f"⏱️  Qdrant客户端初始化耗时: {(t1-t0)*1000:.2f}ms")

        # 初始化嵌入模型
        print(f"📦 加载嵌入模型...")
        t2 = time.time()
        self.model = SentenceTransformer(model_name, device=device)
        self.model_name = model_name
        t3 = time.time()
        print(f"⏱️  模型加载耗时: {(t3-t2)*1000:.2f}ms")

        # 创建集合（如果不存在）
        t4 = time.time()
        self._ensure_collection()
        t5 = time.time()
        print(f"⏱️  集合检查耗时: {(t5-t4)*1000:.2f}ms")
        print(f"⏱️  初始化总耗时: {(t5-t0)*1000:.2f}ms")
        print(f"✅ 初始化完成\n")

    def _ensure_collection(self):
        """确保集合存在"""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.COLLECTION_NAME not in collection_names:
            print(f"📊 创建新集合: {self.COLLECTION_NAME}")
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )
            print(f"✅ 集合创建成功\n")

    def _compute_md5(self, file_path: str) -> str:
        """计算文件的 MD5 哈希值

        Args:
            file_path: 文件路径

        Returns:
            MD5 哈希值（十六进制字符串）
        """
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取文件元数据

        Args:
            file_path: 文件路径

        Returns:
            元数据字典
        """
        path_obj = Path(file_path)
        stat = os.stat(file_path)

        # 确定文件类型
        file_ext = path_obj.suffix.lower()
        file_type_map = {
            '.md': 'markdown',
            '.txt': 'text',
            '.pdf': 'pdf',
            '.docx': 'docx',
            '.doc': 'doc',
            '.xlsx': 'xlsx',
            '.xls': 'xls',
            '.csv': 'csv',
        }
        file_type = file_type_map.get(file_ext, 'unknown')

        # 确定类别（基于路径）
        path_parts = path_obj.parts
        if 'project' in path_parts:
            category = 'project'
        elif 'research' in path_parts:
            category = 'research'
        elif 'business' in path_parts:
            category = 'business'
        else:
            category = 'other'

        return {
            "file_path": str(path_obj.absolute()),
            "file_name": path_obj.name,
            "file_size": stat.st_size,
            "upload_time": datetime.now().isoformat(),
            "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "file_type": file_type,
            "category": category,
        }

    def _chunk_text(self, text: str, max_chunk_size: int = 500) -> List[str]:
        """将文本切分为多个块

        Args:
            text: 输入文本
            max_chunk_size: 每个块的最大字符数

        Returns:
            文本块列表
        """
        chunks = []
        current_chunk = ""
        sentences = text.split('\n')

        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_chunk_size:
                current_chunk += sentence + "\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + "\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _check_duplicate_by_path(self, file_path: str) -> Optional[Dict]:
        """基于文件路径检查重复

        Args:
            file_path: 文件路径

        Returns:
            如果存在重复，返回该文档的信息；否则返回 None
        """
        results = self.client.scroll(
            collection_name=self.COLLECTION_NAME,
            limit=1,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="metadata.file_path",
                        match=MatchValue(value=str(Path(file_path).absolute()))
                    )
                ]
            )
        )

        if results[0]:  # 如果找到点
            return results[0][0].payload
        return None

    def _check_duplicate_by_md5(self, md5_hash: str) -> Optional[Dict]:
        """基于 MD5 检查重复

        Args:
            md5_hash: MD5 哈希值

        Returns:
            如果存在重复，返回该文档的信息；否则返回 None
        """
        results = self.client.scroll(
            collection_name=self.COLLECTION_NAME,
            limit=1,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="metadata.md5",
                        match=MatchValue(value=md5_hash)
                    )
                ]
            )
        )

        if results[0]:
            return results[0][0].payload
        return None

    def upload_document(
        self,
        file_path: str,
        skip_duplicates: bool = True,
        chunk_size: int = 500
    ) -> Dict[str, Any]:
        """上传文档到知识库

        Args:
            file_path: 文件路径
            skip_duplicates: 是否跳过重复文档
            chunk_size: 文本块大小

        Returns:
            上传结果
        """
        print(f"📄 处理文件: {file_path}")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"文件不存在: {file_path}"
            }

        # 计算文件 MD5
        md5_hash = self._compute_md5(file_path)

        # 检查重复（基于文件路径）
        if skip_duplicates:
            duplicate = self._check_duplicate_by_path(file_path)
            if duplicate:
                print(f"   ⏭️  跳过（文件路径重复）")
                return {
                    "success": True,
                    "skipped": True,
                    "reason": "duplicate_path",
                    "existing_doc": duplicate
                }

            # 检查重复（基于 MD5）
            duplicate = self._check_duplicate_by_md5(md5_hash)
            if duplicate:
                print(f"   ⏭️  跳过（内容重复，MD5: {md5_hash[:8]}...）")
                return {
                    "success": True,
                    "skipped": True,
                    "reason": "duplicate_content",
                    "existing_doc": duplicate
                }

        # 提取元数据
        metadata = self._extract_metadata(file_path)
        metadata["md5"] = md5_hash

        # 解析文档内容
        print(f"   🔍 解析文档内容...")
        try:
            elements = partition(filename=file_path)
            text = "\n\n".join([str(e) for e in elements])
        except Exception as e:
            print(f"   ❌ 解析失败: {e}")
            return {
                "success": False,
                "error": f"文档解析失败: {str(e)}"
            }

        if not text or len(text.strip()) < 10:
            print(f"   ❌ 文档内容为空或过短")
            return {
                "success": False,
                "error": "文档内容为空或过短"
            }

        # 切分文本
        chunks = self._chunk_text(text, max_chunk_size=chunk_size)
        print(f"   📊 切分为 {len(chunks)} 个块")

        # 生成向量并创建点
        points = []
        for i, chunk in enumerate(chunks):
            # 生成嵌入向量
            embedding = self.model.encode(chunk, normalize_embeddings=True)

            # 创建点
            point_id = int(hashlib.md5(
                f"{file_path}_{i}".encode()
            ).hexdigest()[:16], 16)

            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_text": chunk[:500] + "..." if len(chunk) > 500 else chunk
            })

            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding.tolist(),
                    payload={
                        "text": chunk,
                        "metadata": chunk_metadata
                    }
                )
            )

        # 批量上传
        print(f"   ⬆️  上传到 Qdrant...")
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=points
        )

        print(f"   ✅ 上传成功: {len(chunks)} 个块\n")

        return {
            "success": True,
            "chunks": len(chunks),
            "metadata": metadata
        }

    def upload_directory(
        self,
        directory: str,
        skip_duplicates: bool = True,
        recursive: bool = True
    ) -> Dict[str, Any]:
        """批量上传目录中的所有文档

        Args:
            directory: 目录路径
            skip_duplicates: 是否跳过重复文档
            recursive: 是否递归处理子目录

        Returns:
            上传结果统计
        """
        supported_extensions = [
            '.md', '.txt', '.pdf', '.docx', '.doc',
            '.ppt', '.pptx', '.xls', '.xlsx', '.csv'
        ]

        # 查找所有支持的文件
        files = []
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                if any(filename.lower().endswith(ext) for ext in supported_extensions):
                    files.append(os.path.join(root, filename))

            if not recursive:
                break

        print(f"\n📁 扫描目录: {directory}")
        print(f"📊 找到 {len(files)} 个支持的文件\n")

        # 上传文件
        results = {
            "total": len(files),
            "success": 0,
            "skipped": 0,
            "failed": 0,
            "details": []
        }

        for i, file_path in enumerate(files, 1):
            print(f"[{i}/{len(files)}] ", end="")
            result = self.upload_document(file_path, skip_duplicates=skip_duplicates)

            if result.get("success"):
                if result.get("skipped"):
                    results["skipped"] += 1
                else:
                    results["success"] += 1
            else:
                results["failed"] += 1

            results["details"].append({
                "file": file_path,
                "result": result
            })

        # 打印统计
        print(f"\n{'='*60}")
        print(f"📊 上传统计:")
        print(f"   总计: {results['total']} 个文件")
        print(f"   ✅ 成功: {results['success']} 个")
        print(f"   ⏭️  跳过: {results['skipped']} 个")
        print(f"   ❌ 失败: {results['failed']} 个")
        print(f"{'='*60}\n")

        return results

    def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """在知识库中搜索

        Args:
            query: 查询文本
            top_k: 返回前 K 个结果
            score_threshold: 相似度阈值
            filters: 元数据过滤条件（可选）

        Returns:
            搜索结果列表
        """
        import time

        # 生成查询向量
        t0 = time.time()
        query_vector = self.model.encode(query, normalize_embeddings=True)
        t1 = time.time()
        print(f"⏱️  查询编码耗时: {(t1-t0)*1000:.2f}ms")

        # 构建过滤条件
        search_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(
                    FieldCondition(
                        key=f"metadata.{key}",
                        match=MatchValue(value=value)
                    )
                )
            if conditions:
                search_filter = Filter(must=conditions)

        # 搜索
        t2 = time.time()
        results = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_vector.tolist(),
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=search_filter
        ).points
        t3 = time.time()
        print(f"⏱️  Qdrant查询耗时: {(t3-t2)*1000:.2f}ms")

        # 格式化结果
        t4 = time.time()
        formatted_results = []
        for result in results:
            formatted_results.append({
                "score": result.score,
                "text": result.payload.get("text", ""),
                "metadata": result.payload.get("metadata", {})
            })
        t5 = time.time()
        print(f"⏱️  结果格式化耗时: {(t5-t4)*1000:.2f}ms")
        print(f"⏱️  搜索总耗时: {(t5-t0)*1000:.2f}ms")

        return formatted_results

    def delete_document(self, file_path: str) -> Dict[str, Any]:
        """删除文档（基于文件路径）

        Args:
            file_path: 文件路径

        Returns:
            删除结果
        """
        # 查找所有匹配的点
        results = self.client.scroll(
            collection_name=self.COLLECTION_NAME,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="metadata.file_path",
                        match=MatchValue(value=str(Path(file_path).absolute()))
                    )
                ]
            ),
            limit=1000,
            with_payload=False
        )

        points = results[0]
        if not points:
            return {
                "success": False,
                "error": "文档不存在"
            }

        # 删除所有匹配的点
        point_ids = [p.id for p in points]
        self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=point_ids
        )

        return {
            "success": True,
            "deleted_points": len(point_ids)
        }

    def list_documents(
        self,
        category: Optional[str] = None,
        file_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """列出知识库中的文档

        Args:
            category: 按类别过滤（可选）
            file_type: 按文件类型过滤（可选）
            limit: 最大返回数量

        Returns:
            文档列表
        """
        # 构建过滤条件
        conditions = []
        if category:
            conditions.append(
                FieldCondition(
                    key="metadata.category",
                    match=MatchValue(value=category)
                )
            )
        if file_type:
            conditions.append(
                FieldCondition(
                    key="metadata.file_type",
                    match=MatchValue(value=file_type)
                )
            )

        scroll_filter = Filter(must=conditions) if conditions else None

        # 滚动查询
        results = self.client.scroll(
            collection_name=self.COLLECTION_NAME,
            limit=limit,
            scroll_filter=scroll_filter,
            with_payload=["metadata"]
        )

        points = results[0]

        # 聚合文档（按文件路径）
        documents = {}
        for point in points:
            metadata = point.payload.get("metadata", {})
            file_path = metadata.get("file_path")

            if file_path not in documents:
                documents[file_path] = {
                    "file_path": file_path,
                    "file_name": metadata.get("file_name"),
                    "file_type": metadata.get("file_type"),
                    "category": metadata.get("category"),
                    "upload_time": metadata.get("upload_time"),
                    "chunks": 0
                }

            documents[file_path]["chunks"] += 1

        return list(documents.values())

    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息

        Returns:
            集合信息
        """
        info = self.client.get_collection(self.COLLECTION_NAME)

        return {
            "name": info.config.params.vectors.size,
            "vectors_count": info.points_count,
            "segments_count": info.segments_count,
            "status": info.status
        }


def main():
    """命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description='Qdrant 本地向量知识库管理工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # upload 命令
    upload_parser = subparsers.add_parser('upload', help='上传文档')
    upload_parser.add_argument('--file', help='单个文件路径')
    upload_parser.add_argument('--dir', help='目录路径（批量上传）')
    upload_parser.add_argument('--storage', default='/home/shang/qdrant_data', help='Qdrant 存储路径')

    # search 命令
    search_parser = subparsers.add_parser('search', help='搜索知识库')
    search_parser.add_argument('--query', required=True, help='查询文本')
    search_parser.add_argument('--top-k', type=int, default=5, help='返回前 K 个结果')
    search_parser.add_argument('--storage', default='/home/shang/qdrant_data', help='Qdrant 存储路径')

    # list 命令
    list_parser = subparsers.add_parser('list', help='列出文档')
    list_parser.add_argument('--category', help='按类别过滤')
    list_parser.add_argument('--type', help='按文件类型过滤')
    list_parser.add_argument('--storage', default='/home/shang/qdrant_data', help='Qdrant 存储路径')

    # delete 命令
    delete_parser = subparsers.add_parser('delete', help='删除文档')
    delete_parser.add_argument('--file', required=True, help='文件路径')
    delete_parser.add_argument('--storage', default='/home/shang/qdrant_data', help='Qdrant 存储路径')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 初始化知识库
    kb = QdrantKnowledgeBase(storage_path=args.storage)

    try:
        # 执行命令
        if args.command == 'upload':
            if args.file:
                kb.upload_document(args.file)
            elif args.dir:
                kb.upload_directory(args.dir)
            else:
                print("❌ 请指定 --file 或 --dir 参数")

        elif args.command == 'search':
            results = kb.search(args.query, top_k=args.top_k)
            print(f"\n🔍 搜索结果: '{args.query}'\n")
            for i, result in enumerate(results, 1):
                print(f"[{i}] 相关度: {result['score']:.4f}")
                print(f"    文件: {result['metadata'].get('file_name', 'Unknown')}")
                print(f"    内容: {result['text'][:200]}...")
                print()

        elif args.command == 'list':
            documents = kb.list_documents(category=args.category, file_type=args.type)
            print(f"\n📚 知识库中的文档（共 {len(documents)} 个）:\n")
            for doc in documents:
                print(f"  📄 {doc['file_name']}")
                print(f"     类型: {doc['file_type']} | 类别: {doc['category']} | 块数: {doc['chunks']}")
                print()

        elif args.command == 'delete':
            result = kb.delete_document(args.file)
            if result['success']:
                print(f"✅ 删除成功: {result['deleted_points']} 个数据块")
            else:
                print(f"❌ 删除失败: {result.get('error', 'Unknown error')}")
    finally:
        # 显式关闭客户端，避免 ImportError
        if hasattr(kb, 'client'):
            kb.client.close()


if __name__ == '__main__':
    main()
