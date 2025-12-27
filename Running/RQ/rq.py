# Python
import warnings
warnings.filterwarnings('ignore')

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

if __name__ == '__main__':
    df_run_power = pd.read_csv(rq_csv_path)
    df_run_power.rename(columns={"日期": "ds", "RQ": "y"}, inplace=True)

    m_run_power = Prophet()
    m_run_power.fit(df_run_power)

    future_run_power = m_run_power.make_future_dataframe(periods=30)
    forecast_run_power = m_run_power.predict(future_run_power)
    print("running power未来30日增长值：", round(forecast_run_power.iloc[-1].yhat - df_run_power.iloc[-1].y, 2))

    df_physical_power = pd.read_csv(rq_csv_path)
    df_physical_power.rename(columns={"日期": "ds", "physical power": "y"}, inplace=True)

    m_physical_power = Prophet()
    m_physical_power.fit(df_physical_power)

    future_physical_power = m_physical_power.make_future_dataframe(periods=30)
    forecast_physical_power = m_physical_power.predict(future_physical_power)
    print("physical power未来30日增长值：", round(forecast_physical_power.iloc[-1].yhat - df_physical_power.iloc[-1].y, 2))

    # Additional code for the third plot
    df_status = pd.read_csv(rq_csv_path)
    df_status = df_status[["日期", "status", "physical power", "fatigue"]]
    df_status['日期'] = pd.to_datetime(df_status['日期'])
    df_status.set_index('日期', inplace=True)

    # Combine all plots in a single figure
    plt.figure(figsize=(10, 15))

    # Plot for run_power
    plt.subplot(3, 1, 1)
    plt.plot(forecast_run_power['ds'], forecast_run_power['yhat'], label='Running Power Forecast', color='blue')
    plt.fill_between(forecast_run_power['ds'], forecast_run_power['yhat_lower'], forecast_run_power['yhat_upper'], color='skyblue', alpha=0.4)
    plt.scatter(df_run_power['ds'], df_run_power['y'], color='black', label='Running Power Actual', s=10)  # Adjust the size with the s parameter
    # plt.title('Running Power Forecast')
    plt.legend()

    ax1 = plt.gca().twinx()
    ax1.tick_params(axis='y', labelcolor='blue')  # 可以根据需要设置刻度的颜色等属性
    # df_status.plot(marker='o', linestyle='-', ax=ax1)  # 使用右侧轴

    # Plot for physical_power
    plt.subplot(3, 1, 2)
    plt.plot(forecast_physical_power['ds'], forecast_physical_power['yhat'], label='Physical Power Forecast', color='green')
    plt.fill_between(forecast_physical_power['ds'], forecast_physical_power['yhat_lower'], forecast_physical_power['yhat_upper'], color='lightgreen', alpha=0.4)
    plt.scatter(df_physical_power['ds'], df_physical_power['y'], color='orange', label='Physical Power Actual', s=10)  # Adjust the size with the s parameter
    # plt.title('Physical Power Forecast')
    plt.legend()

    # 创建右侧轴
    ax2 = plt.gca().twinx()
    ax2.tick_params(axis='y', labelcolor='green')  # 可以根据需要设置刻度的颜色等属性

    # Plot for the third data
    plt.subplot(3, 1, 3)
    plt.axhline(y=0, color='red', linestyle='--', linewidth=1)
    df_status.plot(marker='o', linestyle='-', ax=plt.gca())
    # df_status.plot(marker='o', linestyle='-', ax=ax2)
    # plt.title('Status')

    # 创建右侧轴
    ax3 = plt.gca().twinx()
    # 设置右侧轴的刻度位置
    ax3.tick_params(axis='y', labelcolor='black')  # 可以根据需要设置刻度的颜色等属性
    df_status.plot(marker='o', linestyle='-', ax=ax3)  # 使用右侧轴

    # Adjust layout and show the figure
    plt.tight_layout()
    plt.show()