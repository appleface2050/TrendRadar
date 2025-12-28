#!/usr/bin/env python3
"""
Qdrant 知识库 FastAPI 服务

提供高性能的向量搜索 API，模型只加载一次
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import uvicorn

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition, MatchValue

# 自动从 settings.py 加载 HF_ENDPOINT
try:
    project_root = Path(__file__).parent.parent.parent
    settings_path = project_root / "settings.py"
    if settings_path.exists():
        with open(settings_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('HF_ENDPOINT='):
                    value = line.split('=', 1)[1].strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    os.environ['HF_ENDPOINT'] = value
                    print(f"✅ HF_ENDPOINT 设置为: {value}")
                    break
except Exception as e:
    print(f"⚠️  无法读取 HF_ENDPOINT: {e}")
    pass

from sentence_transformers import SentenceTransformer


# 全局变量
kb_instance = None


# Pydantic 模型
class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询文本")
    top_k: int = Field(5, ge=1, le=100, description="返回前 K 个结果")
    score_threshold: float = Field(0.5, ge=0.0, le=1.0, description="相似度阈值")
    filters: Optional[Dict[str, Any]] = Field(None, description="元数据过滤条件")


class SearchResult(BaseModel):
    score: float
    text: str
    metadata: Dict[str, Any]


class UploadRequest(BaseModel):
    file_path: str
    skip_duplicates: bool = True
    chunk_size: int = 500


class DeleteRequest(BaseModel):
    file_path: str


class ListDocumentsRequest(BaseModel):
    category: Optional[str] = None
    file_type: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    collection_exists: bool
    vectors_count: int


# FastAPI 应用
app = FastAPI(
    title="Qdrant 知识库服务",
    description="高性能向量搜索 API",
    version="1.0.0"
)


class KnowledgeBaseService:
    """知识库服务类"""

    COLLECTION_NAME = "knowledge_base"
    VECTOR_SIZE = 512
    SIMILARITY_THRESHOLD = 0.95

    def __init__(
        self,
        storage_path: str = "/home/shang/qdrant_data",
        model_name: str = "BAAI/bge-small-zh-v1.5",
        device: str = "cuda"
    ):
        self.storage_path = storage_path
        self.model_name = model_name
        self.device = device

        # 初始化 Qdrant 客户端
        self.client = QdrantClient(path=storage_path)

        # 初始化嵌入模型（强制使用本地缓存）
        self.model = SentenceTransformer(
            model_name,
            device=device,
            local_files_only=True  # 强制使用本地缓存，不访问网络
        )

        # 确保集合存在
        self._ensure_collection()

    def _ensure_collection(self):
        """确保集合存在"""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.COLLECTION_NAME not in collection_names:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )

    def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """搜索知识库"""
        # 生成查询向量
        query_vector = self.model.encode(query, normalize_embeddings=True)

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
        results = self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_vector.tolist(),
            limit=top_k,
            score_threshold=score_threshold,
            query_filter=search_filter
        ).points

        # 格式化结果
        formatted_results = []
        for result in results:
            formatted_results.append({
                "score": result.score,
                "text": result.payload.get("text", ""),
                "metadata": result.payload.get("metadata", {})
            })

        return formatted_results

    def get_collection_info(self) -> Dict[str, Any]:
        """获取集合信息"""
        try:
            info = self.client.get_collection(self.COLLECTION_NAME)
            return {
                "exists": True,
                "vectors_count": info.points_count,
                "segments_count": info.segments_count,
                "status": str(info.status)
            }
        except Exception:
            return {
                "exists": False,
                "vectors_count": 0,
                "segments_count": 0,
                "status": "not_found"
            }


# 启动事件
@app.on_event("startup")
async def startup_event():
    """服务启动时初始化知识库"""
    global kb_instance

    import time
    print("=" * 60)
    print("🚀 启动 Qdrant 知识库服务...")
    print("=" * 60)

    t0 = time.time()

    # 初始化知识库
    kb_instance = KnowledgeBaseService(
        storage_path="/home/shang/qdrant_data",
        model_name="BAAI/bge-small-zh-v1.5",
        device="cuda"
    )

    t1 = time.time()
    print(f"✅ 知识库初始化完成 ({(t1-t0)*1000:.2f}ms)")
    print("=" * 60)
    print(f"📍 服务地址: http://localhost:8000")
    print(f"📚 API 文档: http://localhost:8000/docs")
    print("=" * 60)


# API 端点
@app.get("/", summary="服务状态")
async def root():
    """根路径"""
    return {
        "service": "Qdrant 知识库服务",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "search": "/search",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse, summary="健康检查")
async def health_check():
    """检查服务健康状态"""
    if kb_instance is None:
        raise HTTPException(status_code=503, detail="服务未初始化")

    info = kb_instance.get_collection_info()

    return HealthResponse(
        status="healthy",
        model_loaded=True,
        collection_exists=info["exists"],
        vectors_count=info["vectors_count"]
    )


@app.post("/search", response_model=List[SearchResult], summary="搜索知识库")
async def search(request: SearchRequest):
    """在知识库中搜索

    - **query**: 搜索查询文本（必需）
    - **top_k**: 返回前 K 个结果（默认 5，最大 100）
    - **score_threshold**: 相似度阈值（默认 0.5）
    - **filters**: 元数据过滤条件（可选）

    示例:
    ```json
    {
        "query": "收益率曲线",
        "top_k": 5,
        "score_threshold": 0.5
    }
    ```
    """
    if kb_instance is None:
        raise HTTPException(status_code=503, detail="服务未初始化")

    import time
    t0 = time.time()

    results = kb_instance.search(
        query=request.query,
        top_k=request.top_k,
        score_threshold=request.score_threshold,
        filters=request.filters
    )

    t1 = time.time()
    print(f"⏱️  搜索 '{request.query}' 耗时: {(t1-t0)*1000:.2f}ms, 返回 {len(results)} 个结果")

    return results


@app.get("/stats", summary="获取统计信息")
async def get_stats():
    """获取知识库统计信息"""
    if kb_instance is None:
        raise HTTPException(status_code=503, detail="服务未初始化")

    info = kb_instance.get_collection_info()

    return {
        "model_name": kb_instance.model_name,
        "device": kb_instance.device,
        "storage_path": kb_instance.storage_path,
        "collection_name": kb_instance.COLLECTION_NAME,
        "vector_size": kb_instance.VECTOR_SIZE,
        **info
    }


def main():
    """启动服务"""
    import argparse

    parser = argparse.ArgumentParser(description='Qdrant 知识库 FastAPI 服务')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址')
    parser.add_argument('--port', type=int, default=8000, help='监听端口')
    parser.add_argument('--reload', action='store_true', help='自动重载（开发模式）')
    parser.add_argument('--storage', default='/home/shang/qdrant_data', help='Qdrant 存储路径')

    args = parser.parse_args()

    print(f"""
╔══════════════════════════════════════════════════════════╗
║         Qdrant 知识库 FastAPI 服务                        ║
╚══════════════════════════════════════════════════════════╝

📍 服务地址: http://{args.host}:{args.port}
📚 API 文档: http://localhost:{args.port}/docs
🔧 健康检查: http://localhost:{args.port}/health

按 Ctrl+C 停止服务
    """)

    uvicorn.run(
        "knowledge_base_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == '__main__':
    main()
