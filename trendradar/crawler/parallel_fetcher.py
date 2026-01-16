# coding=utf-8
"""
并行数据获取器 - 使用多进程并行提升数据抓取速度
"""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple, Optional, Union
import requests

from trendradar.crawler.fetcher import DataFetcher


class ParallelDataFetcher:
    """并行数据获取器 - 使用线程池并行获取多个平台数据"""

    def __init__(
        self,
        proxy_url: Optional[str] = None,
        api_url: Optional[str] = None,
        max_workers: int = 5,
        timeout: int = 15,
    ):
        """
        初始化并行数据获取器

        Args:
            proxy_url: 代理服务器 URL
            api_url: API 基础 URL（可选）
            max_workers: 最大并发线程数
            timeout: 单个请求超时时间
        """
        self.proxy_url = proxy_url
        self.api_url = api_url or DataFetcher.DEFAULT_API_URL
        self.max_workers = max_workers
        self.timeout = timeout

        # 代理配置
        self.proxies = None
        if self.proxy_url:
            self.proxies = {"http": self.proxy_url, "https": self.proxy_url}

    def _fetch_single_data(
        self, id_info: Union[str, Tuple[str, str]]
    ) -> Tuple[Optional[str], str, str]:
        """
        获取单个平台的数据（线程安全）

        Args:
            id_info: 平台ID或 (平台ID, 别名)

        Returns:
            (响应文本, 平台ID, 别名)
        """
        if isinstance(id_info, tuple):
            id_value, alias = id_info
        else:
            id_value = id_info
            alias = id_value

        url = f"{self.api_url}?id={id_value}"

        proxies = self.proxies

        try:
            # 使用 Session 保持连接复用
            with requests.Session() as session:
                session.headers.update(DataFetcher.DEFAULT_HEADERS)

                start_time = time.time()
                response = session.get(url, proxies=proxies, timeout=self.timeout)

                elapsed = time.time() - start_time

                data_text = response.text
                data_json = json.loads(data_text)

                status = data_json.get("status", "未知")

                if status not in ["success", "cache"]:
                    return None, id_value, alias

                status_info = "最新数据" if status == "success" else "缓存数据"

                if elapsed > 0.5:
                    print(
                        f"✅ {id_value} 获取成功 ({status_info}) - 耗时 {elapsed:.2f}秒"
                    )
                else:
                    print(
                        f"✓ {id_value} 获取成功 ({status_info}) - 耗时 {elapsed:.2f}秒"
                    )

                return data_text, id_value, alias

        except requests.Timeout:
            print(f"⏱ {id_value} 请求超时（{self.timeout}秒）")
            return None, id_value, alias
        except Exception as e:
            print(f"❌ {id_value} 请求失败: {e}")
            return None, id_value, alias

    def fetch_all_parallel(
        self,
        ids_list: List[Union[str, Tuple[str, str]]],
        progress_callback: Optional[callable] = None,
        request_interval: int = 100,
    ) -> Tuple[Dict, Dict, List]:
        """
        并行获取所有平台数据

        Args:
            ids_list: 平台ID列表，每个元素可以是字符串或(平台ID, 别名)
            progress_callback: 进度回调函数(progress, total, current)
            request_interval: 请求间隔（毫秒），仅用于日志显示

        Returns:
            (结果字典, ID到名称映射, 失败ID列表)
        """
        if not ids_list:
            print("⚠️ 没有需要获取的平台ID")
            return {}, {}, []

        results = {}
        id_to_name = {}
        failed_ids = []
        total = len(ids_list)

        print(f"🚀 开始并行获取 {total} 个平台数据（并发数: {self.max_workers}）...")
        if request_interval > 0:
            print(f"请求间隔: {request_interval} 毫秒（并行模式下仅用于日志）")

        def update_progress(current):
            if progress_callback:
                progress = (current / total) * 100
                progress_callback(progress, total, current)

        # 使用线程池并行获取
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_id_info = {
                executor.submit(self._fetch_single_data, id_info): id_info
                for id_info in ids_list
            }

            # 获取完成的任务
            for future in as_completed(future_to_id_info):
                id_info = future_to_id_info[future]

                try:
                    data_text, id_value, alias = future.result()

                    if data_text is not None:
                        # 尝试解析数据，转换为与 DataFetcher 一致的格式
                        data_json = json.loads(data_text)
                        items = data_json.get("items", [])

                        if items:
                            results[id_value] = {}
                            id_to_name[id_value] = alias

                            for index, item in enumerate(items, 1):
                                title = item.get("title")
                                if (
                                    title is None
                                    or isinstance(title, float)
                                    or not str(title).strip()
                                ):
                                    continue
                                title = str(title).strip()
                                url = item.get("url", "")
                                mobile_url = item.get("mobileUrl", "")

                                if title in results[id_value]:
                                    results[id_value][title]["ranks"].append(index)
                                else:
                                    results[id_value][title] = {
                                        "ranks": [index],
                                        "url": url,
                                        "mobileUrl": mobile_url,
                                    }

                        update_progress(len([f for f in future_to_id_info if f.done()]))

                except Exception as e:
                    if isinstance(id_info, tuple):
                        id_value, _ = id_info
                    else:
                        id_value = id_info
                    failed_ids.append(id_value)
                    print(f"❌ {id_value} 获取失败: {e}")

            # 等待所有任务完成
            completed = len([f for f in future_to_id_info if f.done()])
            update_progress(completed)

        successful_ids = [id_value for id_value, _ in future_to_id_info.items()]
        print(
            f"✅ 并行获取完成！成功: {len(successful_ids)}/{total}，失败: {len(failed_ids)}"
        )

        return results, id_to_name, failed_ids


def parallel_fetch_all(
    ids_list: List[Union[str, Tuple[str, str]]],
    proxy_url: Optional[str] = None,
    api_url: Optional[str] = None,
    max_workers: int = 5,
    timeout: int = 15,
    progress_callback: Optional[callable] = None,
) -> Tuple[Dict, Dict, List]:
    """
    并行获取所有平台数据的便捷函数

    Args:
        ids_list: 平台ID列表
        proxy_url: 代理服务器 URL（可选）
        api_url: API 基础 URL（可选）
        max_workers: 最大并发数（默认5）
        timeout: 单个请求超时时间（秒，默认15）
        progress_callback: 进度回调函数

    Returns:
        (结果字典, ID到名称映射, 失败ID列表)
    """
    fetcher = ParallelDataFetcher(
        proxy_url=proxy_url, api_url=api_url, max_workers=max_workers, timeout=timeout
    )

    return fetcher.fetch_all_parallel(ids_list, progress_callback)


if __name__ == "__main__":
    # 测试代码
    test_ids = [
        ("toutiao", "今日头条"),
        ("baidu", "百度热搜"),
        ("weibo", "微博"),
    ]

    def progress(progress, total, current):
        print(f"进度: {progress:.1f}% ({current}/{total})")

    results, id_to_name, failed_ids = parallel_fetch_all(
        test_ids, max_workers=3, timeout=10, progress_callback=progress
    )

    print(f"\n结果: {results}")
    print(f"ID映射: {id_to_name}")
    print(f"失败ID: {failed_ids}")
