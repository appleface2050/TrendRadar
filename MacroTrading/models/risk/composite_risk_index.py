"""
复合风险预警指数

使用机器学习（XGBoost/LightGBM）动态赋权，综合市场和宏观风险指标，
预测未来5日/20日市场回撤，生成0-100的综合风险指数。

功能：
1. 整合市场风险指标和宏观风险指标
2. XGBoost动态赋权
3. 预测未来回撤（5日/20日）
4. 输出综合风险指数（0-100）
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("Warning: XGBoost not installed")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("Warning: LightGBM not installed")

try:
    from sklearn.model_selection import train_test_split, TimeSeriesSplit
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not installed")


class CompositeRiskIndex:
    """复合风险预警指数"""

    def __init__(self, model_type='xgboost', forecast_horizon=5):
        """
        初始化复合风险预警指数

        Parameters:
        -----------
        model_type : str
            模型类型：'xgboost', 'lightgbm', 'ensemble'
        forecast_horizon : int
            预测天数：5（短期）或20（中期）
        """
        self.model_type = model_type
        self.forecast_horizon = forecast_horizon
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []

        # 初始化模型
        if model_type == 'xgboost' and XGBOOST_AVAILABLE:
            self.model = xgb.XGBRegressor(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.01,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1
            )
        elif model_type == 'lightgbm' and LIGHTGBM_AVAILABLE:
            self.model = lgb.LGBMRegressor(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.01,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                n_jobs=-1,
                verbose=-1
            )

    def prepare_target(self, price_data, horizon=None):
        """
        准备目标变量（未来回撤）

        Parameters:
        -----------
        price_data : Series
            价格数据
        horizon : int, optional
            预测天数（默认使用forecast_horizon）

        Returns:
        --------
        Series
            未来回撤（百分比）
        """
        if horizon is None:
            horizon = self.forecast_horizon

        # 计算未来最高价
        future_max = price_data.rolling(window=horizon).max().shift(-horizon)

        # 计算回撤：(当前价 - 未来最高价) / 当前价
        drawdown = (price_data - future_max) / price_data

        # 转换为百分比
        drawdown_pct = drawdown * 100

        return drawdown_pct

    def create_lag_features(self, df, lags=5):
        """
        创建滞后特征

        Parameters:
        -----------
        df : DataFrame
            特征数据
        lags : int
            滞后阶数

        Returns:
        --------
        DataFrame
            包含滞后特征的数据
        """
        data = df.copy()

        # 为每列创建滞后特征
        for col in data.columns:
            for lag in range(1, lags + 1):
                data[f'{col}_lag{lag}'] = data[col].shift(lag)

        return data

    def create_rolling_features(self, df, windows=[5, 10, 20]):
        """
        创建滚动窗口特征

        Parameters:
        -----------
        df : DataFrame
            特征数据
        windows : list
            窗口大小列表

        Returns:
        --------
        DataFrame
            包含滚动特征的数据
        """
        data = df.copy()

        # 为每列创建滚动统计量
        for col in data.columns:
            for window in windows:
                # 滚动均值
                data[f'{col}_mean_{window}'] = data[col].rolling(window=window).mean()
                # 滚动标准差
                data[f'{col}_std_{window}'] = data[col].rolling(window=window).std()
                # 变化率
                data[f'{col}_pct_{window}'] = data[col].pct_change(window)

        return data

    def prepare_features(self, market_indicators, macro_indicators):
        """
        准备特征变量

        Parameters:
        -----------
        market_indicators : DataFrame
            市场风险指标
        macro_indicators : DataFrame
            宏观风险指标

        Returns:
        --------
        DataFrame
            特征矩阵
        """
        print("准备特征变量...")

        # 合并市场和宏观指标
        features = pd.concat([market_indicators, macro_indicators], axis=1)

        # 创建滞后特征
        features = self.create_lag_features(features, lags=3)

        # 创建滚动特征
        features = self.create_rolling_features(features, windows=[5, 10])

        # 移除缺失值
        features = features.dropna()

        self.feature_names = features.columns.tolist()

        print(f"✓ 特征准备完成：{len(features)}个样本，{len(features.columns)}个特征")

        return features

    def fit(self, market_indicators, macro_indicators, price_data):
        """
        拟合模型

        Parameters:
        -----------
        market_indicators : DataFrame
            市场风险指标
        macro_indicators : DataFrame
            宏观风险指标
        price_data : Series
            价格数据（用于计算目标变量）
        """
        print(f"\n开始训练复合风险预警指数模型...")
        print(f"模型类型：{self.model_type}")
        print(f"预测天数：{self.forecast_horizon}天")
        print("=" * 80)

        # 准备特征
        X = self.prepare_features(market_indicators, macro_indicators)

        # 准备目标变量
        y = self.prepare_target(price_data)

        # 合并特征和目标
        data = pd.concat([X, y], axis=1).dropna()

        # 获取目标变量列名
        target_col = y.name if y.name is not None else 'target'
        if target_col not in data.columns:
            # 如果y.name是None，最后一列应该是目标变量
            target_col = data.columns[-1]

        X = data.drop(columns=[target_col])
        y = data[target_col]

        # 划分训练集和测试集（时间序列）
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        # 数据标准化
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # 拟合模型
        print("\n训练模型...")
        if self.model_type == 'xgboost':
            self.model.fit(X_train_scaled, y_train,
                          eval_set=[(X_test_scaled, y_test)],
                          verbose=False)
        elif self.model_type == 'lightgbm':
            self.model.fit(X_train_scaled, y_train,
                          eval_set=[(X_test_scaled, y_test)],
                          callbacks=[lgb.log_evaluation(0)])
        else:
            self.model.fit(X_train_scaled, y_train)

        # 预测
        y_train_pred = self.model.predict(X_train_scaled)
        y_test_pred = self.model.predict(X_test_scaled)

        # 计算性能指标
        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)

        train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))
        test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))

        train_mae = mean_absolute_error(y_train, y_train_pred)
        test_mae = mean_absolute_error(y_test, y_test_pred)

        print("\n模型性能：")
        print("-" * 80)
        print(f"训练集：")
        print(f"  R²: {train_r2:.4f}")
        print(f"  RMSE: {train_rmse:.2f}%")
        print(f"  MAE: {train_mae:.2f}%")

        print(f"\n测试集：")
        print(f"  R²: {test_r2:.4f}")
        print(f"  RMSE: {test_rmse:.2f}%")
        print(f"  MAE: {test_mae:.2f}%")

        # 预警准确率（预测回撤>5%的准确率）
        test_risk_actual = y_test < -5  # 实际回撤超过5%
        test_risk_pred = y_test_pred < -5  # 预测回撤超过5%

        if test_risk_actual.sum() > 0:
            warning_precision = (test_risk_actual & test_risk_pred).sum() / (test_risk_pred.sum() + 1e-8)
            warning_recall = (test_risk_actual & test_risk_pred).sum() / test_risk_actual.sum()

            print(f"\n预警能力（回撤>5%）：")
            print(f"  精确率: {warning_precision:.2%}")
            print(f"  召回率: {warning_recall:.2%}")

        # 特征重要性
        print("\nTop 15 重要特征：")
        print("-" * 80)
        importance = dict(zip(X.columns, self.model.feature_importances_))
        importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)

        for i, (feat, imp) in enumerate(importance[:15], 1):
            print(f"  {i:2d}. {feat:40s}: {imp:.4f}")

        print("\n" + "=" * 80)
        print("模型训练完成！")

        # 保存性能指标
        self.performance = {
            'train_r2': train_r2,
            'test_r2': test_r2,
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'train_mae': train_mae,
            'test_mae': test_mae,
            'feature_importance': dict(importance)
        }

        self.y_test = y_test
        self.y_test_pred = y_test_pred

    def predict(self, market_indicators, macro_indicators):
        """
        预测综合风险指数

        Parameters:
        -----------
        market_indicators : DataFrame
            市场风险指标
        macro_indicators : DataFrame
            宏观风险指标

        Returns:
        --------
        Series
            预测的风险指数（0-100）
        """
        if self.model is None:
            print("Error: 模型未训练")
            return None

        # 准备特征
        X = self.prepare_features(market_indicators, macro_indicators)

        # 标准化
        X_scaled = self.scaler.transform(X)

        # 预测回撤
        predicted_drawdown = self.model.predict(X_scaled)

        # 转换为风险指数（0-100）
        # 回撤越大，风险指数越高
        risk_index = np.clip(-predicted_drawdown * 10, 0, 100)  # -10%回撤 = 100风险指数

        return pd.Series(risk_index, index=X.index, name='risk_index')

    def get_current_risk_level(self, market_indicators, macro_indicators):
        """
        获取当前风险等级

        Parameters:
        -----------
        market_indicators : DataFrame
            市场风险指标
        macro_indicators : DataFrame
            宏观风险指标

        Returns:
        --------
        dict
            当前风险等级信息
        """
        risk_index = self.predict(market_indicators, macro_indicators)

        if risk_index is None:
            return None

        current_risk = risk_index.iloc[-1]

        # 风险等级划分
        if current_risk < 20:
            level = '低风险'
            color = '绿色'
        elif current_risk < 40:
            level = '中等风险'
            color = '黄色'
        elif current_risk < 70:
            level = '高风险'
            color = '橙色'
        else:
            level = '极高风险'
            color = '红色'

        return {
            'risk_index': current_risk,
            'risk_level': level,
            'risk_color': color,
            'date': risk_index.index[-1].strftime('%Y-%m-%d')
        }

    def calculate_risk_trend(self, market_indicators, macro_indicators, window=20):
        """
        计算风险趋势

        Parameters:
        -----------
        market_indicators : DataFrame
            市场风险指标
        macro_indicators : DataFrame
            宏观风险指标
        window : int
            滚动窗口

        Returns:
        --------
        Series
            风险趋势（正=上升，负=下降）
        """
        risk_index = self.predict(market_indicators, macro_indicators)

        if risk_index is None:
            return None

        # 计算滚动均值的变化率
        risk_ma = risk_index.rolling(window=window).mean()
        risk_trend = risk_ma.diff()

        return risk_trend

    def summary(self):
        """
        输出模型摘要
        """
        if not hasattr(self, 'performance'):
            print("Error: 模型未训练")
            return

        print("\n模型摘要：")
        print("=" * 80)
        print(f"模型类型：{self.model_type}")
        print(f"预测天数：{self.forecast_horizon}天")
        print(f"特征数量：{len(self.feature_names)}")

        print("\n性能指标：")
        print(f"  测试集 R²: {self.performance['test_r2']:.4f}")
        print(f"  测试集 RMSE: {self.performance['test_rmse']:.2f}%")
        print(f"  测试集 MAE: {self.performance['test_mae']:.2f}%")

        print("\n" + "=" * 80)

        return self.performance

    def export_risk_index(self, market_indicators, macro_indicators,
                         output_path='data/derived/indicators/composite_risk_index.csv'):
        """
        导出风险指数到CSV

        Parameters:
        -----------
        market_indicators : DataFrame
            市场风险指标
        macro_indicators : DataFrame
            宏观风险指标
        output_path : str
            输出文件路径（默认：data/derived/indicators/）
        """
        risk_index = self.predict(market_indicators, macro_indicators)

        if risk_index is None:
            return

        risk_index.to_csv(output_path, encoding='utf-8-sig')
        print(f"✓ 风险指数已导出到：{output_path}")


# 测试代码
if __name__ == "__main__":
    print("复合风险预警指数模块已创建")
    print("使用示例：")

    print("""
    from models.risk.composite_risk_index import CompositeRiskIndex

    # 初始化
    cri = CompositeRiskIndex(model_type='xgboost', forecast_horizon=5)

    # 训练模型
    cri.fit(market_indicators, macro_indicators, price_data)

    # 预测风险指数
    risk_index = cri.predict(market_indicators, macro_indicators)

    # 获取当前风险等级
    current_risk = cri.get_current_risk_level(market_indicators, macro_indicators)
    print(f"当前风险：{current_risk}")

    # 导出风险指数
    cri.export_risk_index(market_indicators, macro_indicators)
    """)
