"""
市场风险指标

计算各类市场风险指标，包括：
1. 市场情绪指标：波动率偏度、VIX、新高新低比
2. 流动性压力指标：利差、TED spread
3. 杠杆水平：融资交易占比
4. 外资行为：北向资金Z-score、资金流波动率
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class MarketRiskIndicators:
    """市场风险指标计算器"""

    def __init__(self):
        """初始化"""
        self.indicators = {}

    def calculate_volatility_skew(self, price_data, window=20):
        """
        计算波动率偏度（基于收益率）

        Parameters:
        -----------
        price_data : Series or DataFrame
            价格数据
        window : int
            滚动窗口

        Returns:
        --------
        Series
            波动率偏度
        """
        if isinstance(price_data, pd.DataFrame):
            prices = price_data.iloc[:, 0]  # 使用第一列
        else:
            prices = price_data

        # 计算收益率
        returns = prices.pct_change().dropna()

        # 滚动计算偏度
        skew = returns.rolling(window=window).skew()

        return skew

    def calculate_vix_ma(self, vix_data, window_short=5, window_long=20):
        """
        计算VIX移动平均比率

        Parameters:
        -----------
        vix_data : Series
            VIX数据
        window_short : int
            短期窗口
        window_long : int
            长期窗口

        Returns:
        --------
        Series
            VIX MA比率
        """
        ma_short = vix_data.rolling(window=window_short).mean()
        ma_long = vix_data.rolling(window=window_long).mean()

        vix_ma_ratio = ma_short / ma_long

        return vix_ma_ratio

    def calculate_new_high_low_ratio(self, high_data, low_data, window=20):
        """
        计算新高/新低比

        Parameters:
        -----------
        high_data : Series
            最高价数据
        low_data : Series
            最低价数据
        window : int
            滚动窗口

        Returns:
        --------
        Series
            新高新低比
        """
        # 计算滚动最高/最低
        rolling_max = high_data.rolling(window=window).max()
        rolling_min = low_data.rolling(window=window).min()

        # 创新高/新低
        is_new_high = high_data == rolling_max
        is_new_low = low_data == rolling_min

        # 计算比率
        new_high_count = is_new_high.rolling(window=window).sum()
        new_low_count = is_new_low.rolling(window=window).sum()

        ratio = new_high_count / (new_low_count + 1e-8)  # 避免除零

        return ratio

    def calculate_liquidity_spread(self, rate_short_term, rate_long_term):
        """
        计算流动性利差（长期利率 - 短期利率）

        Parameters:
        -----------
        rate_short_term : Series
            短期利率
        rate_long_term : Series
            长期利率

        Returns:
        --------
        Series
            流动性利差
        """
        spread = rate_long_term - rate_short_term

        return spread

    def calculate_ted_spread(self, t_bill_rate, libor_rate):
        """
        计算TED spread（3个月期国债利率 - 3个月期LIBOR）

        Parameters:
        -----------
        t_bill_rate : Series
            国债利率
        libor_rate : Series
            LIBOR利率

        Returns:
        --------
        Series
            TED spread
        """
        ted = libor_rate - t_bill_rate

        return ted

    def calculate_credit_spread(self, corporate_bond_yield, treasury_yield):
        """
        计算信用利差（公司债收益率 - 国债收益率）

        Parameters:
        -----------
        corporate_bond_yield : Series
            公司债收益率
        treasury_yield : Series
            国债收益率

        Returns:
        --------
        Series
            信用利差
        """
        spread = corporate_bond_yield - treasury_yield

        return spread

    def calculate_margin_debt_ratio(self, margin_debt, market_cap):
        """
        计算融资交易占比

        Parameters:
        -----------
        margin_debt : Series
            融资余额
        market_cap : Series
            市值

        Returns:
        --------
        Series
            融资交易占比
        """
        ratio = margin_debt / (market_cap + 1e-8)

        return ratio

    def calculate_northbound_zscore(self, northbound_flow, window=60):
        """
        计算北向资金Z-score

        Parameters:
        -----------
        northbound_flow : Series
            北向资金流
        window : int
            滚动窗口

        Returns:
        --------
        Series
            Z-score
        """
        # 滚动计算均值和标准差
        rolling_mean = northbound_flow.rolling(window=window).mean()
        rolling_std = northbound_flow.rolling(window=window).std()

        # 计算Z-score
        zscore = (northbound_flow - rolling_mean) / (rolling_std + 1e-8)

        return zscore

    def calculate_flow_volatility(self, flow_data, window=20):
        """
        计算资金流波动率

        Parameters:
        -----------
        flow_data : Series
            资金流数据
        window : int
            滚动窗口

        Returns:
        --------
        Series
            资金流波动率
        """
        volatility = flow_data.rolling(window=window).std()

        return volatility

    def calculate_all_indicators(self, data_dict):
        """
        计算所有市场风险指标

        Parameters:
        -----------
        data_dict : dict
            包含所有市场数据的字典

        Returns:
        --------
        DataFrame
            所有市场风险指标
        """
        print("开始计算市场风险指标...")
        print("=" * 80)

        indicators = pd.DataFrame()

        # 1. VIX相关指标
        if 'vix' in data_dict and data_dict['vix'] is not None:
            vix = data_dict['vix']['vix'] if isinstance(data_dict['vix'], pd.DataFrame) else data_dict['vix']

            # VIX MA比率
            indicators['vix_ma_ratio'] = self.calculate_vix_ma(vix)
            print("✓ VIX MA比率")

        # 2. 北向资金相关指标
        if 'northbound_flow' in data_dict and data_dict['northbound_flow'] is not None:
            flow = data_dict['northbound_flow']

            if 'net_flow_north' in flow.columns:
                north_flow = flow.set_index('trade_date')['net_flow_north']

                # Z-score
                indicators['northbound_zscore'] = self.calculate_northbound_zscore(north_flow)
                print("✓ 北向资金Z-score")

                # 波动率
                indicators['flow_volatility'] = self.calculate_flow_volatility(north_flow)
                print("✓ 资金流波动率")

        # 3. 利率相关指标
        if 'rate_diff' in data_dict and data_dict['rate_diff'] is not None:
            rate_diff = data_dict['rate_diff']['rate_diff']
            indicators['rate_diff'] = rate_diff
            print("✓ 中美利差")

        # 4. AH溢价
        if 'ah_premium' in data_dict and data_dict['ah_premium'] is not None:
            ah_premium = data_dict['ah_premium']['ah_premium']
            indicators['ah_premium'] = ah_premium

            # AH溢价Z-score
            ah_mean = ah_premium.rolling(window=60).mean()
            ah_std = ah_premium.rolling(window=60).std()
            indicators['ah_premium_zscore'] = (ah_premium - ah_mean) / (ah_std + 1e-8)
            print("✓ AH溢价Z-score")

        # 5. 美元指数
        if 'dxy' in data_dict and data_dict['dxy'] is not None:
            dxy = data_dict['dxy']['dxy']
            indicators['dxy'] = dxy

            # 美元指数变化率
            indicators['dxy_change'] = dxy.pct_change()
            print("✓ 美元指数变化率")

        # 移除缺失值
        indicators = indicators.dropna()

        print(f"\n✓ 计算完成，共{len(indicators.columns)}个指标，{len(indicators)}个观测值")
        print("=" * 80)

        self.indicators = indicators

        return indicators

    def normalize_indicators(self, method='minmax'):
        """
        标准化指标（0-100）

        Parameters:
        -----------
        method : str
            标准化方法：'minmax' 或 'zscore'

        Returns:
        --------
        DataFrame
            标准化后的指标
        """
        if len(self.indicators) == 0:
            print("Error: 没有指标数据")
            return None

        normalized = self.indicators.copy()

        if method == 'minmax':
            # Min-Max标准化到0-100
            for col in normalized.columns:
                min_val = normalized[col].min()
                max_val = normalized[col].max()

                if max_val - min_val > 1e-8:
                    normalized[col] = 100 * (normalized[col] - min_val) / (max_val - min_val)
                else:
                    normalized[col] = 50  # 如果没有变化，设为中间值

        elif method == 'zscore':
            # Z-score标准化后转换到0-100
            for col in normalized.columns:
                mean_val = normalized[col].mean()
                std_val = normalized[col].std()

                if std_val > 1e-8:
                    zscore = (normalized[col] - mean_val) / std_val
                    # 将Z-score转换到0-100（假设99.7%的数据在±3σ范围内）
                    normalized[col] = 50 + (zscore / 3) * 50
                    normalized[col] = np.clip(normalized[col], 0, 100)
                else:
                    normalized[col] = 50

        return normalized

    def get_indicator_summary(self):
        """
        获取指标摘要统计

        Returns:
        --------
        DataFrame
            指标摘要
        """
        if len(self.indicators) == 0:
            print("Error: 没有指标数据")
            return None

        summary = pd.DataFrame()

        for col in self.indicators.columns:
            summary.loc[col, '均值'] = self.indicators[col].mean()
            summary.loc[col, '标准差'] = self.indicators[col].std()
            summary.loc[col, '最小值'] = self.indicators[col].min()
            summary.loc[col, '最大值'] = self.indicators[col].max()
            summary.loc[col, '最新值'] = self.indicators[col].iloc[-1]

        return summary

    def get_high_risk_indicators(self, threshold=70, normalized=True):
        """
        获取高风险指标（超过阈值）

        Parameters:
        -----------
        threshold : float
            风险阈值（0-100）
        normalized : bool
            是否使用标准化后的指标

        Returns:
        --------
        list
            高风险指标列表
        """
        if normalized:
            data = self.normalize_indicators()
        else:
            data = self.indicators

        if data is None:
            return []

        # 获取最新值
        latest = data.iloc[-1]

        # 筛选高风险指标
        high_risk = latest[latest > threshold].index.tolist()

        return high_risk

    def export_to_csv(self, output_path='data/derived/indicators/market_risk_indicators.csv'):
        """
        导出指标到CSV

        Parameters:
        -----------
        output_path : str
            输出文件路径
        """
        if len(self.indicators) == 0:
            print("Error: 没有指标数据")
            return

        self.indicators.to_csv(output_path, encoding='utf-8-sig')
        print(f"✓ 指标已导出到：{output_path}")


# 测试代码
if __name__ == "__main__":
    print("市场风险指标模块已创建")
    print("使用示例：")

    print("""
    from models.risk.market_risk_indicators import MarketRiskIndicators

    # 初始化
    mri = MarketRiskIndicators()

    # 计算所有指标
    indicators = mri.calculate_all_indicators(data_dict)

    # 标准化
    normalized = mri.normalize_indicators(method='minmax')

    # 获取摘要
    summary = mri.get_indicator_summary()
    print(summary)

    # 获取高风险指标
    high_risk = mri.get_high_risk_indicators(threshold=70)
    print(f"高风险指标：{high_risk}")

    # 导出
    mri.export_to_csv()
    """)
