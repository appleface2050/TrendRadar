# Python
import pandas as pd
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly
import plotly.io as pio
import matplotlib.pyplot as plt
import os

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, 'rq.csv')

# Python
df = pd.read_csv(csv_path)
df.rename(columns={"日期":"ds", "RQ": "y"}, inplace=True)

print(df)


# Python
m = Prophet()
m.fit(df)

future = m.make_future_dataframe(periods=30)
forecast = m.predict(future)
# print(future)
# print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']])


fig1 = m.plot(forecast)

plt.show()
# fig1.show(validate=False)

# Keep the plot window open
# pio.show(fig1, validate=False)


# plot_plotly(m, forecast)
#
# plot_components_plotly(m, forecast)





print("未来30日增长值：", round(forecast.iloc[-1].yhat - df.iloc[-1].y, 2))
