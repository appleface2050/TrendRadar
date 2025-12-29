"""
宏观风险指标

计算各类宏观风险指标，包括：
1. 宏观状态风险：衰退概率、过热概率、滞胀概率
2. 通胀风险：CPI超预期概率、通胀波动率
3. 增长风险：GDP增速下行风险
4. 流动性风险：M1-M2剪刀差
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


class MacroRiskIndicators:
    """宏观风险指标计算器"""

    def __init__(self):
        """初始化"""
        self.indicators = {}
        self.regime_model = None

    def load_regime_model(self, regime_model):
        """
        加载区制转移模型

        Parameters:
        -----------
        regime_model : object
            已训练的区制转移模型（如USMarketRegimeModel或CNPolicyRegimeModel）
        """
        self.regime_model = regime_model
        print("✓ 区制转移模型已加载")

    def calculate_recession_probability(self, regime_probs=None):
        """
        计算衰退概率

        Parameters:
        -----------
        regime_probs : DataFrame, optional
            区制概率数据（如果为None，从regime_model获取）

        Returns:
        --------
        Series
            衰退概率
        """
        if regime_probs is None and self.regime_model is not None:
            # 从区制模型获取概率
            if hasattr(self.regime_model, 'regime_probs'):
                regime_probs = self.regime_model.regime_probs

        if regime_probs is None:
            print("Warning: 无法获取区制概率")
            return None

        # 假设衰退区制是"Regime_3"或"Regime_4"
        # 需要根据实际模型调整
        if 'Regime_3' in regime_probs.columns:
            recession_prob = regime_probs['Regime_3']
        elif 'Regime_4' in regime_probs.columns:
            recession_prob = regime_probs['Regime_4']
        else:
            # 使用最后一列（通常是衰退区制）
            recession_prob = regime_probs.iloc[:, -1]

        return recession_prob

    def calculate_overheating_probability(self, regime_probs=None):
        """
        计算过热概率

        Parameters:
        -----------
        regime_probs : DataFrame, optional
            区制概率数据

        Returns:
        --------
        Series
            过热概率
        """
        if regime_probs is None and self.regime_model is not None:
            if hasattr(self.regime_model, 'regime_probs'):
                regime_probs = self.regime_model.regime_probs

        if regime_probs is None:
            print("Warning: 无法获取区制概率")
            return None

        # 假设过热区制是"Regime_2"
        if 'Regime_2' in regime_probs.columns:
            overheating_prob = regime_probs['Regime_2']
        else:
            overheating_prob = regime_probs.iloc[:, 1]

        return overheating_prob

    def calculate_stagflation_probability(self, regime_probs=None):
        """
        计算滞胀概率

        Parameters:
        -----------
        regime_probs : DataFrame, optional
            区制概率数据

        Returns:
        --------
        Series
            滞胀概率
        """
        if regime_probs is None and self.regime_model is not None:
            if hasattr(self.regime_model, 'regime_probs'):
                regime_probs = self.regime_model.regime_probs

        if regime_probs is None:
            print("Warning: 无法获取区制概率")
            return None

        # 滞胀区制
        if 'Regime_3' in regime_probs.columns:
            # 根据模型，滞胀可能是Regime_3或Regime_4
            if 'Regime_4' in regime_probs.columns:
                # 使用通胀较高的区制作为滞胀
                stagflation_prob = regime_probs[['Regime_3', 'Regime_4']].max(axis=1)
            else:
                stagflation_prob = regime_probs['Regime_3']
        else:
            stagflation_prob = regime_probs.iloc[:, -1]

        return stagflation_prob

    def calculate_cpi_surprise_probability(self, cpi_actual, cpi_expected=None, window=20):
        """
        计算CPI超预期概率

        Parameters:
        -----------
        cpi_actual : Series
            实际CPI数据
        cpi_expected : Series, optional
            预期CPI数据（如果为None，使用历史均值作为预期）
        window : int
            用于计算预期的滚动窗口

        Returns:
        --------
        Series
            CPI超预期概率
        """
        if cpi_expected is None:
            # 使用滚动均值作为预期
            cpi_expected = cpi_actual.rolling(window=window).mean()

        # 计算超预期（实际 - 预期）
        surprise = cpi_actual - cpi_expected

        # 计算超预期的标准差
        surprise_std = surprise.rolling(window=window).std()

        # 计算Z-score
        surprise_zscore = surprise / (surprise_std + 1e-8)

        # 转换为概率（使用正态分布的累积分布函数）
        from scipy import stats
        surprise_prob = 1 - stats.norm.cdf(surprise_zscore)

        return surprise_prob

    def calculate_inflation_volatility(self, cpi_data, window=12):
        """
        计算通胀波动率

        Parameters:
        -----------
        cpi_data : Series
            CPI数据（同比或环比）
        window : int
            滚动窗口

        Returns:
        --------
        Series
            通胀波动率
        """
        # 计算CPI变化率
        if cpi_data.max() > 1:  # 如果是指数形式
            cpi_change = cpi_data.pct_change()
        else:  # 如果已经是变化率
            cpi_change = cpi_data.diff()

        # 滚动标准差
        inflation_vol = cpi_change.rolling(window=window).std()

        return inflation_vol

    def calculate_inflation_trend(self, cpi_data, window=12):
        """
        计算通胀趋势（斜率）

        Parameters:
        -----------
        cpi_data : Series
            CPI数据
        window : int
            滚动窗口

        Returns:
        --------
        Series
            通胀趋势
        """
        # 对数CPI（用于计算增长率）
        log_cpi = np.log(cpi_data)

        # 滚动线性回归斜率
        trend = pd.Series(index=cpi_data.index, dtype=float)

        for i in range(window, len(cpi_data)):
            y = log_cpi.iloc[i-window:i]
            x = np.arange(window)

            # 线性回归
            coef = np.polyfit(x, y, 1)
            trend.iloc[i] = coef[0]  # 斜率

        return trend

    def calculate_gdp_downside_risk(self, gdp_data, window=4):
        """
        计算GDP增速下行风险

        Parameters:
        -----------
        gdp_data : Series
            GDP增速数据
        window : int
            滚动窗口

        Returns:
        --------
        Series
            GDP下行风险指标
        """
        # 计算滚动均值
        gdp_mean = gdp_data.rolling(window=window).mean()

        # 计算下行风险（当前值低于均值的程度）
        downside_risk = np.maximum(0, gdp_mean - gdp_data) / (gdp_mean + 1e-8)

        return downside_risk

    def calculate_m1_m2_scissors(self, m1_data, m2_data):
        """
        计算M1-M2剪刀差

        Parameters:
        -----------
        m1_data : Series
            M1增速数据
        m2_data : Series
            M2增速数据

        Returns:
        --------
        Series
            M1-M2剪刀差
        """
        scissors = m1_data - m2_data

        return scissors

    def calculate_credit_impulse(self, new_loans, gdp_data, window=4):
        """
        计算信贷脉冲（新增信贷/GDP的变化）

        Parameters:
        -----------
        new_loans : Series
            新增贷款数据
        gdp_data : Series
            GDP数据
        window : int
            滚动窗口

        Returns:
        --------
        Series
            信贷脉冲
        """
        # 计算信贷/GDP比率
        credit_to_gdp = new_loans / gdp_data

        # 计算信贷脉冲（信贷/GDP的变化）
        credit_impulse = credit_to_gdp.diff()

        return credit_impulse

    def calculate_all_indicators(self, data_dict):
        """
        计算所有宏观风险指标

        Parameters:
        -----------
        data_dict : dict
            包含所有宏观数据的字典

        Returns:
        --------
        DataFrame
            所有宏观风险指标
        """
        print("开始计算宏观风险指标...")
        print("=" * 80)

        indicators = pd.DataFrame()

        # 1. 宏观状态风险（从区制模型获取）
        if self.regime_model is not None:
            recession_prob = self.calculate_recession_probability()
            if recession_prob is not None:
                indicators['recession_prob'] = recession_prob
                print("✓ 衰退概率")

            overheating_prob = self.calculate_overheating_probability()
            if overheating_prob is not None:
                indicators['overheating_prob'] = overheating_prob
                print("✓ 过热概率")

            stagflation_prob = self.calculate_stagflation_probability()
            if stagflation_prob is not None:
                indicators['stagflation_prob'] = stagflation_prob
                print("✓ 滞胀概率")

        # 2. 通胀风险
        if 'cpi' in data_dict and data_dict['cpi'] is not None:
            cpi = data_dict['cpi']

            if isinstance(cpi, pd.DataFrame):
                cpi_values = cpi.iloc[:, 0]
            else:
                cpi_values = cpi

            # CPI超预期概率
            cpi_surprise = self.calculate_cpi_surprise_probability(cpi_values)
            indicators['cpi_surprise_prob'] = cpi_surprise
            print("✓ CPI超预期概率")

            # 通胀波动率
            inflation_vol = self.calculate_inflation_volatility(cpi_values)
            indicators['inflation_volatility'] = inflation_vol
            print("✓ 通胀波动率")

            # 通胀趋势
            inflation_trend = self.calculate_inflation_trend(cpi_values)
            indicators['inflation_trend'] = inflation_trend
            print("✓ 通胀趋势")

        # 3. 增长风险
        if 'gdp' in data_dict and data_dict['gdp'] is not None:
            gdp = data_dict['gdp']

            if isinstance(gdp, pd.DataFrame):
                gdp_values = gdp.iloc[:, 0]
            else:
                gdp_values = gdp

            # GDP下行风险
            gdp_risk = self.calculate_gdp_downside_risk(gdp_values)
            indicators['gdp_downside_risk'] = gdp_risk
            print("✓ GDP下行风险")

        # 4. 流动性风险
        if 'm1' in data_dict and 'm2' in data_dict:
            m1 = data_dict['m1']
            m2 = data_dict['m2']

            if isinstance(m1, pd.DataFrame):
                m1 = m1.iloc[:, 0]
            if isinstance(m2, pd.DataFrame):
                m2 = m2.iloc[:, 0]

            # M1-M2剪刀差
            scissors = self.calculate_m1_m2_scissors(m1, m2)
            indicators['m1_m2_scissors'] = scissors
            print("✓ M1-M2剪刀差")

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
                    normalized[col] = 50

        elif method == 'zscore':
            # Z-score标准化后转换到0-100
            for col in normalized.columns:
                mean_val = normalized[col].mean()
                std_val = normalized[col].std()

                if std_val > 1e-8:
                    zscore = (normalized[col] - mean_val) / std_val
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

    def export_to_csv(self, output_path='data/derived/indicators/macro_risk_indicators.csv'):
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
    print("宏观风险指标模块已创建")
    print("使用示例：")

    print("""
    from models.risk.macro_risk_indicators import MacroRiskIndicators

    # 初始化
    mri = MacroRiskIndicators()

    # 加载区制模型（可选）
    mri.load_regime_model(regime_model)

    # 计算所有指标
    indicators = mri.calculate_all_indicators(data_dict)

    # 标准化
    normalized = mri.normalize_indicators(method='minmax')

    # 获取摘要
    summary = mri.get_indicator_summary()
    print(summary)

    # 导出
    mri.export_to_csv()
    """)
