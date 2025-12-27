#!/usr/bin/env python3
"""
BigModel.cn 知识库 MCP Server

提供 Claude Code 直接查询 BigModel.cn 知识库的能力
"""

import json
import sys
import asyncio
from typing import Any
import requests

# 配置文件路径
CONFIG_FILE = "/home/shang/git/Indeptrader/confidential.json"
BASE_URL = "https://open.bigmodel.cn/api/llm-application/open"


class BigModelKnowledgeMCP:
    """BigModel.cn 知识库 MCP Server"""

    def __init__(self):
        """初始化"""
        self.api_key = self._load_api_key()
        self.kb_id = self._load_kb_id()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _load_api_key(self) -> str:
        """从配置文件加载 API Key"""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_key = config.get("bigmodel.cnAPI Key")
                if not api_key:
                    raise ValueError("配置文件中未找到 'bigmodel.cnAPI Key'")
                return api_key
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {CONFIG_FILE}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")

    def _load_kb_id(self) -> str:
        """从配置文件加载知识库 ID"""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                kb_id = config.get("bigmodel.cn知识库ID")
                if not kb_id:
                    raise ValueError("配置文件中未找到 'bigmodel.cn知识库ID'")
                return kb_id
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件不存在: {CONFIG_FILE}")
        except json.JSONDecodeError as e:
            raise ValueError(f"配置文件格式错误: {e}")

    def search_knowledge(
        self,
        query: str,
        top_k: int = 5,
        recall_method: str = "mixed"
    ) -> str:
        """检索知识库

        Args:
            query: 查询内容
            top_k: 返回结果数量 (1-20)
            recall_method: 检索方式 (embedding/keyword/mixed)

        Returns:
            检索结果的 JSON 字符串
        """
        url = f"{BASE_URL}/knowledge/retrieve"

        payload = {
            "query": query,
            "knowledge_ids": [self.kb_id],
            "top_k": min(top_k, 20),
            "recall_method": recall_method,
            "recall_ratio": 80
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    data = result.get('data', [])

                    # 格式化输出
                    output = []
                    output.append(f"🔍 查询: {query}")
                    output.append(f"📊 找到 {len(data)} 个相关结果\n")

                    for i, item in enumerate(data, 1):
                        score = item.get('score', 0)
                        text = item.get('text', '')[:500]
                        metadata = item.get('metadata', {})
                        doc_name = metadata.get('doc_name', 'Unknown')

                        output.append(f"【结果 {i}】相关度: {score:.2f}")
                        output.append(f"来源: {doc_name}")
                        output.append(f"内容: {text}...")
                        output.append("")

                    return "\n".join(output)
                else:
                    return f"❌ 检索失败: {result.get('message', 'Unknown error')}"
            else:
                return f"❌ HTTP 错误: {response.status_code} - {response.text}"

        except Exception as e:
            return f"❌ 检索异常: {str(e)}"

    def chat_with_knowledge(self, query: str) -> str:
        """与知识库对话（简化版，仅返回检索结果）

        Args:
            query: 用户问题

        Returns:
            检索到的知识片段
        """
        return self.search_knowledge(query, top_k=5)


# MCP Server 实现
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Tool, TextContent

# 创建 Server 实例
server = Server("bigmodel-kb")

# 初始化知识库客户端（全局）
kb_client = None


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """列出可用工具"""
    return [
        Tool(
            name="search_knowledge",
            description="检索 BigModel.cn 知识库。用于查询项目文档、研究报告、金融知识等。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "查询内容，例如：'收益率曲线倒挂的定义'、'如何使用 FRED API'"
                    },
                    "top_k": {
                        "type": "number",
                        "description": "返回结果数量 (1-20)，默认 5",
                        "default": 5
                    },
                    "recall_method": {
                        "type": "string",
                        "enum": ["embedding", "keyword", "mixed"],
                        "description": "检索方式：embedding=向量检索, keyword=关键词检索, mixed=混合检索（默认）",
                        "default": "mixed"
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
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: Any) -> list[TextContent]:
    """调用工具"""
    try:
        if name == "search_knowledge":
            query = arguments.get("query")
            top_k = arguments.get("top_k", 5)
            recall_method = arguments.get("recall_method", "mixed")

            result = kb_client.search_knowledge(query, top_k, recall_method)
            return [TextContent(type="text", text=result)]

        elif name == "chat_with_knowledge":
            query = arguments.get("query")
            result = kb_client.chat_with_knowledge(query)
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
        kb_client = BigModelKnowledgeMCP()
    except Exception as e:
        print(f"❌ 初始化失败: {e}", file=sys.stderr)
        sys.exit(1)

    # 运行服务器
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="bigmodel-kb",
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
