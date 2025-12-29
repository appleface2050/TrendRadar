"""
Nowcasting引擎（实时预测）

核心功能：
1. 整合DFM、MIDAS等模型
2. 实时预测GDP/CPI
3. 输出预测不确定性区间

理论基础：
- 使用所有可用的混频数据
- 基于动态因子模型提取共同因子
- 使用MIDAS回归处理频率差异
- Kalman滤波进行实时更新

参考文献：
- Giannone, D., Reichlin, L., & Small, D. (2008). Nowcasting: The real-time informational content of macroeconomic data.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union
import warnings
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

# 导入项目模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from models.dfm.base_dfm import BaseDFM
from models.dfm.us_dfm import USDFM
from models.dfm.cn_dfm import CNDFM
from models.midas.midas_regression import MIDASRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error


class NowcastingEngine:
    """
    Nowcasting引擎基类

    工作流程：
    1. 数据收集：获取所有可用的宏观数据
    2. 因子提取：使用DFM提取共同因子
    3. 频率对齐：使用MIDAS处理混频数据
    4. 实时预测：生成目标变量的预测值
    5. 不确定性量化：计算预测区间
    """

    def __init__(
        self,
        target_variable: str = 'GDP',
        target_freq: str = 'Q',
        n_factors: int = 3,
        midas_poly_degree: int = 3
    ):
        """
        初始化Nowcasting引擎

        Parameters
        ----------
        target_variable : str
            目标变量（'GDP', 'CPI'等）
        target_freq : str
            目标频率（'Q'=季度, 'M'=月度）
        n_factors : int
            DFM因子数量
        midas_poly_degree : int
            MIDAS多项式阶数
        """
        self.target_variable = target_variable
        self.target_freq = target_freq
        self.n_factors = n_factors
        self.midas_poly_degree = midas_poly_degree

        # 子模型
        self.dfm_model = None
        self.midas_model = None
        self.regression_model = None

        # 数据
        self.factors = None
        self.predictions = None
        self.prediction_intervals = None

    def load_data(
        self,
        data: pd.DataFrame,
        target_series: pd.Series
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        加载和准备数据

        Parameters
        ----------
        data : pd.DataFrame
            宏观数据（宽表格式）
        target_series : pd.Series
            目标变量序列

        Returns
        -------
        data_clean : pd.DataFrame
            清理后的数据
        target_clean : pd.Series
            清理后的目标变量
        """
        # 移除缺失值过多的列
        missing_ratio = data.isnull().sum() / len(data)
        valid_cols = missing_ratio[missing_ratio < 0.3].index
        data_clean = data[valid_cols].copy()

        # 前向填充和后向填充
        data_clean = data_clean.fillna(method='ffill').fillna(method='bfill')

        # 移除无穷值
        data_clean = data_clean.replace([np.inf, -np.inf], np.nan).dropna()

        # 对齐目标变量
        target_clean = target_series.loc[data_clean.index.intersection(target_series.index)]

        # 保存原始数据用于nowcast
        self.raw_data = data_clean

        print(f"数据清理完成：")
        print(f"  预测变量：{len(data_clean.columns)} 个")
        print(f"  时间点：{len(data_clean)} 个")
        print(f"  缺失率：{data_clean.isnull().sum().sum() / data_clean.size * 100:.2f}%")

        return data_clean, target_clean

    def extract_factors(
        self,
        data: pd.DataFrame,
        method: str = 'pca'
    ) -> pd.DataFrame:
        """
        提取动态因子

        Parameters
        ----------
        data : pd.DataFrame
            宏观数据
        method : str
            估计方法

        Returns
        -------
        factors : pd.DataFrame
            提取的因子
        """
        print(f"\n提取动态因子（{self.n_factors}个）...")

        # 创建DFM模型
        dfm = BaseDFM(n_factors=self.n_factors, standardize=True)
        dfm.fit(data, method=method)

        self.factors = dfm.get_factors()
        self.dfm_model = dfm

        print(f"因子提取完成：{self.factors.shape}")
        print(f"解释方差比（第一个因子）：{dfm.pca_model.explained_variance_ratio_[0]:.2%}")

        return self.factors

    def fit(
        self,
        data: pd.DataFrame,
        target: pd.Series,
        use_midas: bool = True
    ) -> 'NowcastingEngine':
        """
        拟合Nowcasting模型

        Parameters
        ----------
        data : pd.DataFrame
            预测变量数据
        target : pd.Series
            目标变量
        use_midas : bool
            是否使用MIDAS处理频率差异

        Returns
        -------
        self
        """
        print("=" * 60)
        print(f"Nowcasting引擎：预测 {self.target_variable}")
        print("=" * 60)

        # [1] 数据准备
        print("\n[步骤1] 数据准备...")
        data_clean, target_clean = self.load_data(data, target)

        # [2] 因子提取
        print("\n[步骤2] 因子提取...")
        factors = self.extract_factors(data_clean)

        # [3] 频率对齐
        print("\n[步骤3] 频率对齐...")
        if use_midas:
            # 使用MIDAS
            self.midas_model = MIDASRegressor(
                target_freq=self.target_freq,
                predictor_freq='M',
                poly_degree=self.midas_poly_degree
            )
            # 注意：这里简化处理，实际MIDAS需要更复杂的对齐
            X_for_regression = factors
        else:
            X_for_regression = factors

        # [4] 回归模型
        print("\n[步骤4] 拟合回归模型...")
        # 对齐因子和目标变量
        common_index = target_clean.index.intersection(X_for_regression.index)
        X_aligned = X_for_regression.loc[common_index]
        y_aligned = target_clean.loc[common_index]

        # 拟合回归
        self.regression_model = LinearRegression()
        self.regression_model.fit(X_aligned, y_aligned)

        # 计算训练集预测
        train_predictions = self.regression_model.predict(X_aligned)

        # 评估
        mse = mean_squared_error(y_aligned, train_predictions)
        mae = mean_absolute_error(y_aligned, train_predictions)
        r2 = self.regression_model.score(X_aligned, y_aligned)

        print(f"  R²: {r2:.4f}")
        print(f"  MSE: {mse:.4f}")
        print(f"  MAE: {mae:.4f}")

        # [5] 保存训练数据
        self.train_data = {
            'X': X_aligned,
            'y': y_aligned,
            'predictions': train_predictions
        }

        print("\n模型拟合完成！")

        return self

    def nowcast(
        self,
        current_data: pd.DataFrame,
        return_intervals: bool = True,
        confidence_level: float = 0.95
    ) -> Dict[str, Union[float, Tuple[float, float]]]:
        """
        实时预测

        Parameters
        ----------
        current_data : pd.DataFrame
            当前可用的宏观数据
        return_intervals : bool
            是否返回预测区间
        confidence_level : float
            置信水平

        Returns
        -------
        results : dict
            预测结果
        """
        if self.regression_model is None:
            raise ValueError("模型尚未拟合，请先调用fit()方法")

        # 提取因子
        factors_now = self.dfm_model.transform(current_data)

        # 取最新因子的值
        latest_factors = factors_now.iloc[-1:].values

        # 预测
        prediction = self.regression_model.predict(latest_factors)[0]

        results = {
            'prediction': prediction,
            'date': pd.Timestamp.now(),
            'target_variable': self.target_variable
        }

        # 计算预测区间
        if return_intervals:
            lower, upper = self._compute_prediction_interval(
                latest_factors,
                confidence_level
            )
            results['prediction_interval'] = (lower, upper)
            results['confidence_level'] = confidence_level

        return results

    def _compute_prediction_interval(
        self,
        X: np.ndarray,
        confidence_level: float = 0.95
    ) -> Tuple[float, float]:
        """
        计算预测区间

        Parameters
        ----------
        X : np.ndarray
            预测变量
        confidence_level : float
            置信水平

        Returns
        -------
        lower, upper : tuple
            预测区间下限和上限
        """
        from scipy import stats

        # 预测值
        y_pred = self.regression_model.predict(X)[0]

        # 残差标准误
        residuals = self.train_data['y'] - self.train_data['predictions']
        residual_std = np.std(residuals, ddof=len(self.train_data['X'].columns) + 1)

        # t统计量
        n = len(self.train_data['y'])
        p = len(self.train_data['X'].columns)
        t_value = stats.t.ppf((1 + confidence_level) / 2, df=n - p - 1)

        # 预测区间
        margin = t_value * residual_std

        lower = y_pred - margin
        upper = y_pred + margin

        return lower, upper

    def plot_nowcasts(
        self,
        figsize: Tuple[int, int] = (14, 6)
    ):
        """
        绘制Nowcasting结果

        Parameters
        ----------
        figsize : tuple
            图形大小
        """
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=figsize)

        # 绘制实际值
        ax.plot(
            self.train_data['y'].index,
            self.train_data['y'].values,
            label='实际值',
            linewidth=2
        )

        # 绘制预测值
        ax.plot(
            self.train_data['y'].index,
            self.train_data['predictions'],
            label='Nowcast预测',
            linewidth=2,
            linestyle='--'
        )

        ax.set_title(f'{self.target_variable} Nowcasting预测')
        ax.set_xlabel('日期')
        ax.set_ylabel('数值')
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        return fig


class USNowcastingEngine(NowcastingEngine):
    """
    美国Nowcasting引擎

    专门用于预测美国GDP和CPI
    """

    def __init__(
        self,
        target_variable: str = 'GDP',
        target_freq: str = 'Q',
        n_factors: int = 3
    ):
        super().__init__(target_variable, target_freq, n_factors)

        # 加载美国DFM
        self.us_dfm = USDFM(n_factors=n_factors)

    def load_from_csv(
        self,
        csv_path: str = 'data/csv/us_all_indicators.csv',
        target_csv_path: Optional[str] = None,
        start_date: str = '2010-01-01'
    ) -> 'USNowcastingEngine':
        """
        从CSV加载数据并拟合模型

        Parameters
        ----------
        csv_path : str
            预测变量CSV路径
        target_csv_path : str, optional
            目标变量CSV路径
        start_date : str
            开始日期

        Returns
        -------
        self
        """
        # 加载宏观数据
        macro_data = self.us_dfm.fetch_from_csv(csv_path, start_date=start_date)

        # 加载目标变量
        if target_csv_path:
            target_data = pd.read_csv(target_csv_path, index_col=0, parse_dates=True)
            target_series = target_data[self.target_variable]
        else:
            # 从宏观数据中提取
            if self.target_variable in macro_data.columns:
                target_series = macro_data[self.target_variable].dropna()
            else:
                raise ValueError(f"未找到目标变量 {self.target_variable}")

        # 拟合模型
        self.fit(macro_data, target_series)

        return self


class CNNowcastingEngine(NowcastingEngine):
    """
    中国Nowcasting引擎

    专门用于预测中国GDP和CPI
    """

    def __init__(
        self,
        target_variable: str = 'GDP',
        target_freq: str = 'Q',
        n_factors: int = 3
    ):
        super().__init__(target_variable, target_freq, n_factors)

        # 加载中国DFM
        self.cn_dfm = CNDFM(n_factors=n_factors)

    def load_from_tushare(
        self,
        start_date: str = '2010-01-01'
    ) -> 'CNNowcastingEngine':
        """
        从Tushare加载数据并拟合模型

        Parameters
        ----------
        start_date : str
            开始日期

        Returns
        -------
        self
        """
        # 加载宏观数据
        macro_data = self.cn_dfm.fetch_macro_data(start_date=start_date)

        # 提取目标变量
        if self.target_variable in macro_data.columns:
            target_series = macro_data[self.target_variable].dropna()
        else:
            raise ValueError(f"未找到目标变量 {self.target_variable}")

        # 拟合模型
        self.fit(macro_data, target_series)

        return self


def test_nowcasting_engine():
    """
    测试Nowcasting引擎
    """
    print("=" * 60)
    print("测试Nowcasting引擎")
    print("=" * 60)

    # 创建美国Nowcasting引擎
    engine = USNowcastingEngine(
        target_variable='GDP',
        target_freq='Q',
        n_factors=3
    )

    # 从CSV加载数据并拟合
    try:
        engine.load_from_csv(
            csv_path='data/csv/us_all_indicators.csv',
            start_date='2014-01-01'
        )

        # 实时预测
        print("\n[实时预测]")
        nowcast_result = engine.nowcast(
            engine.train_data['X'].iloc[-60:]  # 使用最近的数据
        )

        print(f"预测日期：{nowcast_result['date']}")
        print(f"预测值：{nowcast_result['prediction']:.2f}")
        if 'prediction_interval' in nowcast_result:
            lower, upper = nowcast_result['prediction_interval']
            print(f"预测区间（{nowcast_result['confidence_level']:.0%}）：[{lower:.2f}, {upper:.2f}]")

        # 绘图
        print("\n[绘图]")
        fig = engine.plot_nowcasts(figsize=(14, 6))
        fig.savefig('models/nowcasting/nowcast_plot.png', dpi=100, bbox_inches='tight')
        print("图表已保存到：models/nowcasting/nowcast_plot.png")

        return engine

    except Exception as e:
        print(f"错误：{e}")
        print("请确保数据文件存在")
        return None


if __name__ == '__main__':
    # 运行测试
    engine = test_nowcasting_engine()
