#!/usr/bin/env python3
"""
Qdrant 本地知识库 MCP Server

提供 Claude Code 直接查询本地 Qdrant 知识库的能力
性能优势: 检索延迟 < 100ms,无需网络连接
"""

import json
import sys
import asyncio
from typing import Any, Optional
from pathlib import Path

# 导入 QdrantKnowledgeBase
try:
    # 添加 scripts 目录到 Python 路径
    scripts_dir = Path(__file__).parent
    sys.path.insert(0, str(scripts_dir))
    from qdrant_kb import QdrantKnowledgeBase
except ImportError:
    print("❌ 无法导入 QdrantKnowledgeBase", file=sys.stderr)
    sys.exit(1)


class QdrantKnowledgeMCP:
    """Qdrant 本地知识库 MCP 客户端"""

    def __init__(
        self,
        storage_path: str = "/home/shang/qdrant_data",
        model_name: str = "BAAI/bge-small-zh-v1.5",
        device: str = "cuda"
    ):
        """初始化知识库客户端

        Args:
            storage_path: Qdrant 数据存储路径
            model_name: 嵌入模型名称
            device: 计算设备
        """
        self.storage_path = storage_path
        self.model_name = model_name
        self.device = device

        # 初始化知识库
        self.kb = QdrantKnowledgeBase(
            storage_path=storage_path,
            model_name=model_name,
            device=device
        )

    def search_knowledge(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.5,
        filters: Optional[dict] = None
    ) -> str:
        """检索知识库

        Args:
            query: 查询内容
            top_k: 返回结果数量
            score_threshold: 相似度阈值
            filters: 元数据过滤条件 (如 {"category": "project"})

        Returns:
            检索结果的格式化字符串
        """
        try:
            results = self.kb.search(
                query=query,
                top_k=top_k,
                score_threshold=score_threshold,
                filters=filters
            )

            if not results:
                return f"🔍 查询: {query}\n❓ 未找到相关结果"

            # 格式化输出
            output = []
            output.append(f"🔍 查询: {query}")
            output.append(f"📊 找到 {len(results)} 个相关结果\n")

            for i, result in enumerate(results, 1):
                score = result.get('score', 0)
                text = result.get('text', '')[:800]
                metadata = result.get('metadata', {})
                file_name = metadata.get('file_name', 'Unknown')
                category = metadata.get('category', 'N/A')
                file_type = metadata.get('file_type', 'N/A')

                output.append(f"【结果 {i}】相关度: {score:.4f}")
                output.append(f"📁 来源: {file_name}")
                output.append(f"🏷️  类别: {category} | 类型: {file_type}")
                output.append(f"📄 内容:\n{text}...")
                output.append("")

            return "\n".join(output)

        except Exception as e:
            return f"❌ 检索异常: {str(e)}"

    def chat_with_knowledge(self, query: str) -> str:
        """与知识库对话（快捷方式）

        Args:
            query: 用户问题

        Returns:
            检索到的知识片段
        """
        return self.search_knowledge(query, top_k=5)

    def list_documents(
        self,
        category: Optional[str] = None,
        file_type: Optional[str] = None,
        limit: int = 50
    ) -> str:
        """列出知识库中的文档

        Args:
            category: 按类别过滤
            file_type: 按文件类型过滤
            limit: 最大返回数量

        Returns:
            文档列表的格式化字符串
        """
        try:
            docs = self.kb.list_documents(
                category=category,
                file_type=file_type,
                limit=limit
            )

            if not docs:
                return "📚 知识库中没有文档"

            output = []
            output.append(f"📚 知识库文档列表（共 {len(docs)} 个）\n")

            for i, doc in enumerate(docs, 1):
                output.append(f"{i}. 📄 {doc['file_name']}")
                output.append(f"   类型: {doc['file_type']} | 类别: {doc['category']} | 块数: {doc['chunks']}")
                output.append(f"   路径: {doc['file_path']}")
                output.append("")

            return "\n".join(output)

        except Exception as e:
            return f"❌ 查询失败: {str(e)}"


# MCP Server 实现
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Tool, TextContent

# 创建 Server 实例
server = Server("qdrant-kb")

# 初始化知识库客户端（全局）
kb_client = None


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """列出可用工具"""
    return [
        Tool(
            name="search_knowledge",
            description=(
                "检索本地 Qdrant 知识库（优先使用）。"
                "用于查询项目文档、研究报告、API 使用说明、金融概念等。"
                "性能优势: < 100ms 响应时间,无需网络连接。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "查询内容，例如：'收益率曲线倒挂的定义'、'如何使用 FRED API'、'MCP 服务器配置'"
                    },
                    "top_k": {
                        "type": "number",
                        "description": "返回结果数量 (1-20)，默认 5",
                        "default": 5
                    },
                    "score_threshold": {
                        "type": "number",
                        "description": "相似度阈值 (0.0-1.0)，默认 0.5",
                        "default": 0.5
                    },
                    "filters": {
                        "type": "object",
                        "description": "元数据过滤条件，例如: {\"category\": \"project\"} 或 {\"file_type\": \"markdown\"}",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": ["project", "research", "business", "other"],
                                "description": "文档类别"
                            },
                            "file_type": {
                                "type": "string",
                                "description": "文件类型，如: markdown, pdf, docx"
                            }
                        }
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="chat_with_knowledge",
            description="与知识库对话（快捷方式）。自动检索并返回最相关的 5 个结果。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "你的问题"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="list_knowledge_documents",
            description="列出知识库中的所有文档。可按类别或文件类型过滤。",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["project", "research", "business", "other"],
                        "description": "按类别过滤（可选）"
                    },
                    "file_type": {
                        "type": "string",
                        "description": "按文件类型过滤，例如: markdown, pdf（可选）"
                    },
                    "limit": {
                        "type": "number",
                        "description": "最大返回数量，默认 50",
                        "default": 50
                    }
                }
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Any) -> list[TextContent]:
    """调用工具"""
    try:
        if name == "search_knowledge":
            query = arguments.get("query")
            top_k = arguments.get("top_k", 5)
            score_threshold = arguments.get("score_threshold", 0.5)
            filters = arguments.get("filters")

            result = kb_client.search_knowledge(query, top_k, score_threshold, filters)
            return [TextContent(type="text", text=result)]

        elif name == "chat_with_knowledge":
            query = arguments.get("query")
            result = kb_client.chat_with_knowledge(query)
            return [TextContent(type="text", text=result)]

        elif name == "list_knowledge_documents":
            category = arguments.get("category")
            file_type = arguments.get("file_type")
            limit = arguments.get("limit", 50)

            result = kb_client.list_documents(category, file_type, limit)
            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(type="text", text=f"❌ 未知工具: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"❌ 工具调用失败: {str(e)}")]


async def main():
    """主函数"""
    global kb_client

    # 初始化知识库客户端
    try:
        kb_client = QdrantKnowledgeMCP(
            storage_path="/home/shang/qdrant_data",
            model_name="BAAI/bge-small-zh-v1.5",
            device="cuda"  # 如果没有 GPU，改为 "cpu"
        )
    except Exception as e:
        print(f"❌ 初始化失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 运行服务器
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="qdrant-kb",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )


if __name__ == "__main__":
    import mcp.server.stdio
    asyncio.run(main())
