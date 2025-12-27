import datetime
import pandas as pd
import numpy
import os
import sys
import plotly.express as px
from pandasql import sqldf
import seaborn as sns
import matplotlib.pyplot as plt
import prettytable

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# sqldf(query, globals())
# meat = pd.read_csv('C:\\Users\\Shang\\.conda\\envs\\abc\\lib\\site-packages\\pandasql\\data\\meat.csv')
script_dir = os.path.dirname(os.path.abspath(__file__))
records = pd.read_csv(os.path.join(script_dir, '..', 'records.csv'))

pysqldf = lambda query: sqldf(query, globals())


csv_data_start_ = "2023-12-24"


def daily_trend_total_km_30_days():
    global records
    start = datetime.datetime.strptime(csv_data_start_, "%Y-%m-%d").date()
    today = datetime.date.today()
    # print(records)
    data = {}
    while start <= today:
        delta_30 = start - datetime.timedelta(days=30)
        sql = f"""
        SELECT sum(distance) FROM records where date>='{delta_30.strftime("%F")}' and date <= '{start.strftime("%F")}'
        """
        # print(sql)
        r = pysqldf(sql)
        daily_trend_total_km_30_days = r.loc[0][0]
        # print(start, round(daily_trend_total_km_30_days, 2))
        data[start.strftime("%F")] = round(daily_trend_total_km_30_days, 2)
        start += datetime.timedelta(days=1)

    # print(data)
    df = pd.DataFrame(list(data.items()), columns=['Date', 'Value'])
    df['Date'] = pd.to_datetime(df['Date'])

    # Set the style for seaborn
    sns.set(style="whitegrid")
    # sns.set_theme(style="darkgrid")

    # Create a line plot using Seaborn
    plt.figure(figsize=(12, 6))
    sns.lineplot(x='Date', y='Value', data=df, marker='o', color='blue', label='Value')

    # Set labels and title
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.title(sys._getframe().f_code.co_name)

    # Show the plot
    plt.show()

def daily_trend_total_km_90_days():
    global records
    start = datetime.datetime.strptime(csv_data_start_, "%Y-%m-%d").date()
    today = datetime.date.today()
    data = {}
    while start <= today:
        delta_ = start - datetime.timedelta(days=90)
        sql = f"""
        SELECT sum(distance) FROM records where date>='{delta_.strftime("%F")}' and date <= '{start.strftime("%F")}'
        """
        r = pysqldf(sql)
        result = r.loc[0][0]
        data[start.strftime("%F")] = round(result, 2)
        start += datetime.timedelta(days=1)

    # print(data)
    df = pd.DataFrame(list(data.items()), columns=['Date', 'Value'])
    df['Date'] = pd.to_datetime(df['Date'])

    # Set the style for seaborn
    sns.set(style="whitegrid")
    # sns.set_theme(style="darkgrid")

    # Create a line plot using Seaborn
    plt.figure(figsize=(12, 6))
    sns.lineplot(x='Date', y='Value', data=df, marker='o', color='blue', label='Value')

    # Set labels and title
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.title(sys._getframe().f_code.co_name)

    # Show the plot
    plt.show()


def get_daily_trend_total_km_30_days():
    global records
    start = datetime.datetime.strptime(csv_data_start_, "%Y-%m-%d").date()
    today = datetime.date.today()
    data = {}
    while start <= today:
        delta_30 = start - datetime.timedelta(days=30)
        sql = f"""
        SELECT sum(distance) FROM records where date>='{delta_30.strftime("%F")}' and date <= '{start.strftime("%F")}'
        """
        r = pysqldf(sql)
        # daily_trend_total_km_30_days = r.loc[0][0]
        daily_trend_total_km_30_days = r.iloc[0].tolist()[0]
        data[start.strftime("%F")] = round(daily_trend_total_km_30_days, 2)
        start += datetime.timedelta(days=1)
    return data

def get_daily_trend_total_km_90_days():
    global records
    start = datetime.datetime.strptime(csv_data_start_, "%Y-%m-%d").date()
    today = datetime.date.today()
    data = {}
    while start <= today:
        delta_ = start - datetime.timedelta(days=90)
        sql = f"""
        SELECT sum(distance)/3 FROM records where date>='{delta_.strftime("%F")}' and date <= '{start.strftime("%F")}'
        """
        r = pysqldf(sql)
        # result = r.loc[0][0]
        result = r.iloc[0].tolist()[0]
        data[start.strftime("%F")] = round(result, 2)
        start += datetime.timedelta(days=1)

    return data

def get_total_km():
    global records
    start = datetime.datetime.strptime(csv_data_start_, "%Y-%m-%d").date()
    today = datetime.date.today()
    data = {}
    while start <= today:
        sql = f"""
        SELECT sum(distance) FROM records where date <= '{start.strftime("%F")}'
        """
        r = pysqldf(sql)
        result = r.loc[0][0]
        data[start.strftime("%F")] = round(result, 2)
        start += datetime.timedelta(days=1)
    return data

def get_remaining_km():
    pass

def main():
    # 最近30日跑量
    daily_trend_total_km_30_days()

    # 最近90日跑量
    daily_trend_total_km_90_days()

def recent_used_distance_plotly():
    data_30_days = get_daily_trend_total_km_30_days()
    data_90_days = get_daily_trend_total_km_90_days()
    # total_km = get_total_km()
    # remaining_km = get_remaining_km()

    # print(data_30_days)
    # print(data_90_days)
    # print(total_km)

    # 将字典转换为DataFrame
    df_30_days = pd.DataFrame(list(data_30_days.items()), columns=['Date', 'total_distance_30_days'])
    df_90_days = pd.DataFrame(list(data_90_days.items()), columns=['Date', 'total_distance_90_days'])
    # df_total_km = pd.DataFrame(list(total_km.items()), columns=['Date', 'total_km'])

    # 将两个DataFrame合并
    merged_df = pd.merge(df_30_days, df_90_days, on='Date', how='outer')
    # merged_df = pd.merge(merged_df, df_total_km, on='Date', how='outer')

    fig = px.line(merged_df, x='Date', y=["total_distance_30_days", "total_distance_90_days"], title='recent used distance')
    fig.show()

def recent_used_distance():
    data_30_days = get_daily_trend_total_km_30_days()
    data_90_days = get_daily_trend_total_km_90_days()
    # total_km = get_total_km()
    # remaining_km = get_remaining_km()

    # print(data_30_days)
    # print(data_90_days)
    # print(total_km)

    # 将字典转换为DataFrame
    df_30_days = pd.DataFrame(list(data_30_days.items()), columns=['Date', 'total_distance_30_days'])
    df_90_days = pd.DataFrame(list(data_90_days.items()), columns=['Date', 'total_distance_90_days'])
    # df_total_km = pd.DataFrame(list(total_km.items()), columns=['Date', 'total_km'])

    # 将两个DataFrame合并
    merged_df = pd.merge(df_30_days, df_90_days, on='Date', how='outer')
    # merged_df = pd.merge(merged_df, df_total_km, on='Date', how='outer')

    # 使用seaborn画折线图
    plt.figure(figsize=(12, 6))
    sns.lineplot(x='Date', y='total_distance_30_days', data=merged_df, label='total_distance_30_days')
    sns.lineplot(x='Date', y='total_distance_90_days', data=merged_df, label='total_distance_90_days')
    # sns.lineplot(x='Date', y='total_km', data=merged_df, label='total_km')

    # 设置图表标题和标签
    plt.title('Distance Comparison Over Time')
    plt.xlabel('Date')
    plt.ylabel('Distance')

    # 显示图例
    plt.legend()

    # 旋转x轴刻度标签，使其更易读
    plt.xticks(rotation=45)

    # 显示图表
    plt.show()

def total_km_vs_remaining_km():
    total_km = get_total_km()
    remaining_km = get_remaining_km()

    print(total_km)

    # 将字典转换为DataFrame
    # df_30_days = pd.DataFrame(list(data_30_days.items()), columns=['Date', 'total_distance_30_days'])
    # df_90_days = pd.DataFrame(list(data_90_days.items()), columns=['Date', 'total_distance_90_days'])
    df_total_km = pd.DataFrame(list(total_km.items()), columns=['Date', 'total_km'])

    # 将两个DataFrame合并
    merged_df = pd.merge(df_30_days, df_90_days, on='Date', how='outer')
    merged_df = pd.merge(merged_df, df_total_km, on='Date', how='outer')

    # 使用seaborn画折线图
    plt.figure(figsize=(12, 6))
    sns.lineplot(x='Date', y='total_distance_30_days', data=merged_df, label='total_distance_30_days')
    sns.lineplot(x='Date', y='total_distance_90_days', data=merged_df, label='total_distance_90_days')
    # sns.lineplot(x='Date', y='total_km', data=merged_df, label='total_km')

    # 设置图表标题和标签
    plt.title('Distance Comparison Over Time')
    plt.xlabel('Date')
    plt.ylabel('Distance')

    # 显示图例
    plt.legend()

    # 旋转x轴刻度标签，使其更易读
    plt.xticks(rotation=45)

    # 显示图表
    plt.show()

if __name__ == '__main__':
    now = datetime.datetime.now()
    # main()
    # recent_used_distance()
    # total_km_vs_remaining_km()
    recent_used_distance_plotly()

    print(datetime.datetime.now() - now)