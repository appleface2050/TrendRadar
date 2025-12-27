import pandas as pd
import matplotlib.pyplot as plt
from prophet import Prophet
import math
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Running.Shoe.display.util import time_to_minutes


def main():
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    records_csv = os.path.join(script_dir, '..', 'records.csv')

    df = pd.read_csv(records_csv)

    df = df.iloc[131:]

    df['minutes'] = df['used_time'].apply(time_to_minutes)
    df["km_per_min"] = df['minutes'] / df["distance"]           # 就是pace1 命名有问题，实际是 minutes per km

    df['pace_part1'] = df['km_per_min'].astype(int)

    # 使用 apply 和 math.modf 提取小数部分
    df['decimal_part'] = df['km_per_min'].apply(lambda x: math.modf(x)[0])
    df['pace_part2'] = (60 * df['decimal_part']).astype(int)
    df['pace_part2'] = df['pace_part2'].apply(lambda x: f'0{x}' if x < 10 else x)
    df['pace_part2'] = df['pace_part2'].astype(str)
    df['pace'] = df.apply(lambda row: f"{row['pace_part1']}:{row['pace_part2']}", axis=1)

    # df["pace"] = str(int(df["km_per_min"])) + ":" + str((df["km_per_min"] - int(df["km_per_min"])) * 60)
    # df["perfermance"] = df['pace'] / df["average_heart_rate"] / df["average_heart_rate"] * 10000
    # df["perfermance2"] = (60 / df['pace']) / df["average_heart_rate"] / df["average_heart_rate"] * 10000
    df["performance"] = round((60 / df['km_per_min']) / df["average_heart_rate"] * 100, 2)

    df = df.sort_values(by=["date"], ascending=True)

    df = df[["date", "distance", "average_heart_rate", "shoe", "type", "km_per_min", "pace", "performance"]]

    # print(df[["date", "distance", "average_heart_rate", "type", "pace", "performance"]])

    print(df[["date", "distance", "pace", "average_heart_rate", "performance", "shoe"]].tail(50))
    print(df[["distance", "average_heart_rate", "performance"]].describe())

    p_df = df.rename(columns={"date": "ds", "performance": "y"}, inplace=False)

    p = Prophet()
    p.fit(p_df)

    future_dataframe = p.make_future_dataframe(periods=30)
    forecast_performance = p.predict(future_dataframe)

    # print("forecast_performance: ", forecast_performance)

    # 将日期列转换为datetime类型
    df['date'] = pd.to_datetime(df['date'])

    # 按日期排序
    df = df.sort_values(by='date')

    # # 绘制折线图
    # plt.figure(figsize=(10, 6))
    # plt.plot(df['date'], df['performance'], marker='o', linestyle='-')
    #
    # # 添加标题和标签
    # plt.title('Performance Over Time')
    # plt.xlabel('Date')
    # plt.ylabel('Performance')
    #
    # # 旋转x轴刻度标签，以便更好地显示日期
    # plt.xticks(rotation=45)

    plt.plot(forecast_performance['ds'], forecast_performance['yhat'], label='Performance Forecast', color='blue')
    plt.fill_between(forecast_performance['ds'], forecast_performance['yhat_lower'], forecast_performance['yhat_upper'],
                     color='skyblue', alpha=0.4)
    plt.scatter(p_df['ds'], p_df['y'], color='black', label='Performance Actual',
                s=10)  # Adjust the size with the s parameter
    # plt.title('Running Power Forecast')
    plt.legend()

    # 显示图形
    plt.show()


if __name__ == '__main__':
    main()
