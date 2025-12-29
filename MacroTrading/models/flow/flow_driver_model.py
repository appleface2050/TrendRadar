"""
资金流三层驱动模型

将资金流驱动因素分解为三层：
1. 全球层：VIX、美元指数、全球风险偏好
2. 相对吸引力层：中美实际利差、增长预期差
3. 市场微观层：AH溢价、USDCNH期权、市场情绪

使用回归和机器学习方法分析各层驱动因素的贡献度
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

try:
    from sklearn.linear_model import LinearRegression, Ridge, Lasso
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import r2_score, mean_squared_error
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not installed")

try:
    import statsmodels.api as sm
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    print("Warning: statsmodels not installed")


class FlowDriverModel:
    """资金流三层驱动模型"""

    def __init__(self, method='ols'):
        """
        初始化模型

        Parameters:
        -----------
        method : str
            回归方法：'ols', 'ridge', 'lasso', 'rf'
        """
        self.method = method
        self.model = None
        self.scaler = StandardScaler() if method in ['ridge', 'lasso'] else None
        self.feature_names = []
        self.layer_mapping = {}

        # 初始化回归模型
        if SKLEARN_AVAILABLE:
            if method == 'ols':
                self.model = LinearRegression()
            elif method == 'ridge':
                self.model = Ridge(alpha=1.0)
            elif method == 'lasso':
                self.model = Lasso(alpha=1.0)
            elif method == 'rf':
                self.model = RandomForestRegressor(n_estimators=100, random_state=42)

    def prepare_features(self, data_dict):
        """
        准备特征变量

        Parameters:
        -----------
        data_dict : dict
            包含所有数据的字典

        Returns:
        --------
        DataFrame
            特征矩阵
        """
        print("准备特征变量...")

        # 初始化特征DataFrame
        features = pd.DataFrame()

        # Layer 1: 全球层
        if 'vix' in data_dict and data_dict['vix'] is not None:
            features['vix'] = data_dict['vix']['vix']
            self.layer_mapping['vix'] = 'global'

        if 'dxy' in data_dict and data_dict['dxy'] is not None:
            features['dxy'] = data_dict['dxy']['dxy']
            self.layer_mapping['dxy'] = 'global'

        # Layer 2: 相对吸引力层
        if 'rate_diff' in data_dict and data_dict['rate_diff'] is not None:
            features['rate_diff'] = data_dict['rate_diff']['rate_diff']
            self.layer_mapping['rate_diff'] = 'attraction'

        # 如果有增长预期差数据，添加进来
        # features['growth_diff'] = ...

        # Layer 3: 市场微观层
        if 'ah_premium' in data_dict and data_dict['ah_premium'] is not None:
            features['ah_premium'] = data_dict['ah_premium']['ah_premium']
            self.layer_mapping['ah_premium'] = 'micro'

        # 如果有USDCNH期权数据，添加进来
        # features['usdcnh_vol'] = ...

        # 处理缺失值
        features = features.dropna()

        print(f"✓ 特征准备完成，共{len(features.columns)}个特征，{len(features)}个观测值")

        return features

    def prepare_target(self, flow_data):
        """
        准备目标变量（资金流）

        Parameters:
        -----------
        flow_data : DataFrame
            资金流数据

        Returns:
        --------
        Series
            目标变量
        """
        if flow_data is None or len(flow_data) == 0:
            return None

        # 如果有净流入数据，使用净流入
        if 'net_flow_north' in flow_data.columns:
            target = flow_data[['net_flow_north']].copy()
            target = target.set_index(flow_data['trade_date'])
            target.columns = ['flow']
        else:
            # 否则使用其他资金流指标
            target = flow_data[['ggt_ss', 'ggt_sz']].copy()
            target['flow'] = target['ggt_ss'] + target['ggt_sz']
            target = target.set_index(flow_data['trade_date'])
            target = target[['flow']]

        return target['flow']

    def calculate_layer_importance(self, X, y):
        """
        计算各层的重要性

        Parameters:
        -----------
        X : DataFrame
            特征矩阵
        y : Series
            目标变量

        Returns:
        --------
        dict
            各层的重要性得分
        """
        # 训练一个简单的随机森林模型
        if not SKLEARN_AVAILABLE:
            return {}

        rf = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=5)
        rf.fit(X, y)

        # 获取特征重要性
        feature_importance = dict(zip(X.columns, rf.feature_importances_))

        # 按层聚合
        layer_importance = {
            'global': 0,
            'attraction': 0,
            'micro': 0
        }

        for feature, importance in feature_importance.items():
            layer = self.layer_mapping.get(feature, 'micro')
            layer_importance[layer] += importance

        # 归一化
        total = sum(layer_importance.values())
        if total > 0:
            layer_importance = {k: v/total for k, v in layer_importance.items()}

        return layer_importance

    def fit(self, data_dict, flow_data):
        """
        拟合模型

        Parameters:
        -----------
        data_dict : dict
            包含所有特征数据的字典
        flow_data : DataFrame
            资金流数据（目标变量）
        """
        print(f"\n开始拟合资金流驱动模型（方法：{self.method}）...")
        print("=" * 80)

        # 准备特征和目标
        X = self.prepare_features(data_dict)
        y = self.prepare_target(flow_data)

        if X is None or y is None:
            print("Error: 特征或目标变量为空")
            return

        # 合并特征和目标
        data = pd.merge(X, y, left_index=True, right_index=True, how='inner')
        X = data.drop(columns=['flow'])
        y = data['flow']

        self.feature_names = X.columns.tolist()

        # 数据标准化（Ridge和Lasso）
        if self.scaler is not None:
            X_scaled = self.scaler.fit_transform(X)
            X = pd.DataFrame(X_scaled, index=X.index, columns=X.columns)

        # 划分训练集和测试集
        if len(X) > 50:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )
        else:
            X_train, y_train = X, y
            X_test, y_test = X, y

        # 拟合模型
        self.model.fit(X_train, y_train)

        # 预测
        y_train_pred = self.model.predict(X_train)
        y_test_pred = self.model.predict(X_test)

        # 计算性能指标
        train_r2 = r2_score(y_train, y_train_pred)
        train_rmse = np.sqrt(mean_squared_error(y_train, y_train_pred))

        if len(X_test) > 0:
            test_r2 = r2_score(y_test, y_test_pred)
            test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))
        else:
            test_r2 = train_r2
            test_rmse = train_rmse

        print("\n模型性能：")
        print(f"  训练集 R²: {train_r2:.4f}")
        print(f"  训练集 RMSE: {train_rmse:.2f}")
        print(f"  测试集 R²: {test_r2:.4f}")
        print(f"  测试集 RMSE: {test_rmse:.2f}")

        # 计算特征重要性
        print("\n特征重要性：")
        print("-" * 80)

        if self.method in ['ridge', 'lasso']:
            # 对于正则化回归，使用系数绝对值作为重要性
            importance = np.abs(self.model.coef_)
        elif self.method == 'rf':
            importance = self.model.feature_importances_
        else:
            # 对于OLS，使用标准化系数
            importance = self._calculate_standardized_coef(X, y)

        feature_importance = dict(zip(self.feature_names, importance))
        feature_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)

        for feature, imp in feature_importance:
            layer = self.layer_mapping.get(feature, 'unknown')
            print(f"  {feature:20s} ({layer:12s}): {imp:.4f}")

        # 计算各层重要性
        print("\n各层重要性：")
        print("-" * 80)
        layer_importance = self.calculate_layer_importance(X, y)

        layer_names = {
            'global': '全球层',
            'attraction': '相对吸引力层',
            'micro': '市场微观层'
        }

        for layer, importance in layer_importance.items():
            print(f"  {layer_names[layer]:20s}: {importance:.2%}")

        print("\n" + "=" * 80)
        print("模型拟合完成！")

        # 保存性能指标
        self.performance = {
            'train_r2': train_r2,
            'train_rmse': train_rmse,
            'test_r2': test_r2,
            'test_rmse': test_rmse,
            'feature_importance': dict(feature_importance),
            'layer_importance': layer_importance
        }

    def _calculate_standardized_coef(self, X, y):
        """计算标准化系数"""
        if not STATSMODELS_AVAILABLE:
            # 如果statsmodels不可用，使用系数绝对值
            return np.abs(self.model.coef_)

        # 添加常数项
        X_sm = sm.add_constant(X)

        # OLS回归
        model = sm.OLS(y, X_sm).fit()

        # 标准化系数
        coef = model.params[1:]  # 去掉常数项
        return np.abs(coef)

    def predict(self, data_dict):
        """
        预测资金流

        Parameters:
        -----------
        data_dict : dict
            包含所有特征数据的字典

        Returns:
        --------
        Series
            预测的资金流
        """
        if self.model is None:
            print("Error: 模型未训练")
            return None

        # 准备特征
        X = self.prepare_features(data_dict)

        # 数据标准化
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X)
            X = pd.DataFrame(X_scaled, index=X.index, columns=X.columns)

        # 预测
        y_pred = self.model.predict(X)

        return pd.Series(y_pred, index=X.index, name='predicted_flow')

    def get_layer_contribution(self, data_dict):
        """
        获取各层对预测的贡献度

        Parameters:
        -----------
        data_dict : dict
            包含所有特征数据的字典

        Returns:
        --------
        DataFrame
            各层的贡献度时间序列
        """
        if self.model is None:
            print("Error: 模型未训练")
            return None

        # 准备特征
        X = self.prepare_features(data_dict)

        # 数据标准化
        if self.scaler is not None:
            X_scaled = self.scaler.transform(X)
            X = pd.DataFrame(X_scaled, index=X.index, columns=X.columns)

        # 计算各层贡献
        layer_contribution = pd.DataFrame(index=X.index)

        if self.method in ['ols', 'ridge', 'lasso']:
            # 线性模型：直接使用系数
            for feature in X.columns:
                coef_idx = self.feature_names.index(feature)
                coef = self.model.coef_[coef_idx]
                layer = self.layer_mapping.get(feature, 'micro')

                if layer not in layer_contribution.columns:
                    layer_contribution[layer] = 0

                layer_contribution[layer] += coef * X[feature]

        elif self.method == 'rf':
            # 随机森林：使用特征重要性
            for feature in X.columns:
                importance = self.feature_importance.get(feature, 0)
                layer = self.layer_mapping.get(feature, 'micro')

                if layer not in layer_contribution.columns:
                    layer_contribution[layer] = 0

                layer_contribution[layer] += importance * X[feature]

        return layer_contribution

    def summary(self):
        """
        输出模型摘要

        Returns:
        --------
        dict
            模型摘要信息
        """
        if not hasattr(self, 'performance'):
            print("Error: 模型未训练")
            return None

        print("\n模型摘要：")
        print("=" * 80)

        print(f"\n模型类型：{self.method}")
        print(f"特征数量：{len(self.feature_names)}")

        print("\n性能指标：")
        print(f"  训练集 R²: {self.performance['train_r2']:.4f}")
        print(f"  测试集 R²: {self.performance['test_r2']:.4f}")

        print("\n各层重要性：")
        layer_names = {
            'global': '全球层',
            'attraction': '相对吸引力层',
            'micro': '市场微观层'
        }

        for layer, importance in self.performance['layer_importance'].items():
            print(f"  {layer_names[layer]}: {importance:.2%}")

        print("\n" + "=" * 80)

        return self.performance


# 测试代码
if __name__ == "__main__":
    from data.flow.flow_fetcher import FlowDataFetcher
    from configs.db_config import get_confidential_config

    # 加载配置
    config = get_confidential_config()

    # 获取数据
    print("获取资金流数据...")
    fetcher = FlowDataFetcher(
        tushare_token=config.get('TUSHARE_DataApi__token'),
        fred_key=config.get('FRED_API_Key')
    )

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365*2)).strftime('%Y-%m-%d')

    data_dict = fetcher.fetch_all_flow_data(start_date, end_date)

    # 如果有北向资金流数据，使用它作为目标
    if 'northbound_flow' in data_dict:
        flow_data = data_dict['northbound_flow']
    else:
        print("Error: 没有资金流数据")
        exit()

    # 训练模型
    model = FlowDriverModel(method='ols')
    model.fit(data_dict, flow_data)

    # 输出摘要
    model.summary()

    # 获取各层贡献
    contribution = model.get_layer_contribution(data_dict)
    if contribution is not None:
        print("\n各层贡献度时间序列：")
        print(contribution.tail())
