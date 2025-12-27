import warnings

# 禁用所有警告
warnings.filterwarnings('ignore')


import datetime
import os

import pandas as pd
import statsmodels.api as sm
import plotly.graph_objs as go
import plotly.offline as pyo

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
rq_csv_path = os.path.join(script_dir, 'rq.csv')

# Read the data
df = pd.read_csv(rq_csv_path)
df['日期'] = pd.to_datetime(df['日期'])
df.set_index('日期', inplace=True)

# Fit the ARIMA model
# model = sm.tsa.ARIMA(df['RQ'], order=(5, 5, 5))
model = sm.tsa.ARIMA(df['RQ'], order=(2, 2, 2))
results = model.fit()

# Forecast future data
forecast = results.forecast(steps=30)  # Forecast the next 15 data points

# forecast["date"] = pd.date_range(start=df.index[-1], periods=16)[1:]
# Print the forecast results
# print("未来30天的预测值:")
print("未来30天增长值:", round(forecast.values[-1] - df['RQ'][-1], 2))

# Create a Plotly figure
trace1 = go.Scatter(x=df.index, y=df['RQ'], mode='lines', name='观测值')
trace2 = go.Scatter(x=pd.date_range(start=df.index[-1], periods=31)[1:], y=forecast, mode='lines', name='预测值',
                    line=dict(dash='dash'))

data = [trace1, trace2]

layout = go.Layout(
    title='RQ时间序列预测',
    xaxis=dict(title='日期'),
    yaxis=dict(title='RQ')
)

fig = go.Figure(data=data, layout=layout)

# Display the plot using Plotly
today = datetime.date.today().strftime("%Y-%m-%d")
result_dir = os.path.join(script_dir, 'result')
os.makedirs(result_dir, exist_ok=True)
# pyo.plot(fig, filename=os.path.join(result_dir, today + ".html"))
pyo.plot(fig, filename=os.path.join(result_dir, "result" + ".html"))
