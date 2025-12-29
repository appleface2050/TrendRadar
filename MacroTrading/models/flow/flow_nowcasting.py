"""
资金流Nowcasting模型

使用MIDAS回归预测未来1-5日的资金流方向和规模

功能：
1. 短期预测：预测未来1-5日的资金流
2. 方向预测：预测资金流入/流出方向
3. 不确定性量化：提供预测区间
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import Ridge
    from sklearn.metrics import accuracy_score, precision_score, recall_score
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not installed")

try:
    from models.midas.midas_regression import MIDASRegressor
    MIDAS_AVAILABLE = True
except ImportError:
    MIDAS_AVAILABLE = False
    print("Warning: MIDAS module not available")


class FlowNowcastingModel:
    """资金流Nowcasting模型"""

    def __init__(self, horizon_days=5, method='rf'):
        """
        初始化模型

        Parameters:
        -----------
        horizon_days : int
            预测天数（1-5天）
        method : str
            预测方法：'rf'（随机森林）, 'gbm'（梯度提升）, 'ridge'（岭回归）, 'midas'
        """
        self.horizon_days = horizon_days
        self.method = method
        self.model = None
        self.feature_names = []

        # 初始化模型
        if SKLEARN_AVAILABLE:
            if method == 'rf':
                self.model = RandomForestRegressor(
                    n_estimators=200,
                    max_depth=10,
                    min_samples_split=10,
                    random_state=42
                )
            elif method == 'gbm':
                self.model = GradientBoostingRegressor(
                    n_estimators=200,
                    max_depth=5,
                    learning_rate=0.01,
                    random_state=42
                )
            elif method == 'ridge':
                self.model = Ridge(alpha=1.0)

        elif method == 'midas' and MIDAS_AVAILABLE:
            self.model = MIDASRegressor(
                target_freq='D',
                predictor_freq='D',
                poly_degree=3
            )

    def create_lag_features(self, df, lags=5):
        """
        创建滞后特征

        Parameters:
        -----------
        df : DataFrame
            原始数据
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
            原始数据
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
                # 滚动最大值
                data[f'{col}_max_{window}'] = data[col].rolling(window=window).max()
                # 滚动最小值
                data[f'{col}_min_{window}'] = data[col].rolling(window=window).min()

        return data

    def prepare_features_targets(self, flow_data, external_data=None):
        """
        准备特征和目标变量

        Parameters:
        -----------
        flow_data : DataFrame
            资金流数据
        external_data : dict, optional
            外部特征数据（VIX、DXY等）

        Returns:
        --------
        X, y : DataFrame, Series
            特征矩阵和目标变量
        """
        print("准备特征和目标变量...")

        # 确保日期索引
        if 'date' in flow_data.columns:
            flow_data['date'] = pd.to_datetime(flow_data['date'])
            flow_data = flow_data.set_index('date')

        if 'trade_date' in flow_data.columns:
            flow_data['trade_date'] = pd.to_datetime(flow_data['trade_date'])
            flow_data = flow_data.set_index('trade_date')

        # 提取资金流
        if 'net_flow_north' in flow_data.columns:
            flow = flow_data[['net_flow_north']].copy()
            flow.columns = ['flow']
        elif 'ggt_ss' in flow_data.columns and 'ggt_sz' in flow_data.columns:
            flow = pd.DataFrame()
            flow['flow'] = flow_data['ggt_ss'] + flow_data['ggt_sz']
            flow.index = flow_data.index
        else:
            print("Error: 未找到资金流数据")
            return None, None

        # 创建滞后特征
        flow_features = self.create_lag_features(flow, lags=5)
        flow_features = self.create_rolling_features(flow[['flow']], windows=[5, 10, 20])

        # 添加外部特征
        if external_data:
            for key, df in external_data.items():
                if df is not None and len(df) > 0:
                    # 确保日期索引
                    if not isinstance(df.index, pd.DatetimeIndex):
                        df.index = pd.to_datetime(df.index)

                    # 取第一个数值列
                    numeric_cols = df.select_dtypes(include=[np.number]).columns
                    if len(numeric_cols) > 0:
                        col = numeric_cols[0]
                        flow_features[key] = df[col]

        # 移除原始flow列（避免数据泄露）
        if 'flow' in flow_features.columns:
            flow_features = flow_features.drop(columns=['flow'])

        # 创建目标变量（未来N天的资金流）
        target = flow['flow'].shift(-self.horizon_days)

        # 移除缺失值
        combined = pd.concat([flow_features, target], axis=1)
        combined.columns = list(flow_features.columns) + ['target']
        combined = combined.dropna()

        X = combined.drop(columns=['target'])
        y = combined['target']

        self.feature_names = X.columns.tolist()

        print(f"✓ 特征准备完成：{len(X)}个样本，{len(X.columns)}个特征")
        print(f"✓ 目标变量：未来{self.horizon_days}天的资金流")

        return X, y

    def fit(self, flow_data, external_data=None):
        """
        拟合模型

        Parameters:
        -----------
        flow_data : DataFrame
            资金流数据
        external_data : dict, optional
            外部特征数据
        """
        print(f"\n开始训练资金流Nowcasting模型...")
        print(f"预测天数：{self.horizon_days}天")
        print(f"预测方法：{self.method}")
        print("=" * 80)

        # 准备数据
        X, y = self.prepare_features_targets(flow_data, external_data)

        if X is None or y is None:
            print("Error: 数据准备失败")
            return

        # 划分训练集和测试集
        if len(X) > 100:
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        else:
            X_train, y_train = X, y
            X_test, y_test = X, y

        # 拟合模型
        if self.method != 'midas':
            self.model.fit(X_train, y_train)

        # 预测
        y_train_pred = self.model.predict(X_train)
        y_test_pred = self.model.predict(X_test)

        # 计算性能指标
        train_r2 = self._calculate_r2(y_train, y_train_pred)
        test_r2 = self._calculate_r2(y_test, y_test_pred)

        train_rmse = np.sqrt(np.mean((y_train - y_train_pred)**2))
        test_rmse = np.sqrt(np.mean((y_test - y_test_pred)**2))

        # 计算方向准确率
        train_direction_acc = self._calculate_direction_accuracy(y_train, y_train_pred)
        test_direction_acc = self._calculate_direction_accuracy(y_test, y_test_pred)

        print("\n模型性能：")
        print("-" * 80)
        print(f"训练集：")
        print(f"  R²: {train_r2:.4f}")
        print(f"  RMSE: {train_rmse:.2f}")
        print(f"  方向准确率: {train_direction_acc:.2%}")

        print(f"\n测试集：")
        print(f"  R²: {test_r2:.4f}")
        print(f"  RMSE: {test_rmse:.2f}")
        print(f"  方向准确率: {test_direction_acc:.2%}")

        # 特征重要性
        if self.method in ['rf', 'gbm'] and SKLEARN_AVAILABLE:
            print("\nTop 10 重要特征：")
            print("-" * 80)
            importance = dict(zip(X.columns, self.model.feature_importances_))
            importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)

            for i, (feat, imp) in enumerate(importance[:10], 1):
                print(f"  {i:2d}. {feat:30s}: {imp:.4f}")

        print("\n" + "=" * 80)
        print("模型训练完成！")

        # 保存性能指标
        self.performance = {
            'train_r2': train_r2,
            'test_r2': test_r2,
            'train_rmse': train_rmse,
            'test_rmse': test_rmse,
            'train_direction_acc': train_direction_acc,
            'test_direction_acc': test_direction_acc
        }

        self.X_test = X_test
        self.y_test = y_test

    def _calculate_r2(self, y_true, y_pred):
        """计算R²"""
        ss_res = np.sum((y_true - y_pred)**2)
        ss_tot = np.sum((y_true - np.mean(y_true))**2)
        return 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    def _calculate_direction_accuracy(self, y_true, y_pred):
        """计算方向准确率"""
        true_direction = np.sign(y_true)
        pred_direction = np.sign(y_pred)
        return np.mean(true_direction == pred_direction)

    def predict(self, recent_data, external_data=None):
        """
        预测未来N天的资金流

        Parameters:
        -----------
        recent_data : DataFrame
            最近的资金流数据
        external_data : dict, optional
            最新的外部特征数据

        Returns:
        --------
        dict
            预测结果
        """
        if self.model is None:
            print("Error: 模型未训练")
            return None

        # 准备特征（使用最近的数据）
        X, _ = self.prepare_features_targets(recent_data, external_data)

        if X is None or len(X) == 0:
            print("Error: 无法准备特征")
            return None

        # 使用最后一个样本进行预测
        X_latest = X.iloc[[-1]]

        # 预测
        prediction = self.model.predict(X_latest)[0]

        # 如果是随机森林，获取预测区间
        if self.method == 'rf' and SKLEARN_AVAILABLE:
            predictions = []
            for tree in self.model.estimators_:
                predictions.append(tree.predict(X_latest)[0])

            prediction_std = np.std(predictions)
            prediction_lower = prediction - 1.96 * prediction_std
            prediction_upper = prediction + 1.96 * prediction_std
        else:
            prediction_lower = prediction
            prediction_upper = prediction

        result = {
            'horizon_days': self.horizon_days,
            'prediction': prediction,
            'prediction_lower': prediction_lower,
            'prediction_upper': prediction_upper,
            'direction': 'inflow' if prediction > 0 else 'outflow',
            'date': datetime.now().strftime('%Y-%m-%d')
        }

        return result

    def predict_rolling(self, flow_data, external_data=None, start_idx=None):
        """
        滚动预测（用于回测）

        Parameters:
        -----------
        flow_data : DataFrame
            资金流数据
        external_data : dict, optional
            外部特征数据
        start_idx : int, optional
            开始预测的位置

        Returns:
        --------
        DataFrame
            滚动预测结果
        """
        X, y = self.prepare_features_targets(flow_data, external_data)

        if X is None or y is None:
            return None

        if start_idx is None:
            start_idx = int(len(X) * 0.8)

        predictions = []

        for i in range(start_idx, len(X)):
            # 使用i之前的数据训练
            X_train = X.iloc[:i]
            y_train = y.iloc[:i]

            # 训练模型
            self.model.fit(X_train, y_train)

            # 预测
            X_pred = X.iloc[[i]]
            pred = self.model.predict(X_pred)[0]

            predictions.append({
                'date': X.index[i],
                'actual': y.iloc[i],
                'predicted': pred,
                'direction_actual': 'inflow' if y.iloc[i] > 0 else 'outflow',
                'direction_pred': 'inflow' if pred > 0 else 'outflow'
            })

        return pd.DataFrame(predictions)

    def summary(self):
        """
        输出模型摘要
        """
        if not hasattr(self, 'performance'):
            print("Error: 模型未训练")
            return

        print("\n模型摘要：")
        print("=" * 80)
        print(f"预测天数：{self.horizon_days}天")
        print(f"预测方法：{self.method}")
        print(f"特征数量：{len(self.feature_names)}")

        print("\n性能指标：")
        print(f"  测试集 R²: {self.performance['test_r2']:.4f}")
        print(f"  测试集 RMSE: {self.performance['test_rmse']:.2f}")
        print(f"  方向准确率: {self.performance['test_direction_acc']:.2%}")

        print("\n" + "=" * 80)


# 测试代码
if __name__ == "__main__":
    # 这里应该使用实际的资金流数据进行测试
    print("资金流Nowcasting模型已创建")
    print("请使用实际的资金流数据进行训练和预测")
