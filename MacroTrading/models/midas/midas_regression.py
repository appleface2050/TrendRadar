"""
MIDAS（Mixed Data Sampling）混频回归模型

理论基础：
- 允许因变量和自变量具有不同的频率
- 例如：用月度数据预测季度GDP
- 使用多项式权重函数降低参数数量

应用场景：
- Nowcasting（实时预测）
- 使用高频数据预测低频目标

参考文献：
- Ghysels, E., Santa-Clara, P., & Valkanov, R. (2004). The MIDAS touch: Mixed data sampling regression models.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
import warnings

# 尝试导入MIDASpy
try:
    from MIDASpy import midas, midas_ml
    MIDASPY_AVAILABLE = True
except (ImportError, Exception) as e:
    MIDASPY_AVAILABLE = False
    print(f"警告：MIDASpy不可用（{type(e).__name__}），将使用简化实现")

from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings('ignore')


class BaseMIDAS:
    """
    MIDAS混频回归基础类

    核心思想：
    y_t = α + β * B(L^{1/m}; θ) * x_t + ε_t

    其中：
    - y_t: 低频目标变量（如季度GDP）
    - x_t: 高频预测变量（如月度指标）
    - B(L^{1/m}; θ): MIDAS多项式权重函数
    - m: 频率比（如月度到季度，m=3）
    """

    def __init__(
        self,
        freq_ratio: int = 3,  # 月度到季度
        poly_type: str = 'normalized_almon',
        poly_degree: int = 3
    ):
        """
        初始化MIDAS模型

        Parameters
        ----------
        freq_ratio : int
            频率比（高频/低频）
            - 3: 月度 → 季度
            - 12: 月度 → 年度
            - 4: 季度 → 年度
        poly_type : str
            多项式类型：
            - 'normalized_almon': Almon多项式
            - 'exponential_almon': 指数Almon
            - 'beta': Beta函数
        poly_degree : int
            多项式阶数
        """
        self.freq_ratio = freq_ratio
        self.poly_type = poly_type
        self.poly_degree = poly_degree

        self.model = None
        self.weights = None
        self.scaler = StandardScaler()

    def _almon_poly_weights(
        self,
        n_lags: int,
        theta: np.ndarray
    ) -> np.ndarray:
        """
        Almon多项式权重

        Parameters
        ----------
        n_lags : int
            滞后期数
        theta : np.ndarray
            多项式参数

        Returns
        -------
        weights : np.ndarray
            权重向量
        """
        # 归一化时间
        t = np.arange(n_lags) / (n_lags - 1)

        # 构造多项式基函数
        Phi = np.vstack([t**d for d in range(self.poly_degree + 1)]).T

        # 计算权重
        weights = Phi @ theta

        # 归一化权重（和为1）
        weights = weights / weights.sum()

        return weights

    def _beta_weights(
        self,
        n_lags: int,
        theta: np.ndarray
    ) -> np.ndarray:
        """
        Beta函数权重

        Parameters
        ----------
        n_lags : int
            滞后期数
        theta : np.ndarray
            Beta函数参数 [theta1, theta2, theta3]

        Returns
        -------
        weights : np.ndarray
            权重向量
        """
        theta1, theta2, theta3 = theta

        # 归一化时间
        t = np.arange(n_lags) / (n_lags - 1)

        # Beta函数权重
        weights = t**(theta1 - 1) * (1 - t)**(theta2 - 1)
        weights = theta3 * weights

        # 归一化
        weights = weights / (weights.sum() + 1e-10)

        return weights

    def _construct_midas_transform(
        self,
        high_freq_data: np.ndarray,
        weights: np.ndarray
    ) -> np.ndarray:
        """
        构造MIDAS变换后的低频变量

        Parameters
        ----------
        high_freq_data : np.ndarray
            高频数据 (T_high * freq_ratio,)
        weights : np.ndarray
            MIDAS权重

        Returns
        -------
        low_freq_transform : np.ndarray
            变换后的低频数据
        """
        n_low = len(high_freq_data) // self.freq_ratio

        # 转换为低频
        low_freq_transform = np.zeros(n_low)

        for i in range(n_low):
            # 提取对应的高频数据块
            start_idx = i * self.freq_ratio
            end_idx = (i + 1) * self.freq_ratio
            block = high_freq_data[start_idx:end_idx]

            # 应用MIDAS权重
            if len(block) == self.freq_ratio:
                # 反向权重（最近的观测值权重更大）
                low_freq_transform[i] = np.sum(block * weights[::-1])
            else:
                # 边界处理
                low_freq_transform[i] = np.nan

        return low_freq_transform

    def fit(
        self,
        y: pd.Series,
        X: pd.DataFrame,
        method: str = 'ols'
    ) -> 'BaseMIDAS':
        """
        拟合MIDAS模型

        Parameters
        ----------
        y : pd.Series
            低频目标变量（索引为日期）
        X : pd.DataFrame
            高频预测变量（索引为日期）
        method : str
            估计方法：'ols', 'ridge', 'midaspy'

        Returns
        -------
        self
        """
        # 数据对齐
        y_aligned, X_aligned = self._align_data(y, X)

        # 使用MIDASpy（如果可用）
        if method == 'midaspy' and MIDASPY_AVAILABLE:
            return self._fit_midaspy(y_aligned, X_aligned)

        # 简化实现：先转换频率，再回归
        return self._fit_simplified(y_aligned, X_aligned, method)

    def _align_data(
        self,
        y: pd.Series,
        X: pd.DataFrame
    ) -> Tuple[pd.Series, pd.DataFrame]:
        """
        对齐低频和高频数据

        Parameters
        ----------
        y : pd.Series
            低频目标变量
        X : pd.DataFrame
            高频预测变量

        Returns
        -------
        y_aligned : pd.Series
            对齐后的低频变量
        X_aligned : pd.DataFrame
            对齐后的高频变量
        """
        # 找出共同时间范围
        start_date = max(y.index.min(), X.index.min())
        end_date = min(y.index.max(), X.index.max())

        y_filtered = y[(y.index >= start_date) & (y.index <= end_date)]
        X_filtered = X[(X.index >= start_date) & (X.index <= end_date)]

        return y_filtered, X_filtered

    def _fit_simplified(
        self,
        y: pd.Series,
        X: pd.DataFrame,
        method: str = 'ols'
    ) -> 'BaseMIDAS':
        """
        简化实现：频率转换 + 回归

        Parameters
        ----------
        y : pd.Series
            低频目标变量
        X : pd.DataFrame
            高频预测变量
        method : str
            回归方法

        Returns
        -------
        self
        """
        # 对每个高频变量应用MIDAS变换
        X_transformed = pd.DataFrame(index=y.index)

        for col in X.columns:
            # 下采样到低频（使用均值或最后值）
            if self.freq_ratio == 3:  # 月度 → 季度
                X_transformed[col] = X[col].resample('Q').mean()
            elif self.freq_ratio == 12:  # 月度 → 年度
                X_transformed[col] = X[col].resample('Y').mean()
            elif self.freq_ratio == 4:  # 季度 → 年度
                X_transformed[col] = X[col].resample('Y').mean()

        # 对齐
        common_index = y.index.intersection(X_transformed.index)
        y_final = y.loc[common_index]
        X_final = X_transformed.loc[common_index]

        # 移除NaN
        X_final = X_final.dropna()

        # 对齐y和X的索引
        common_index_clean = y_final.index.intersection(X_final.index)
        y_final = y_final.loc[common_index_clean]
        X_final = X_final.loc[common_index_clean]

        # 检查是否有足够的数据
        if len(X_final) == 0 or len(y_final) == 0:
            raise ValueError("频率对齐后没有足够的数据点")

        # 转换为numpy数组
        X_array = X_final.values
        if X_array.ndim == 1:
            X_array = X_array.reshape(-1, 1)

        # 标准化
        X_scaled = self.scaler.fit_transform(X_array)

        # 拟合回归
        if method == 'ridge':
            self.model = Ridge(alpha=1.0)
        else:
            self.model = LinearRegression()

        self.model.fit(X_scaled, y_final)

        # 计算权重（系数）
        self.weights = self.model.coef_

        return self

    def _fit_midaspy(
        self,
        y: pd.Series,
        X: pd.DataFrame
    ) -> 'BaseMIDAS':
        """
        使用MIDASpy库拟合模型

        Parameters
        ----------
        y : pd.Series
            低频目标变量
        X : pd.DataFrame
            高频预测变量

        Returns
        -------
        self
        """
        try:
            # 使用MIDASpy
            midas_model = midas.ml(
                y=y.values,
                x=X.values,
                freq_x=self.freq_ratio,
                poly_type=self.poly_type
            )

            midas_model.fit()

            self.model = midas_model
            self.weights = midas_model.params

        except Exception as e:
            print(f"MIDASpy拟合失败：{e}")
            print("降级到简化实现...")
            return self._fit_simplified(y, X)

        return self

    def predict(
        self,
        X: pd.DataFrame
    ) -> np.ndarray:
        """
        预测

        Parameters
        ----------
        X : pd.DataFrame
            高频预测变量

        Returns
        -------
        predictions : np.ndarray
            预测值
        """
        if self.model is None:
            raise ValueError("模型尚未拟合")

        # 下采样
        if self.freq_ratio == 3:
            X_transformed = X.resample('Q').mean()
        elif self.freq_ratio == 12:
            X_transformed = X.resample('Y').mean()
        else:
            X_transformed = X.resample('Q').mean()

        # 移除NaN
        X_transformed = X_transformed.dropna()

        # 检查是否有数据
        if len(X_transformed) == 0:
            raise ValueError("预测数据为空")

        # 标准化
        X_scaled = self.scaler.transform(X_transformed)

        # 预测
        predictions = self.model.predict(X_scaled)

        return predictions


class MIDASRegressor:
    """
    MIDAS回归器的便捷封装

    支持多个预测变量的MIDAS回归
    """

    def __init__(
        self,
        target_freq: str = 'Q',  # 目标频率
        predictor_freq: str = 'M',  # 预测变量频率
        poly_type: str = 'normalized_almon',
        poly_degree: int = 3
    ):
        """
        参数
        ----
        target_freq : str
            目标频率（'Q'=季度, 'M'=月度, 'A'=年度）
        predictor_freq : str
            预测变量频率
        poly_type : str
            多项式类型
        poly_degree : int
            多项式阶数
        """
        self.target_freq = target_freq
        self.predictor_freq = predictor_freq
        self.poly_type = poly_type
        self.poly_degree = poly_degree

        # 计算频率比（更准确的方法）
        freq_pairs = {
            ('D', 'W'): 7,
            ('D', 'M'): 30,
            ('D', 'Q'): 90,
            ('D', 'A'): 365,
            ('W', 'M'): 4,
            ('W', 'Q'): 13,
            ('W', 'A'): 52,
            ('M', 'Q'): 3,
            ('M', 'A'): 12,
            ('Q', 'A'): 4,
        }

        key = (predictor_freq, target_freq)
        if key in freq_pairs:
            self.freq_ratio = freq_pairs[key]
        else:
            # 反向映射（高频到低频）
            reverse_key = (target_freq, predictor_freq)
            if reverse_key in freq_pairs:
                self.freq_ratio = 1  # 反向情况，暂设为1
            else:
                raise ValueError(f"不支持的频率组合: {predictor_freq} → {target_freq}")

        self.models = {}

    def fit(
        self,
        y: pd.Series,
        X: pd.DataFrame
    ) -> 'MIDASRegressor':
        """
        拟合MIDAS回归

        Parameters
        ----------
        y : pd.Series
            目标变量
        X : pd.DataFrame
            预测变量

        Returns
        -------
        self
        """
        # 对每个预测变量拟合单独的MIDAS模型
        for col in X.columns:
            model = BaseMIDAS(
                freq_ratio=self.freq_ratio,
                poly_type=self.poly_type,
                poly_degree=self.poly_degree
            )

            model.fit(y, X[[col]], method='ols')
            self.models[col] = model

        return self

    def predict(
        self,
        X: pd.DataFrame
    ) -> np.ndarray:
        """
        预测

        Parameters
        ----------
        X : pd.DataFrame
            预测变量

        Returns
        -------
        predictions : np.ndarray
            预测值（平均）
        """
        predictions = []

        for col, model in self.models.items():
            if col in X.columns:
                pred = model.predict(X[[col]])
                predictions.append(pred)

        # 平均预测
        if predictions:
            return np.mean(predictions, axis=0)
        else:
            raise ValueError("没有可用的预测变量")


def test_midas():
    """
    测试MIDAS模型
    """
    print("=" * 60)
    print("测试MIDAS混频回归模型")
    print("=" * 60)

    # 生成模拟数据
    np.random.seed(42)

    # 生成月度数据（高频）
    n_months = 120
    monthly_dates = pd.date_range('2010-01-01', periods=n_months, freq='M')

    # 3个月度指标
    monthly_data = pd.DataFrame({
        'indicator1': np.random.randn(n_months).cumsum(),
        'indicator2': np.random.randn(n_months).cumsum(),
        'indicator3': np.random.randn(n_months).cumsum()
    }, index=monthly_dates)

    # 生成季度GDP（低频）
    n_quarters = n_months // 3
    quarterly_dates = pd.date_range('2010-01-01', periods=n_quarters, freq='Q')

    # GDP与月度指标相关
    gdp = np.zeros(n_quarters)
    for i in range(n_quarters):
        # 季度GDP = 对应3个月指标的平均 + 随机噪声
        start_idx = i * 3
        end_idx = (i + 1) * 3
        gdp[i] = monthly_data['indicator1'].iloc[start_idx:end_idx].mean() * 0.5 + \
                 monthly_data['indicator2'].iloc[start_idx:end_idx].mean() * 0.3 + \
                 monthly_data['indicator3'].iloc[start_idx:end_idx].mean() * 0.2 + \
                 np.random.randn() * 0.1

    gdp_series = pd.Series(gdp, index=quarterly_dates)

    # 拟合MIDAS模型
    print("\n[1] 拟合MIDAS模型...")
    midas_model = MIDASRegressor(
        target_freq='Q',
        predictor_freq='M',
        poly_type='normalized_almon',
        poly_degree=3
    )

    midas_model.fit(gdp_series, monthly_data)

    # 预测
    print("\n[2] 预测...")
    predictions = midas_model.predict(monthly_data)

    print(f"预测值数量：{len(predictions)}")
    print(f"预测值（最后5个）：{predictions[-5:]}")

    # 评估
    print("\n[3] 评估预测性能...")
    from sklearn.metrics import mean_squared_error, r2_score

    # 对齐
    common_index = gdp_series.index.intersection(
        pd.date_range(predictions[0], periods=len(predictions), freq='Q')
    )
    y_true = gdp_series.loc[common_index]

    mse = mean_squared_error(y_true, predictions[:len(y_true)])
    r2 = r2_score(y_true, predictions[:len(y_true)])

    print(f"MSE: {mse:.4f}")
    print(f"R²: {r2:.4f}")

    print("\nMIDAS模型测试完成！")

    return midas_model


if __name__ == '__main__':
    # 运行测试
    midas_model = test_midas()
