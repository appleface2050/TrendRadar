#!/usr/bin/env python3
"""
Qdrant 知识库双向同步脚本

功能：
1. 扫描 Qdrant 中的所有文件
2. 扫描本地 knowledge-base 目录中的所有文件
3. 删除 Qdrant 中本地已不存在的文件
4. 添加本地新文件到 Qdrant

使用方法：
    # 同步模式（删除+添加）
    python sync_knowledge_base.py --dir /path/to/knowledge-base

    # 仅删除本地已不存在的文件
    python sync_knowledge_base.py --dir /path/to/knowledge-base --delete-only

    # 仅添加新文件
    python sync_knowledge_base.py --dir /path/to/knowledge-base --add-only

    # 预览模式（不执行实际操作）
    python sync_knowledge_base.py --dir /path/to/knowledge-base --dry-run
"""

import argparse
import hashlib
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Set, Dict, List, Tuple, Optional, Any
from contextlib import contextmanager

# 添加脚本目录到 Python 路径
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition, MatchValue, PointStruct
from sentence_transformers import SentenceTransformer
from unstructured.partition.auto import partition


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
                    break
except Exception:
    pass


class Timer:
    """简单的计时器类"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        """开始计时"""
        self.start_time = time.time()
        return self

    def stop(self):
        """停止计时"""
        self.end_time = time.time()
        return self

    def elapsed(self) -> float:
        """获取经过的时间（秒）"""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time

    def format_elapsed(self) -> str:
        """格式化时间显示"""
        elapsed = self.elapsed()
        if elapsed < 60:
            return f"{elapsed:.2f}秒"
        elif elapsed < 3600:
            minutes = int(elapsed // 60)
            seconds = elapsed % 60
            return f"{minutes}分{seconds:.1f}秒"
        else:
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = elapsed % 60
            return f"{hours}小时{minutes}分{seconds:.0f}秒"


@contextmanager
def timer_context(name: str, verbose: bool = True):
    """计时上下文管理器

    Args:
        name: 操作名称
        verbose: 是否输出日志
    """
    t = Timer()
    t.start()
    try:
        yield t
    finally:
        t.stop()
        if verbose:
            print(f"   ⏱️  {name}耗时: {t.format_elapsed()}")


class KnowledgeBaseSync:
    """知识库双向同步类"""

    # 支持的文件类型
    SUPPORTED_EXTENSIONS = {
        '.md', '.txt', '.pdf', '.docx', '.doc',
        '.ppt', '.pptx', '.xls', '.xlsx', '.csv'
    }

    # 向量维度
    VECTOR_SIZE = 1024  # BGE-M3 模型使用 1024 维

    # 集合名称
    COLLECTION_NAME = "knowledge_base"

    def __init__(
        self,
        client: QdrantClient,
        model: SentenceTransformer,
        verbose: bool = True
    ):
        """初始化同步器

        Args:
            client: QdrantClient 实例
            model: SentenceTransformer 嵌入模型实例
            verbose: 是否输出详细日志
        """
        self.client = client
        self.model = model
        self.verbose = verbose

    def _log(self, message: str):
        """输出日志"""
        if self.verbose:
            print(message)

    def _compute_md5(self, file_path: str) -> str:
        """计算文件的 MD5 哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """提取文件元数据"""
        path_obj = Path(file_path)
        stat = os.stat(file_path)

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

        path_parts = path_obj.parts
        if 'project' in path_parts:
            category = 'project'
        elif 'research' in path_parts:
            category = 'research'
        elif 'business' in path_parts:
            category = 'business'
        elif 'references' in path_parts:
            category = 'references'
        else:
            category = 'other'

        return {
            "file_path": str(path_obj.absolute()),
            "file_name": path_obj.name,
            "file_size": stat.st_size,
            "upload_time": time.time(),
            "last_modified": stat.st_mtime,
            "file_type": file_type,
            "category": category,
        }

    def _chunk_text(self, text: str, max_chunk_size: int = 500) -> List[str]:
        """将文本切分为多个块"""
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

    def _get_qdrant_files(self) -> Set[str]:
        """获取 Qdrant 中所有文件的路径

        Returns:
            文件路径集合
        """
        self._log("📊 正在扫描 Qdrant 中的文件...")

        all_files = set()
        offset = None
        limit = 100

        while True:
            results = self.client.scroll(
                collection_name=self.COLLECTION_NAME,
                limit=limit,
                offset=offset,
                with_payload=["metadata"],
                scroll_filter=None
            )

            points = results[0]
            if not points:
                break

            for point in points:
                metadata = point.payload.get("metadata", {})
                file_path = metadata.get("file_path")
                if file_path:
                    all_files.add(file_path)

            offset = results[1]
            if offset is None:
                break

        self._log(f"   ✅ Qdrant 中共有 {len(all_files)} 个文件\n")
        return all_files

    def _get_local_files(self, directory: str) -> Set[str]:
        """获取本地目录中所有支持的文件路径

        Args:
            directory: 本地目录路径

        Returns:
            文件路径集合（绝对路径）
        """
        self._log(f"📁 正在扫描本地目录: {directory}")

        local_files = set()
        dir_path = Path(directory).absolute()

        for file_path in dir_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                local_files.add(str(file_path))

        self._log(f"   ✅ 本地共有 {len(local_files)} 个支持的文件\n")
        return local_files

    def _compare_files(
        self,
        qdrant_files: Set[str],
        local_files: Set[str]
    ) -> Tuple[Set[str], Set[str]]:
        """对比 Qdrant 和本地文件

        Args:
            qdrant_files: Qdrant 中的文件路径
            local_files: 本地文件路径

        Returns:
            (需要删除的文件, 需要添加的文件)
        """
        files_to_delete = qdrant_files - local_files
        files_to_add = local_files - qdrant_files

        return files_to_delete, files_to_add

    def _check_duplicate_by_path(self, file_path: str) -> Optional[Dict]:
        """基于文件路径检查重复"""
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

        if results[0]:
            return results[0][0].payload
        return None

    def delete_missing_files(self, files: Set[str], dry_run: bool = False) -> Dict[str, any]:
        """删除本地已不存在的文件

        Args:
            files: 需要删除的文件路径集合
            dry_run: 是否为预览模式

        Returns:
            删除结果统计
        """
        if not files:
            self._log("✅ 没有需要删除的文件\n")
            return {"total": 0, "success": 0, "failed": 0, "skipped": 0}

        self._log(f"\n🗑️  准备删除 {len(files)} 个本地已不存在的文件:")
        for file_path in list(files)[:5]:
            self._log(f"   - {Path(file_path).name}")
        if len(files) > 5:
            self._log(f"   ... 还有 {len(files) - 5} 个文件")
        self._log("")

        if dry_run:
            self._log("⚠️  预览模式：不会实际删除文件\n")
            return {"total": len(files), "success": 0, "failed": 0, "skipped": len(files)}

        results = {
            "total": len(files),
            "success": 0,
            "failed": 0,
            "details": []
        }

        for i, file_path in enumerate(files, 1):
            self._log(f"[{i}/{len(files)}] 删除: {Path(file_path).name}")

            # 查找所有匹配的点
            scroll_results = self.client.scroll(
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

            points = scroll_results[0]

            if not points:
                self._log(f"   ⚠️  文件不存在于知识库中")
                results["failed"] += 1
                results["details"].append({
                    "file": file_path,
                    "result": {"success": False, "error": "not_found"}
                })
                continue

            # 删除所有匹配的点
            point_ids = [p.id for p in points]
            self.client.delete(
                collection_name=self.COLLECTION_NAME,
                points_selector=point_ids
            )

            self._log(f"   ✅ 成功删除 {len(point_ids)} 个数据块")
            results["success"] += 1

            results["details"].append({
                "file": file_path,
                "result": {"success": True, "deleted_points": len(point_ids)}
            })

        return results

    def upload_document(
        self,
        file_path: str,
        skip_duplicates: bool = True,
        chunk_size: int = 500
    ) -> Dict[str, Any]:
        """上传文档到知识库"""
        self._log(f"📄 处理文件: {file_path}")

        if not os.path.exists(file_path):
            return {
                "success": False,
                "error": f"文件不存在: {file_path}"
            }

        md5_hash = self._compute_md5(file_path)

        if skip_duplicates:
            duplicate = self._check_duplicate_by_path(file_path)
            if duplicate:
                self._log(f"   ⏭️  跳过（文件路径重复）")
                return {
                    "success": True,
                    "skipped": True,
                    "reason": "duplicate_path",
                    "existing_doc": duplicate
                }

        metadata = self._extract_metadata(file_path)
        metadata["md5"] = md5_hash

        self._log(f"   🔍 解析文档内容...")
        try:
            elements = partition(filename=file_path)
            text = "\n\n".join([str(e) for e in elements])
        except Exception as e:
            self._log(f"   ❌ 解析失败: {e}")
            return {
                "success": False,
                "error": f"文档解析失败: {str(e)}"
            }

        if not text or len(text.strip()) < 10:
            self._log(f"   ❌ 文档内容为空或过短")
            return {
                "success": False,
                "error": "文档内容为空或过短"
            }

        chunks = self._chunk_text(text, max_chunk_size=chunk_size)
        self._log(f"   📊 切分为 {len(chunks)} 个块")

        points = []
        for i, chunk in enumerate(chunks):
            embedding = self.model.encode(chunk, normalize_embeddings=True)

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
                {
                    "id": point_id,
                    "vector": embedding.tolist(),
                    "payload": {
                        "text": chunk,
                        "metadata": chunk_metadata
                    }
                }
            )

        self._log(f"   ⬆️  上传到 Qdrant...")
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[
                PointStruct(
                    id=p["id"],
                    vector=p["vector"],
                    payload=p["payload"]
                ) for p in points
            ]
        )

        self._log(f"   ✅ 上传成功: {len(chunks)} 个块\n")

        return {
            "success": True,
            "chunks": len(chunks),
            "metadata": metadata
        }

    def add_new_files(
        self,
        files: Set[str],
        dry_run: bool = False,
        chunk_size: int = 500
    ) -> Dict[str, any]:
        """添加本地新文件到知识库

        Args:
            files: 需要添加的文件路径集合
            dry_run: 是否为预览模式
            chunk_size: 文本块大小

        Returns:
            添加结果统计
        """
        if not files:
            self._log("✅ 没有需要添加的新文件\n")
            return {"total": 0, "success": 0, "skipped": 0, "failed": 0}

        self._log(f"\n📤 准备添加 {len(files)} 个新文件:")
        for file_path in list(files)[:5]:
            self._log(f"   + {Path(file_path).name}")
        if len(files) > 5:
            self._log(f"   ... 还有 {len(files) - 5} 个文件")
        self._log("")

        if dry_run:
            self._log("⚠️  预览模式：不会实际添加文件\n")
            return {"total": len(files), "success": 0, "skipped": 0, "failed": 0, "details": []}

        results = {
            "total": len(files),
            "success": 0,
            "skipped": 0,
            "failed": 0,
            "details": []
        }

        for i, file_path in enumerate(files, 1):
            file_start_time = time.time()
            self._log(f"[{i}/{len(files)}] 添加: {Path(file_path).name}")

            result = self.upload_document(
                file_path,
                skip_duplicates=True,
                chunk_size=chunk_size
            )

            if result.get("success"):
                if result.get("skipped"):
                    self._log(f"   ⏭️  跳过（已存在）")
                    results["skipped"] += 1
                else:
                    chunks = result.get("chunks", 0)
                    file_elapsed = time.time() - file_start_time
                    self._log(f"   ✅ 成功添加 {chunks} 个数据块 (耗时: {file_elapsed:.2f}秒)")
                    results["success"] += 1
            else:
                error = result.get("error", "Unknown error")
                self._log(f"   ❌ 添加失败: {error}")
                results["failed"] += 1

            results["details"].append({
                "file": file_path,
                "result": result
            })

        return results

    def sync(
        self,
        directory: str,
        delete_only: bool = False,
        add_only: bool = False,
        dry_run: bool = False,
        chunk_size: int = 500
    ) -> Dict[str, any]:
        """执行双向同步

        Args:
            directory: 本地目录路径
            delete_only: 仅删除本地已不存在的文件
            add_only: 仅添加新文件
            dry_run: 预览模式，不执行实际操作
            chunk_size: 文本块大小

        Returns:
            同步结果统计
        """
        # 启动总计时器
        total_timer = Timer().start()

        print("=" * 70)
        print("🔄 Qdrant 知识库双向同步")
        print("=" * 70)
        print(f"📁 本地目录: {directory}")
        print(f"🗑️  删除模式: {'仅删除' if delete_only else '是'}")
        print(f"📤 添加模式: {'仅添加' if add_only else '是'}")
        print(f"👀 预览模式: {'是' if dry_run else '否'}")
        print("=" * 70)
        print()

        # 0. 确保集合存在
        if not dry_run:
            collections = self.client.get_collections()
            if not any(c.name == self.COLLECTION_NAME for c in collections.collections):
                print(f"📦 创建新集合: {self.COLLECTION_NAME}")
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=self.VECTOR_SIZE,
                        distance=Distance.COSINE
                    )
                )
                print(f"   ✅ 集合创建成功（向量维度: {self.VECTOR_SIZE}）\n")

        # 1. 扫描文件
        qdrant_files = self._get_qdrant_files()
        local_files = self._get_local_files(directory)

        # 2. 对比文件
        self._log("🔍 对比文件差异...")
        files_to_delete, files_to_add = self._compare_files(qdrant_files, local_files)

        if files_to_delete:
            self._log(f"   需要删除: {len(files_to_delete)} 个文件")
        else:
            self._log("   需要删除: 0 个文件")

        if files_to_add:
            self._log(f"   需要添加: {len(files_to_add)} 个文件")
        else:
            self._log("   需要添加: 0 个文件")

        self._log("")

        # 3. 检查是否需要更新
        if not files_to_delete and not files_to_add:
            self._log("✅ 知识库已是最新，无需更新")
            total_timer.stop()
            self._log(f"⏱️  检查耗时: {total_timer.format_elapsed()}")
            self._log("")
            return {"needs_update": False}

        # 4. 执行同步
        sync_results = {
            "needs_update": True,
            "delete": {},
            "add": {}
        }

        if not add_only and files_to_delete:
            sync_results["delete"] = self.delete_missing_files(files_to_delete, dry_run)

        if not delete_only and files_to_add:
            sync_results["add"] = self.add_new_files(files_to_add, dry_run, chunk_size)

        # 5. 打印总结
        self._print_summary(sync_results, dry_run, total_timer)

        return sync_results

    def _print_summary(self, results: Dict[str, any], dry_run: bool, total_timer: Timer = None):
        """打印同步总结

        Args:
            results: 同步结果
            dry_run: 是否为预览模式
            total_timer: 总计时器
        """
        print("\n" + "=" * 70)
        print("📊 同步完成")
        print("=" * 70)

        # 删除统计
        delete_results = results.get("delete", {})
        if delete_results:
            total = delete_results.get("total", 0)
            success = delete_results.get("success", 0)
            failed = delete_results.get("failed", 0)
            skipped = delete_results.get("skipped", 0)

            print(f"\n🗑️  删除操作:")
            print(f"   总计: {total} 个文件")
            if not dry_run:
                print(f"   ✅ 成功: {success} 个")
                print(f"   ❌ 失败: {failed} 个")
            else:
                print(f"   ⏭️  跳过: {skipped} 个 (预览模式)")

        # 添加统计
        add_results = results.get("add", {})
        if add_results:
            total = add_results.get("total", 0)
            success = add_results.get("success", 0)
            failed = add_results.get("failed", 0)
            skipped = add_results.get("skipped", 0)

            print(f"\n📤 添加操作:")
            print(f"   总计: {total} 个文件")
            if not dry_run:
                print(f"   ✅ 成功: {success} 个")
                print(f"   ⏭️  跳过: {skipped} 个")
                print(f"   ❌ 失败: {failed} 个")
            else:
                print(f"   ⏭️  跳过: {total} 个 (预览模式)")

        # 打印总计时时间
        if total_timer:
            total_timer.stop()
            print(f"\n⏱️  总耗时: {total_timer.format_elapsed()}")

        print("\n" + "=" * 70 + "\n")


def check_port_open(host: str, port: int) -> bool:
    """检查端口是否开放"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0


def stop_kb_server(verbose: bool = True) -> bool:
    """停止知识库服务

    Args:
        verbose: 是否输出详细日志

    Returns:
        是否成功停止
    """
    if verbose:
        print("🛑 检查知识库服务状态...")

    # 查找知识库服务进程
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'knowledge_base_server.py'],
            capture_output=True,
            text=True
        )
        pids = result.stdout.strip().split('\n') if result.stdout.strip() else []

        if not pids or not pids[0]:
            if verbose:
                print("   ℹ️  没有运行中的知识库服务")
            return True

        if verbose:
            print(f"   🔍 发现 {len(pids)} 个知识库服务进程")

        # 停止所有知识库服务进程
        for pid in pids:
            if pid:
                try:
                    os.kill(int(pid), signal.SIGTERM)
                    if verbose:
                        print(f"   ✅ 已停止进程 {pid}")
                except ProcessLookupError:
                    if verbose:
                        print(f"   ⚠️  进程 {pid} 已不存在")
                except Exception as e:
                    if verbose:
                        print(f"   ❌ 停止进程 {pid} 失败: {e}")
                    return False

        # 等待进程完全退出
        if verbose:
            print("   ⏳ 等待服务完全停止...")
        time.sleep(2)

        # 验证是否已停止
        result = subprocess.run(
            ['pgrep', '-f', 'knowledge_base_server.py'],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            if verbose:
                print("   ⚠️  服务仍在运行，尝试强制停止...")
                subprocess.run(['pkill', '-9', '-f', 'knowledge_base_server.py'])
                time.sleep(1)

        if verbose:
            print("   ✅ 知识库服务已停止\n")

        return True

    except Exception as e:
        if verbose:
            print(f"   ❌ 停止服务时出错: {e}\n")
        return False


def start_kb_server(script_path: str = None, verbose: bool = True) -> bool:
    """启动知识库服务

    Args:
        script_path: 启动脚本路径（默认为 knowledge-base/scripts/start_kb_server.sh）
        verbose: 是否输出详细日志

    Returns:
        是否成功启动
    """
    if verbose:
        print("🚀 准备启动知识库服务...")

    # 默认启动脚本路径
    if script_path is None:
        script_dir = Path(__file__).parent
        script_path = script_dir / "start_kb_server.sh"

    script_path = Path(script_path)

    if not script_path.exists():
        if verbose:
            print(f"   ❌ 启动脚本不存在: {script_path}")
            print(f"   💡 请手动启动知识库服务")
        return False

    if verbose:
        print(f"   📜 使用启动脚本: {script_path}")

    # 检查服务是否已经在运行
    if check_port_open('localhost', 8000):
        if verbose:
            print(f"   ✅ 服务已在运行中（端口 8000 已开放）\n")
        return True

    # 等待所有 sync_knowledge_base.py 进程退出
    if verbose:
        print("   ⏳ 等待同步脚本完成...")
    max_wait = 5
    for i in range(max_wait):
        result = subprocess.run(
            ['pgrep', '-f', 'sync_knowledge_base.py'],
            capture_output=True,
            text=True
        )
        if not result.stdout.strip():
            if verbose and i > 0:
                print(f"   ✅ 同步脚本已完成 (等待 {i}秒)")
            break
        time.sleep(1)
    else:
        if verbose:
            print(f"   ⚠️  同步脚本仍在运行，但继续尝试启动服务")

    try:
        # 使用后台方式启动脚本，创建新会话以独立运行
        # 使用 PIPE 捕获输出，但使用 start_new_session 确保进程独立
        process = subprocess.Popen(
            ['bash', str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True  # 创建新的会话，使进程独立于父进程
        )

        if verbose:
            print(f"   ✅ 启动命令已执行 (PID: {process.pid})")
            print("   ⏳ 等待服务启动...")

        # 等待服务启动（启动脚本会等待 10 秒）
        max_wait = 15
        for i in range(max_wait):
            time.sleep(1)

            # 检查脚本进程是否已完成
            return_code = process.poll()
            if return_code is not None:
                # 脚本已完成，检查输出
                stdout, stderr = process.communicate()
                if return_code == 0:
                    # 启动成功
                    if check_port_open('localhost', 8000):
                        if verbose:
                            print(f"   ✅ 服务已启动 (耗时 {i+1}秒)\n")
                        return True
                    else:
                        # 脚本返回成功但端口未开放
                        if verbose:
                            print(f"   ⚠️  启动脚本完成但端口未开放")
                            print(f"   输出: {stdout}")
                        time.sleep(5)  # 额外等待
                        if check_port_open('localhost', 8000):
                            if verbose:
                                print(f"   ✅ 服务已启动 (延迟启动)\n")
                            return True
                        return False
                else:
                    # 启动失败
                    if verbose:
                        print(f"   ⚠️  服务启动失败")
                        if stdout:
                            print(f"   输出: {stdout}")
                        if stderr:
                            print(f"   错误: {stderr}")
                        print()
                    return False

            # 检查端口是否已开放
            if check_port_open('localhost', 8000):
                if verbose:
                    print(f"   ✅ 服务已启动 (耗时 {i+1}秒)\n")
                return True

        # 超时但脚本还在运行
        if verbose:
            print(f"   ⚠️  服务启动超时，但脚本仍在运行\n")
        return True

    except Exception as e:
        if verbose:
            print(f"   ❌ 启动服务时出错: {e}\n")
        return False


def init_qdrant_client(
    storage_path: str = None,
    qdrant_url: str = None,
    qdrant_port: int = 6333
) -> QdrantClient:
    """初始化 Qdrant 客户端

    自动检测使用本地存储模式还是 HTTP 连接模式

    Args:
        storage_path: 本地存储路径
        qdrant_url: Qdrant 服务 URL
        qdrant_port: Qdrant 服务端口

    Returns:
        QdrantClient 实例
    """
    # 如果指定了 URL，使用 HTTP 连接
    if qdrant_url:
        print(f"🔗 使用 HTTP 模式连接到 Qdrant: {qdrant_url}")
        return QdrantClient(url=qdrant_url)

    # 如果指定了存储路径，检查是否可以访问
    if storage_path:
        # 检查端口 6333 (Qdrant 默认端口)
        if check_port_open('localhost', 6333):
            print(f"🔗 检测到 Qdrant 服务运行在端口 6333，使用 HTTP 模式")
            return QdrantClient(url="http://localhost:6333")

        # 检查其他常见端口
        for port in [6334, 6335]:
            if check_port_open('localhost', port):
                print(f"🔗 检测到 Qdrant 服务运行在端口 {port}，使用 HTTP 模式")
                return QdrantClient(url=f"http://localhost:{port}")

        # 尝试使用本地存储模式
        try:
            print(f"💾 尝试使用本地存储模式: {storage_path}")
            return QdrantClient(path=storage_path)
        except Exception as e:
            print(f"❌ 无法使用本地存储模式: {e}")
            print(f"\n提示: 请确保以下条件之一满足:")
            print(f"  1. Qdrant 服务正在运行（端口 6333 或其他）")
            print(f"  2. 没有其他进程正在使用 Qdrant 本地存储")
            print(f"  3. 使用 --qdrant-url 参数指定 Qdrant 服务地址")
            raise

    # 默认使用 localhost
    print(f"🔗 使用 HTTP 模式连接到 Qdrant: http://localhost:{qdrant_port}")
    return QdrantClient(url=f"http://localhost:{qdrant_port}")


def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(
        description='Qdrant 知识库双向同步脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 完整同步（默认会自动停止和重启服务）
  python sync_knowledge_base.py --dir /path/to/knowledge-base

  # 禁用自动重启服务
  python sync_knowledge_base.py --dir /path/to/knowledge-base --no-auto-restart

  # 仅删除本地已不存在的文件
  python sync_knowledge_base.py --dir /path/to/knowledge-base --delete-only

  # 仅添加新文件
  python sync_knowledge_base.py --dir /path/to/knowledge-base --add-only

  # 预览模式（不执行实际操作）
  python sync_knowledge_base.py --dir /path/to/knowledge-base --dry-run

  # 连接到远程 Qdrant 服务
  python sync_knowledge_base.py --dir /path/to/knowledge-base --qdrant-url http://localhost:6333
        """
    )

    parser.add_argument(
        '--dir',
        required=True,
        help='本地知识库目录路径'
    )

    parser.add_argument(
        '--storage',
        default='/home/shang/qdrant_data',
        help='Qdrant 数据存储路径（默认: /home/shang/qdrant_data）'
    )

    parser.add_argument(
        '--qdrant-url',
        help='Qdrant 服务 URL（例如: http://localhost:6333）'
    )

    parser.add_argument(
        '--qdrant-port',
        type=int,
        default=6333,
        help='Qdrant 服务端口（默认: 6333）'
    )

    parser.add_argument(
        '--model-name',
        default='BAAI/bge-m3',
        help='嵌入模型名称（默认: BAAI/bge-m3）'
    )

    parser.add_argument(
        '--device',
        default='cuda',
        help='计算设备（cuda 或 cpu，默认: cuda）'
    )

    parser.add_argument(
        '--delete-only',
        action='store_true',
        help='仅删除本地已不存在的文件'
    )

    parser.add_argument(
        '--add-only',
        action='store_true',
        help='仅添加本地新文件'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，不执行实际操作'
    )

    parser.add_argument(
        '--chunk-size',
        type=int,
        default=500,
        help='文本块大小（默认: 500）'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='静默模式，减少输出'
    )

    parser.add_argument(
        '--no-auto-restart',
        action='store_true',
        help='禁用自动停止和重启知识库服务（默认启用）'
    )

    parser.add_argument(
        '--start-script',
        help='知识库服务启动脚本路径（默认: knowledge-base/scripts/start_kb_server.sh）'
    )

    args = parser.parse_args()

    # 启动总运行时间计时器
    script_timer = Timer().start()

    # 检查目录是否存在
    if not Path(args.dir).exists():
        print(f"❌ 错误: 目录不存在: {args.dir}")
        sys.exit(1)

    # auto_restart 默认为 True，除非指定了 --no-auto-restart
    auto_restart = not args.no_auto_restart

    # 检查服务是否在运行（用于后续判断是否需要启动）
    service_was_running = False
    if auto_restart:
        # 先检查服务是否在运行
        try:
            result = subprocess.run(
                ['pgrep', '-f', 'knowledge_base_server.py'],
                capture_output=True,
                text=True
            )
            service_was_running = bool(result.stdout.strip())
        except Exception:
            service_was_running = False

        # 自动停止服务
        print("\n" + "=" * 70)
        if not stop_kb_server(verbose=not args.quiet):
            print("⚠️  停止服务失败，继续执行同步...")
            print("=" * 70 + "\n")
        else:
            print("=" * 70 + "\n")

    print("🚀 初始化 Qdrant 客户端...")
    client = init_qdrant_client(
        storage_path=args.storage,
        qdrant_url=args.qdrant_url,
        qdrant_port=args.qdrant_port
    )
    print()

    print("📦 加载嵌入模型...")
    print(f"   模型: {args.model_name}")
    print(f"   设备: {args.device}")

    # 模型加载计时
    model_load_timer = Timer().start()

    # 优先使用本地缓存路径，避免网络请求和超时
    cache_dir = Path.home() / '.cache' / 'huggingface' / 'hub'
    model_cache = cache_dir / f"models--{'--'.join(args.model_name.split('/'))}"

    model_path = None
    if model_cache.exists():
        snapshots = list((model_cache / 'snapshots').glob('*'))
        if snapshots:
            # 使用最新的快照
            model_path = max(snapshots, key=lambda p: p.stat().st_mtime)
            print(f"   📁 使用本地缓存: {model_path}")

    if model_path and model_path.exists():
        # 直接加载本地路径
        model = SentenceTransformer(str(model_path), device=args.device)
    else:
        # 回退到标准加载方式
        model = SentenceTransformer(
            args.model_name,
            device=args.device,
            local_files_only=True
        )

    model_load_timer.stop()
    print(f"   ⏱️  模型加载耗时: {model_load_timer.format_elapsed()}")
    print("✅ 模型加载完成\n")

    try:
        # 创建同步器
        syncer = KnowledgeBaseSync(client, model, verbose=not args.quiet)

        # 执行同步
        sync_results = syncer.sync(
            directory=args.dir,
            delete_only=args.delete_only,
            add_only=args.add_only,
            dry_run=args.dry_run,
            chunk_size=args.chunk_size
        )

        # 检查是否需要更新
        if not sync_results.get("needs_update", True):
            print("💡 知识库已是最新，无需重启服务\n")
            # 如果服务原本没有运行，还是要启动它
            if auto_restart and not service_was_running and not args.dry_run:
                print("\n" + "=" * 70)
                print("🔄 检测到服务原本未运行，正在启动...")
                print("=" * 70)

                # 先关闭客户端，释放 Qdrant 资源
                client.close()
                if not args.quiet:
                    print("   ✅ 已释放 Qdrant 客户端资源")

                # 等待一下确保资源完全释放
                time.sleep(2)

                if not start_kb_server(script_path=args.start_script, verbose=not args.quiet):
                    print("💡 请手动启动知识库服务:")
                    print(f"   bash {Path(args.start_script) if args.start_script else Path(__file__).parent / 'start_kb_server.sh'}")
                print("=" * 70 + "\n")

                script_timer.stop()
                sys.exit(0)
            else:
                client.close()
                script_timer.stop()
                sys.exit(0)

    finally:
        # 关闭客户端
        try:
            client.close()
        except Exception:
            pass

    # 自动重启服务
    if auto_restart and not args.dry_run:
        print("\n" + "=" * 70)
        if not start_kb_server(script_path=args.start_script, verbose=not args.quiet):
            print("💡 请手动启动知识库服务:")
            print(f"   bash {Path(args.start_script) if args.start_script else Path(__file__).parent / 'start_kb_server.sh'}")
        print("=" * 70 + "\n")

    # 停止总计时器并输出
    script_timer.stop()
    print("=" * 70)
    print(f"🎉 脚本执行完成！总运行时间: {script_timer.format_elapsed()}")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
