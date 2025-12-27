import warnings
import matplotlib.pyplot as plt
# 禁用所有警告
# from Home.Running.Shoe.display.performance import time_to_minutes
import os

warnings.filterwarnings('ignore')


import datetime
import math

import pandas as pd

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
rq_monthly_csv_path = os.path.join(script_dir, 'rq_monthly.csv')

def pace_to_km_per_min(pace):
    min = pace.split(":")[0]
    sec = pace.split(":")[1]
    km_per_min = int(min) + int(sec) / 60
    return km_per_min

def display_plot(df):
    # 将月份设为索引，并按月份排序
    df['month'] = pd.to_datetime(df['month'])
    df.set_index('month', inplace=True)
    df.sort_index(inplace=True)

    # 绘制折线图
    plt.figure(figsize=(10, 6))
    for column in df.columns:
        plt.plot(df.index, df[column], label=column)

    plt.title('Monthly Data')
    plt.xlabel('Month')
    plt.ylabel('Value')
    plt.legend()
    plt.show()

# Read the data
df = pd.read_csv(rq_monthly_csv_path)

df['km_per_min'] = df['pace'].apply(pace_to_km_per_min)       # 命名有问题，实际是 minutes per km
df["performance"] = round((60 / df['km_per_min']) / df["heart_rate"] * 100, 2)

df["speed"] = 1/df['km_per_min']*1000/60              #米/秒
df["stride_length"] = round(df['speed'] / (df['cadence'] / 60), 4)  # 线转换为步/秒
df = df[["month", "rq", "distance", "performance", "stride_length"]]

# df = df[["month", "rq", "performance", "stride_length"]]
# df = df[["month", "performance", "stride_length"]]



# df = df[["month",  "distance"]]

# df = df[["month",  "rq"]]
df = df[["month",  "performance"]]
# df = df[["month",  "stride_length"]]

# df = df[["month",  "rq", "performance"]]
# print(df)


display_plot(df)


