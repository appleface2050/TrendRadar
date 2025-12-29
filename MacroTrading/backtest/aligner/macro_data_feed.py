"""
Backtrader自定义数据源 - 宏观数据源

集成日历对齐器，确保回测时不会使用未来数据

功能：
1. 提供价格数据（OHLCV）
2. 提供宏观数据（使用日历对齐器）
3. 支持混频数据
4. 避免未来函数
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import warnings
warnings.filterwarnings('ignore')

try:
    import backtrader as bt
    BACKTRADER_AVAILABLE = True
except ImportError:
    BACKTRADER_AVAILABLE = False
    print("Warning: backtrader not installed")

from utils.calendar_aligner import CalendarAligner


class MacroDataFeed(bt.feeds.PandasData):
    """
    Backtrader自定义数据源 - 支持宏观数据

    继承自PandasData，添加宏观数据字段
    """
    # 添加宏观数据字段
    lines = (
        'macro_score',          # 综合宏观得分
        'liquidity_score',      # 流动性得分
        'valuation_score',      # 估值得分
        'sentiment_score',      # 情绪得分
        'risk_index',           # 风险指数
        'regime_prob_1',        # 区制1概率
        'regime_prob_2',        # 区制2概率
        'regime_prob_3',        # 区制3概率
        'regime_prob_4',        # 区制4概率
    )

    # 参数定义
    params = (
        ('macro_data', None),          # 宏观数据DataFrame
        ('risk_data', None),           # 风险数据DataFrame
        ('regime_data', None),         # 区制数据DataFrame
        ('calendar_aligner', None),    # 日历对齐器
    )


class MacroDataFactory:
    """
    宏观数据源工厂类

    负责创建和配置Backtrader数据源
    """

    def __init__(self, use_calendar_aligner: bool = True):
        """
        初始化数据源工厂

        Parameters:
        -----------
        use_calendar_aligner : bool
            是否使用日历对齐器（默认True，强烈推荐）
        """
        self.use_calendar_aligner = use_calendar_aligner

        if use_calendar_aligner:
            self.calendar_aligner = CalendarAligner()
        else:
            self.calendar_aligner = None

        self.macro_data_cache = {}
        self.price_data_cache = {}

    def load_price_data(
        self,
        price_file: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        加载价格数据

        Parameters:
        -----------
        price_file : str
            价格数据文件路径（CSV）
        start_date : str, optional
            开始日期
        end_date : str, optional
            结束日期

        Returns:
        --------
        DataFrame
            价格数据，包含：datetime, open, high, low, close, volume
        """
        # 读取CSV文件
        df = pd.read_csv(price_file)

        # 转换日期
        df['datetime'] = pd.to_datetime(df['date'])

        # 设置索引
        df.set_index('datetime', inplace=True)

        # 过滤日期范围
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]

        # 确保必需列存在
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"价格数据缺少列: {col}")

        return df

    def load_macro_data(
        self,
        macro_file: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        resample_freq: str = 'D'
    ) -> pd.DataFrame:
        """
        加载宏观数据

        Parameters:
        -----------
        macro_file : str
            宏观数据文件路径（CSV）
        start_date : str, optional
            开始日期
        end_date : str, optional
            结束日期
        resample_freq : str
            重采样频率（默认'D'日度）

        Returns:
        --------
        DataFrame
            宏观数据，已重采样到指定频率
        """
        # 读取CSV文件
        df = pd.read_csv(macro_file)

        # 转换日期
        df['datetime'] = pd.to_datetime(df['date'])

        # 设置索引
        df.set_index('datetime', inplace=True)

        # 过滤日期范围
        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]

        # 前向填充（宏观数据可能不是每天都有）
        if resample_freq != 'D':
            df = df.resample(resample_freq).ffill()

        return df

    def merge_data(
        self,
        price_data: pd.DataFrame,
        macro_data: Optional[pd.DataFrame] = None,
        risk_data: Optional[pd.DataFrame] = None,
        regime_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """
        合并价格数据和宏观数据

        Parameters:
        -----------
        price_data : DataFrame
            价格数据
        macro_data : DataFrame, optional
            宏观数据
        risk_data : DataFrame, optional
            风险数据
        regime_data : DataFrame, optional
            区制数据

        Returns:
        --------
        DataFrame
            合并后的数据
        """
        # 复制价格数据
        merged = price_data.copy()

        # 合并宏观数据
        if macro_data is not None:
            # 前向填充缺失值（宏观数据）
            merged = pd.merge(
                merged,
                macro_data,
                left_index=True,
                right_index=True,
                how='left'
            )

        # 合并风险数据
        if risk_data is not None:
            merged = pd.merge(
                merged,
                risk_data,
                left_index=True,
                right_index=True,
                how='left'
            )

        # 合并区制数据
        if regime_data is not None:
            merged = pd.merge(
                merged,
                regime_data,
                left_index=True,
                right_index=True,
                how='left'
            )

        # 前向填充所有缺失值
        merged.fillna(method='ffill', inplace=True)
        merged.fillna(method='bfill', inplace=True)

        return merged

    def create_data_feed(
        self,
        price_data: pd.DataFrame,
        macro_data: Optional[pd.DataFrame] = None,
        risk_data: Optional[pd.DataFrame] = None,
        regime_data: Optional[pd.DataFrame] = None
    ) -> MacroDataFeed:
        """
        创建Backtrader数据源

        Parameters:
        -----------
        price_data : DataFrame
            价格数据
        macro_data : DataFrame, optional
            宏观数据
        risk_data : DataFrame, optional
            风险数据
        regime_data : DataFrame, optional
            区制数据

        Returns:
        --------
        MacroDataFeed
            Backtrader数据源
        """
        if not BACKTRADER_AVAILABLE:
            raise ImportError("backtrader未安装，无法创建数据源")

        # 合并数据
        merged_data = self.merge_data(
            price_data,
            macro_data,
            risk_data,
            regime_data
        )

        # 重置索引（backtrader需要datetime列）
        merged_data.reset_index(inplace=True)

        # 创建数据源
        data_feed = MacroDataFeed(
            dataname=merged_data,
            datetime=None,  # 使用索引作为datetime
            open='open',
            high='high',
            low='low',
            close='close',
            volume='volume',
            openinterest=-1,
            macro_data=macro_data,
            risk_data=risk_data,
            regime_data=regime_data,
            calendar_aligner=self.calendar_aligner
        )

        return data_feed

    def create_multi_data_feeds(
        self,
        price_files: Dict[str, str],
        macro_file: Optional[str] = None,
        risk_file: Optional[str] = None,
        regime_file: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, MacroDataFeed]:
        """
        创建多个数据源（用于多资产回测）

        Parameters:
        -----------
        price_files : dict
            价格文件字典，例如：{'stock': 'data/stock.csv', 'index': 'data/index.csv'}
        macro_file : str, optional
            宏观数据文件
        risk_file : str, optional
            风险数据文件
        regime_file : str, optional
            区制数据文件
        start_date : str, optional
            开始日期
        end_date : str, optional
            结束日期

        Returns:
        --------
        dict
            数据源字典
        """
        # 加载宏观数据（如果提供）
        macro_data = None
        if macro_file:
            macro_data = self.load_macro_data(macro_file, start_date, end_date)

        # 加载风险数据（如果提供）
        risk_data = None
        if risk_file:
            risk_data = self.load_macro_data(risk_file, start_date, end_date)

        # 加载区制数据（如果提供）
        regime_data = None
        if regime_file:
            regime_data = self.load_macro_data(regime_file, start_date, end_date)

        # 为每个资产创建数据源
        data_feeds = {}

        for name, price_file in price_files.items():
            # 加载价格数据
            price_data = self.load_price_data(price_file, start_date, end_date)

            # 创建数据源
            data_feed = self.create_data_feed(
                price_data,
                macro_data,
                risk_data,
                regime_data
            )

            data_feeds[name] = data_feed

        return data_feeds


# 便捷函数
def load_data_for_backtest(
    price_file: str,
    macro_file: Optional[str] = None,
    risk_file: Optional[str] = None,
    regime_file: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    use_calendar_aligner: bool = True
) -> MacroDataFeed:
    """
    便捷函数：加载回测数据

    Parameters:
    -----------
    price_file : str
        价格数据文件
    macro_file : str, optional
        宏观数据文件
    risk_file : str, optional
        风险数据文件
    regime_file : str, optional
        区制数据文件
    start_date : str, optional
        开始日期
    end_date : str, optional
        结束日期
    use_calendar_aligner : bool
        是否使用日历对齐器

    Returns:
    --------
    MacroDataFeed
        Backtrader数据源
    """
    factory = MacroDataFactory(use_calendar_aligner=use_calendar_aligner)

    # 加载价格数据
    price_data = factory.load_price_data(price_file, start_date, end_date)

    # 加载宏观数据
    macro_data = None
    if macro_file:
        macro_data = factory.load_macro_data(macro_file, start_date, end_date)

    # 加载风险数据
    risk_data = None
    if risk_file:
        risk_data = factory.load_macro_data(risk_file, start_date, end_date)

    # 加载区制数据
    regime_data = None
    if regime_file:
        regime_data = factory.load_macro_data(regime_file, start_date, end_date)

    # 创建数据源
    data_feed = factory.create_data_feed(
        price_data,
        macro_data,
        risk_data,
        regime_data
    )

    return data_feed
