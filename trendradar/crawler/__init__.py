# coding=utf-8
"""
爬虫模块 - 数据抓取功能
"""

from trendradar.crawler.fetcher import DataFetcher
from trendradar.crawler.parallel_fetcher import ParallelDataFetcher, parallel_fetch_all

__all__ = ["DataFetcher", "ParallelDataFetcher", "parallel_fetch_all"]
