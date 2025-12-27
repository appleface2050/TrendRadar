# Python
import pandas as pd
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly
import plotly.io as pio
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import os

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
rq_csv_path = os.path.join(script_dir, 'rq.csv')


def run_power():
    # Python
    df = pd.read_csv(rq_csv_path)
    df.rename(columns={"日期": "ds", "RQ": "y"}, inplace=True)

    # print(df)

    # Python
    m = Prophet()
    m.fit(df)

    future = m.make_future_dataframe(periods=30)
    # print(future)

    forecast = m.predict(future)
    # print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']])

    print("未来30日增长值：", round(forecast.iloc[-1].yhat - df.iloc[-1].y, 2))

    fig1 = m.plot(forecast)

    plt.show()


def physical_power():
    # Python
    df = pd.read_csv(rq_csv_path)
    # df.rename(columns={"日期": "ds", "RQ": "y"}, inplace=True)
    df.rename(columns={"日期": "ds", "physical power": "y"}, inplace=True)

    # print(df)

    # Python
    m = Prophet()
    m.fit(df)

    future = m.make_future_dataframe(periods=30)
    # print(future)

    forecast = m.predict(future)
    # print(forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']])

    print("未来30日增长值：", round(forecast.iloc[-1].yhat - df.iloc[-1].y, 2))

    fig1 = m.plot(forecast)

    plt.show()


def run_status():
    """身体状态"""
    df = pd.read_csv(rq_csv_path)
    # 将日期列转换为日期类型
    # df = df[["日期", "physical condition", "physical power","fatigue"]]
    df = df[["日期", "physical power",  "fatigue"]]
    df['日期'] = pd.to_datetime(df['日期'])

    # 设置日期为索引
    df.set_index('日期', inplace=True)

    # 绘制折线图
    plt.figure(figsize=(10, 6))
    df.plot(marker='o', linestyle='-', ax=plt.gca())

    # 添加标题和标签
    plt.title('')
    plt.xlabel('')
    plt.ylabel('')

    # 显示图例
    # plt.legend(loc='upper left')
    # font = FontProperties(fname=r'C:\Windows\Fonts\SimHei.ttf', size=12)
    # plt.legend(prop=font, loc='upper left')
    # 显示图表
    plt.show()


if __name__ == '__main__':
    run_power()
    physical_power()
    run_status()
