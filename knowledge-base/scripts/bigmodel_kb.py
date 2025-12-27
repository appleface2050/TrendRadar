#!/usr/bin/env python3
"""
BigModel.cn 知识库管理工具

使用方法:
    # 设置 API Key
    python3 bigmodel_kb.py set-key "your-api-key"

    # 上传单个文件
    python3 bigmodel_kb.py upload --kb-id "kb_id" --file "path/to/file.pdf"

    # 批量上传目录
    python3 bigmodel_kb.py upload --kb-id "kb_id" --dir "path/to/dir"

    # 列出知识库中的文档
    python3 bigmodel_kb.py list --kb-id "kb_id"

    # 查询知识库
    python3 bigmodel_kb.py query --kb-id "kb_id" --query "你的问题"

    # 删除文档
    python3 bigmodel_kb.py delete --kb-id "kb_id" --doc-id "doc_id"
"""

import argparse
import json
import os
import sys
from pathlib import Path
import requests
from typing import Optional, List, Dict

# 配置文件路径
CONFIG_FILE = "/home/shang/git/Indeptrader/confidential.json"
BASE_URL = "https://open.bigmodel.cn/api/llm-application/open"


class BigModelKnowledgeBase:
    """BigModel.cn 知识库管理类"""

    def __init__(self, api_key: Optional[str] = None):
        """初始化

        Args:
            api_key: API Key，如果不提供则从配置文件读取
        """
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = self._load_api_key()

        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

    def _load_api_key(self) -> str:
        """从配置文件加载 API Key"""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                api_key = config.get("bigmodel.cnAPI Key")
                if not api_key:
                    print(f"❌ 错误: 配置文件中未找到 'bigmodel.cnAPI Key'")
                    sys.exit(1)
                return api_key
        except FileNotFoundError:
            print(f"❌ 错误: 配置文件不存在: {CONFIG_FILE}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ 错误: 配置文件格式错误: {e}")
            sys.exit(1)

    @staticmethod
    def set_api_key(api_key: str):
        """保存 API Key 到配置文件"""
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except FileNotFoundError:
            config = {}

        config["bigmodel.cnAPI Key"] = api_key

        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

        print(f"✅ API Key 已保存到 {CONFIG_FILE}")

    def upload_file(self, kb_id: str, file_path: str) -> Dict:
        """上传单个文件到知识库

        Args:
            kb_id: 知识库 ID
            file_path: 文件路径

        Returns:
            上传结果
        """
        if not os.path.exists(file_path):
            print(f"❌ 错误: 文件不存在: {file_path}")
            return {"success": False, "error": "File not found"}

        filename = os.path.basename(file_path)

        # 准备 multipart/form-data
        files = {
            'files': (filename, open(file_path, 'rb'))
        }

        data = {
            'knowledge_type': '1',  # 1: 按标题段落切片（动态解析）
        }

        url = f"{BASE_URL}/document/upload_document/{kb_id}"

        try:
            response = requests.post(
                url,
                headers=self.headers,
                files=files,
                data=data
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    success_infos = result.get('data', {}).get('successInfos', [])
                    if success_infos:
                        doc_id = success_infos[0].get('documentId')
                        print(f"✅ 上传成功: {filename}")
                        print(f"   文档 ID: {doc_id}")
                        return {"success": True, "documentId": doc_id}

                    failed_infos = result.get('data', {}).get('failedInfos', [])
                    if failed_infos:
                        reason = failed_infos[0].get('failReason', 'Unknown error')
                        print(f"❌ 上传失败: {filename}")
                        print(f"   原因: {reason}")
                        return {"success": False, "error": reason}
                else:
                    print(f"❌ 上传失败: {result.get('message', 'Unknown error')}")
                    return {"success": False, "error": result.get('message')}
            else:
                print(f"❌ 上传失败: HTTP {response.status_code}")
                print(f"   {response.text}")
                return {"success": False, "error": response.text}

        except Exception as e:
            print(f"❌ 上传异常: {e}")
            return {"success": False, "error": str(e)}
        finally:
            files['files'][1].close()

    def upload_directory(self, kb_id: str, directory: str) -> List[Dict]:
        """批量上传目录下的所有文件

        Args:
            kb_id: 知识库 ID
            directory: 目录路径

        Returns:
            上传结果列表
        """
        supported_extensions = ['.md', '.txt', '.pdf', '.docx', '.doc', '.ppt', '.pptx', '.xls', '.xlsx', '.csv']
        results = []

        print(f"📁 扫描目录: {directory}")

        # 递归查找所有支持格式的文件
        files = []
        for root, dirs, filenames in os.walk(directory):
            for filename in filenames:
                if any(filename.lower().endswith(ext) for ext in supported_extensions):
                    files.append(os.path.join(root, filename))

        print(f"📊 找到 {len(files)} 个支持格式的文件\n")

        for i, file_path in enumerate(files, 1):
            print(f"[{i}/{len(files)}] 正在上传: {os.path.basename(file_path)}")
            result = self.upload_file(kb_id, file_path)
            results.append({
                "file": file_path,
                "result": result
            })

        # 统计结果
        success_count = sum(1 for r in results if r["result"].get("success"))
        print(f"\n✅ 上传完成: {success_count}/{len(files)} 成功")

        return results

    def list_documents(self, kb_id: str, page: int = 1, size: int = 20) -> List[Dict]:
        """列出知识库中的所有文档

        Args:
            kb_id: 知识库 ID
            page: 页码（默认 1）
            size: 每页数量（默认 20）

        Returns:
            文档列表
        """
        url = f"{BASE_URL}/document/list"
        params = {
            "knowledge_id": kb_id,
            "page": page,
            "size": size
        }

        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    documents = result.get('data', {}).get('list', [])

                    print(f"\n📚 知识库 {kb_id} 中的文档:")
                    print(f"共 {len(documents)} 个文档（第 {page} 页）\n")

                    for doc in documents:
                        print(f"  📄 {doc.get('name', 'Unknown')}")
                        print(f"     ID: {doc.get('id', 'N/A')}")
                        print(f"     状态: {doc.get('status', 'Unknown')}")
                        print(f"     大小: {doc.get('word_num', 'N/A')} 字")
                        print(f"     创建时间: {doc.get('create_time', 'N/A')}")
                        print()

                    return documents
                else:
                    print(f"❌ 获取文档列表失败: {result.get('message', 'Unknown error')}")
                    return []
            else:
                print(f"❌ 获取文档列表失败: HTTP {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ 获取文档列表异常: {e}")
            return []

    def delete_document(self, kb_id: str, doc_id: str) -> Dict:
        """删除知识库中的文档

        Args:
            kb_id: 知识库 ID
            doc_id: 文档 ID

        Returns:
            删除结果
        """
        url = f"{BASE_URL}/document/delete"

        data = {
            "knowledge_id": kb_id,
            "document_id": doc_id
        }

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=data
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 200:
                    print(f"✅ 删除成功: 文档 ID {doc_id}")
                    return {"success": True}
                else:
                    print(f"❌ 删除失败: {result.get('message', 'Unknown error')}")
                    return {"success": False, "error": result.get('message')}
            else:
                print(f"❌ 删除失败: HTTP {response.status_code}")
                return {"success": False}

        except Exception as e:
            print(f"❌ 删除异常: {e}")
            return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description='BigModel.cn 知识库管理工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # set-key 命令
    subparsers.add_parser('set-key', help='设置 API Key')

    # upload 命令
    upload_parser = subparsers.add_parser('upload', help='上传文件到知识库')
    upload_parser.add_argument('--kb-id', required=True, help='知识库 ID')
    upload_parser.add_argument('--file', help='单个文件路径')
    upload_parser.add_argument('--dir', help='目录路径（批量上传）')

    # list 命令
    list_parser = subparsers.add_parser('list', help='列出知识库中的文档')
    list_parser.add_argument('--kb-id', required=True, help='知识库 ID')
    list_parser.add_argument('--page', type=int, default=1, help='页码（默认 1）')
    list_parser.add_argument('--size', type=int, default=20, help='每页数量（默认 20）')

    # delete 命令
    delete_parser = subparsers.add_parser('delete', help='删除文档')
    delete_parser.add_argument('--kb-id', required=True, help='知识库 ID')
    delete_parser.add_argument('--doc-id', required=True, help='文档 ID')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 处理命令
    if args.command == 'set-key':
        if len(sys.argv) != 3:
            print("用法: python3 bigmodel_kb.py set-key <your-api-key>")
            sys.exit(1)
        api_key = sys.argv[2]
        BigModelKnowledgeBase.set_api_key(api_key)

    else:
        # 其他命令需要初始化实例
        kb = BigModelKnowledgeBase()

        if args.command == 'upload':
            if args.file:
                kb.upload_file(args.kb_id, args.file)
            elif args.dir:
                kb.upload_directory(args.kb_id, args.dir)
            else:
                print("❌ 错误: 请指定 --file 或 --dir 参数")
                sys.exit(1)

        elif args.command == 'list':
            kb.list_documents(args.kb_id, args.page, args.size)

        elif args.command == 'delete':
            kb.delete_document(args.kb_id, args.doc_id)


if __name__ == '__main__':
    main()
