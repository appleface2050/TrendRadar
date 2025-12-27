import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt

# 读取数据
data = {'ds': ['2020-07', '2020-08', '2020-09', '2020-10', '2020-11', '2020-12',
               '2021-10', '2022-01', '2022-03', '2022-04', '2022-05', '2022-06',
               '2022-07', '2022-08', '2022-09', '2022-12', '2023-01', '2023-02', '2023-03'],
        'y': [6.56, 61.63, 40.78, 92.06, 63.33, 10.01, 2.11, 14.85, 7.57, 9.88, 22.25, 8.31, 2.25, 5.91, 1.26, 1.29, 0.66, 7.19, 0.67]}
df = pd.DataFrame(data)

# 将时间戳列转换为 datetime 类型
df['ds'] = pd.to_datetime(df['ds'])

# 特征工程 - 添加滞后项
df['lag_1'] = df['y'].shift(1)

# 去掉第一行含有 NaN 的数据
df = df.dropna()

# 拆分数据集
# train_size = int(len(df) * 0.8)
# train, test = df[0:train_size], df[train_size:]
train, test = df, df

# 准备训练和测试数据
X_train, y_train = train[['lag_1']], train['y']
X_test, y_test = test[['lag_1']], test['y']

# 创建并训练线性回归模型
model = LinearRegression()
model.fit(X_train, y_train)

# 获取最后一个月的 lag_1 值
latest_lag_1 = df['lag_1'].iloc[-1]

# 使用模型进行预测
next_month_prediction = model.predict([[latest_lag_1]])

# 预测下一个月的 "y" 值
predicted_y = next_month_prediction[0]

print(f'预测下一个月的 y 值: {predicted_y}')
# # 评估模型性能
# rmse = np.sqrt(mean_squared_error(y_test, predictions))
# print(f'Root Mean Squared Error: {rmse}')
#
# # 可视化结果
# plt.plot(test['ds'], y_test, label='Actual')
# plt.plot(test['ds'], predictions, label='Predicted')
# plt.legend()
# plt.show()
