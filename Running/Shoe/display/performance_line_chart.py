"""
================================================================================
统一数据库查询接口使用说明
================================================================================

本文件中的数据库查询逻辑已被提取到 Running/db_queries.py 中。

使用新接口的方式：
-----------------
from Running.db_queries import calculate_monthly_performance

# 计算指定月份的平均performance
start_date = '2025-01-01'
end_date = '2025-01-31'
avg_performance = calculate_monthly_performance(start_date, end_date)

print(f"月度平均performance: {avg_performance}")

优势：
-----
- 代码复用，避免重复逻辑
- 统一的接口，易于维护
- 清晰的函数名和文档

原始查询位置：第31-56行
================================================================================
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import datetime
import pandas as pd
import numpy as np
from sqlalchemy import text
from sqlalchemy.sql import exists
import csv
import matplotlib.pyplot as plt
from AutomatedFactorResearchSystem.util_date import get_month_list_by_start_end
from Running.Shoe.display.util import time_to_minutes
from Home.Running.Shoe.display.shoe_table import read_shoe_info_csv
from Running.running_models import engine_running, ShoeInfo, DailyShoeRecord, session, DailyShoeStats, \
    DailyRQRecord, DailyShoeStatsCurrentMonth
from Running.utils import time_to_second, second_to_time, pace1_to_pace2


def plot_performance_line_chart():
    today = datetime.date.today()

    start = "2023-12-26"
    month_list = get_month_list_by_start_end(start, today.strftime("%F"))
    performance_list = []
    for month in month_list:
        start_date = month + "-01"
        end_date = month + "-31"
        sql = text(
            f"select distance,used_time,average_heart_rate from `running_shoe_record` where date>='{start_date}' and date <= '{end_date}' ")
        # print(sql)
        result = session.execute(sql)

        mul_distance_performance = 0
        total_distance = 0
        for row in result:
            if row[1] == "0":
                continue
            distance = float(row[0])
            used_time = row[1]
            average_heart_rate = float(row[2])

            minutes = time_to_minutes(used_time)
            km_per_min = minutes / distance  # 就是pace1

            performance = (60 / km_per_min) / average_heart_rate * 100
            total_distance += distance
            mul_distance_performance += performance * distance
        if total_distance != 0:
            avg_performance = round(mul_distance_performance / total_distance, 2)
        else:
            avg_performance = 0
        # print(month, avg_performance)
        performance_list.append(avg_performance)

    df = pd.DataFrame(
        {
            "month": month_list,
            "avg_performance": performance_list
        }
    )
    df['delta'] = df['avg_performance'].diff()
    df = df.fillna(0)
    print(df)

    # 计算均值
    avg_performance_mean = df['avg_performance'].mean()
    delta_mean = df['delta'].mean()

    # 将'month'列转换为日期格式
    # df['month'] = pd.to_datetime(df['month'])
    # 排序DataFrame以确保按月份顺序绘制折线图
    # df = df.sort_values(by='month')

    # 设置纵坐标范围为0到10
    # plt.ylim(6, 8)
    # 绘制折线图
    # plt.plot(df['month'], df['avg_performance'], marker='o', label='avg_performance')
    # plt.plot(df['month'], df['delta'], marker='o', label='delta')
    # # 设置图形标题和轴标签
    # plt.title('Monthly Average Performance')
    # # plt.xlabel('Month')
    # plt.ylabel('Average Performance')
    #
    # # 旋转x轴标签，以避免重叠
    # plt.xticks(rotation=45)
    # plt.show()

    # 创建图形和主坐标轴
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # 绘制 avg_performance 的折线
    ax1.plot(df['month'], df['avg_performance'], marker='o', label='avg_performance', color='blue')
    ax1.set_xlabel('Month')
    ax1.set_ylabel('avg_performance', color='blue')
    ax1.set_ylim(6, 11)  # 设置左侧坐标轴的范围
    ax1.tick_params('y', colors='blue')  # 设置左侧坐标轴的颜色

    # 在左侧坐标轴上添加表示均值的蓝线
    ax1.axhline(y=avg_performance_mean, color='blue', linestyle='--', label='avg_performance mean')


    # 创建共享x轴的次坐标轴
    ax2 = ax1.twinx()

    # 绘制 delta 的折线
    ax2.plot(df['month'], df['delta'], marker='o', label='delta', color='red')
    ax2.set_ylabel('delta', color='red')
    ax2.set_ylim(-0.75, 0.75)  # 设置右侧坐标轴的范围
    ax2.tick_params('y', colors='red')  # 设置右侧坐标轴的颜色

    # 在右侧坐标轴上添加表示均值的红线
    ax2.axhline(y=delta_mean, color='red', linestyle='--', label='delta mean')

    # 添加标题
    plt.title('Performance Over Time')

    # 显示图例
    fig.tight_layout()
    plt.show()

if __name__ == '__main__':
    plot_performance_line_chart()

