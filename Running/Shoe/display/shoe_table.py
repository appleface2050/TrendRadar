"""
================================================================================
统一数据库查询接口使用说明
================================================================================

本文件中的数据库查询逻辑已被提取到 Running/db_queries.py 中。

使用新接口的方式：
-----------------
from Running.db_queries import (
    get_monthly_shoe_performance_stats,
    get_today_all_ranks,
    get_current_month_performance_detail,
    get_today_date
)

# 示例1: 获取月度跑鞋性能统计
month_stats = get_monthly_shoe_performance_stats('2025-01', 'month')

# 示例2: 获取今日所有排名
today = get_today_date()
sum_rank, rank_details = get_today_all_ranks(today)

# 示例3: 获取当月详细统计
month_detail = get_current_month_performance_detail('2025-01')

优势：
-----
- 代码复用，避免重复逻辑
- 统一的接口，易于维护
- 清晰的函数名和文档

主要查询位置：
--------------
- cal_performance_of_the_month_or_history(): 第144-152行
- handle_performance_of_history_detail(): 第988-1090行
- show_performance_of_the_month_per_month(): 第906-914行
================================================================================
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import warnings

from Running.Shoe.display.util import time_to_minutes
from Running.running_models import engine_running, ShoeInfo, DailyShoeRecord, session, DailyShoeStats, \
    DailyRQRecord

warnings.filterwarnings('ignore')

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import matplotlib.pyplot as plt
import numpy as np
import math
import csv
import pandas as pd
import datetime
import statistics
import mplcursors
from matplotlib.font_manager import FontProperties
from collections import defaultdict
from prettytable import PrettyTable
from sqlalchemy import text
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly


def read_run_records_csv():
    shoe_name_list = list(read_shoe_info_csv().keys())

    df = pd.read_csv('C:\git\Quant\Home\Running\Shoe\\records.csv')
    df = df.sort_values(by='date', ascending=False)
    record = {}
    # Read CSV data from the file
    dict_data = df.to_dict(orient='records')
    for shoe_name in shoe_name_list:
        shoe_record_list = []
        for r in dict_data:
            if r["shoe"] == shoe_name:
                shoe_record_list.append(r)
        record[shoe_name] = shoe_record_list

    # Print the resulting dictionary
    return record


def read_shoe_info_csv():
    # Parse CSV data and populate the dictionary
    # Specify the path to your CSV file
    csv_file_path = 'C:\git\Quant\Home\Running\Shoe\shoe_info.csv'
    shoe_info = {}
    # Read CSV data from the file
    with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
        # Parse CSV data and populate the dictionary
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            name = row['name']
            brand = row['brand']
            price = int(row['price'])
            color = row['color']
            start_date = row['start_date']
            end_date = row['end_date']
            sold_price = row['sold_price']
            shortage = row['shortage']

            # Populate the shoe_info dictionary
            shoe_info[name] = {
                'price': price,
                'color': color,
                'start_date': start_date,
                'end_date': end_date,
                'brand': brand,
                'sold_price': sold_price,
                'shortage': shortage,
            }
    # Print the resulting dictionary
    return shoe_info


def fangcheng(a, b, c):
    if (b * b - 4 * a * c) < 0:
        # print("此方程无解！")
        raise Exception("此方程无解！")
    elif (b * b - 4 * a * c) == 0:
        # print('此方程有一个解！')
        return (0 - b + math.sqrt(b * b - 4 * a * c)) / 2 * a
    else:
        # print('此方程有两个解！')
        return (0 - b + math.sqrt(b * b - 4 * a * c)) / 2 * a, (0 - b - math.sqrt(b * b - 4 * a * c)) / 2 * a


def convert_daily_to_monthly(records):
    monthly_records = defaultdict(dict)

    for shoe_name, data in records.items():
        for date, distance in data.items():
            year_month = date[:7]  # Extract the year and month
            monthly_records[shoe_name][year_month] = monthly_records[shoe_name].get(year_month, 0) + distance

    return dict(monthly_records)


def convert_daily_to_monthly_v2():
    shoe_info = read_shoe_info_csv()
    record_v2 = read_run_records_csv()
    shoe_names = list(shoe_info.keys())
    # tmp_list = [record_v2.get(shoe) for shoe in shoe_names if record_v2.get(shoe)]
    # print(tmp_list)

    monthly_records = defaultdict(dict)
    for shoe in shoe_names:
        shoe_result_dict = {}
        shoe_record_list = record_v2.get(shoe)
        for shoe_record in shoe_record_list:
            year_month = shoe_record["date"][:7]
            if year_month in list(shoe_result_dict.keys()):
                shoe_result_dict[year_month] += shoe_record["distance"]
            else:
                shoe_result_dict[year_month] = shoe_record["distance"]
        monthly_records[shoe] = shoe_result_dict
    return monthly_records


def cal_performance_of_the_month_or_history(shoe_names, months_for_performance_of_the_month, type):
    if type == "month":
        table_name = "running_daily_shoe_stats_current_month"
    elif type == "history":
        table_name = "running_daily_shoe_stats"
    else:
        raise Exception("type error")

    performance_of_the_month_per_month = {}
    for month in months_for_performance_of_the_month:
        start_date = month + "-01"
        end_date = month + "-31"
        sql = text(
            f"""
            SELECT shoe,MAX(rq_inc1) AS rq_inc1,Min(top1_pace) AS top1_pace,MAX(top1_performance) AS top1_performance, MAX(rq1) AS rq
            FROM `{table_name}` 
            WHERE DATE>= '{start_date}' AND DATE<= '{end_date}' AND top1_pace != '00:00'
            GROUP BY shoe
            ORDER BY MAX(rq_inc1) DESC
            """
        )
        # print(sql)
        result = session.execute(sql)
        data = {}
        for row in result:
            rq_inc1 = row[1]
            if rq_inc1 == "":
                rq_inc1 = "0"
            rq = row[4]
            if rq == "":
                rq = "0"
            data[row[0]] = {"rq_inc1": rq_inc1, "top1_pace": row[2], "top1_performance": row[3], "rq": rq}
        # print(data)

        # 计算百分位
        # 将字典转换为列表
        shoes_scores_rq_inc1 = [(name, float(score["rq_inc1"])) for name, score in data.items() if
                                float(score["rq_inc1"]) > 0.0]
        # 按照分数从高到低排序，并处理相同分数的情况
        sorted_shoes_rq_inc1 = sorted(shoes_scores_rq_inc1, key=lambda x: (x[1], x[0]), reverse=True)
        # 计算排名并输出结果
        ranked_rq_inc1 = [(name, rank + 1) for rank, (name, _) in enumerate(sorted_shoes_rq_inc1)]
        ranked_rq_inc1 = dict(ranked_rq_inc1)
        # print("ranked_rq_inc1:", ranked_rq_inc1)

        shoes_scores_top1_pace = [(name, score["top1_pace"]) for name, score in data.items() if
                                  score["top1_pace"] != "00:00"]
        # 按照分数从高到低排序，并处理相同分数的情况
        sorted_shoes_top1_pace = sorted(shoes_scores_top1_pace, key=lambda x: (x[1], x[0]), reverse=False)
        # 计算排名并输出结果

        ranked_top1_pace = [(name, rank + 1) for rank, (name, _) in enumerate(sorted_shoes_top1_pace)]
        ranked_top1_pace = dict(ranked_top1_pace)
        # print("ranked_top1_pace:", ranked_top1_pace)

        shoes_scores_top1_performance = [(name, float(score["top1_performance"])) for name, score in data.items() if
                                         float(score["top1_performance"]) > 0]
        sorted_shoes_top1_performance = sorted(shoes_scores_top1_performance, key=lambda x: (x[1], x[0]), reverse=True)
        ranked_top1_performance = [(name, rank + 1) for rank, (name, _) in enumerate(sorted_shoes_top1_performance)]
        ranked_top1_performance = dict(ranked_top1_performance)
        # print("ranked_top1_performance:", ranked_top1_performance)

        shoes_scores_rq = [(name, float(score["rq"])) for name, score in data.items() if
                           float(score["rq"]) > 0]
        sorted_shoes_rq = sorted(shoes_scores_rq, key=lambda x: (x[1], x[0]), reverse=True)
        ranked_top1_rq = [(name, rank + 1) for rank, (name, _) in enumerate(sorted_shoes_rq)]
        ranked_top1_rq = dict(ranked_top1_rq)

        sum_rank = {}

        for shoe in shoe_names:
            sum_rank[shoe] = 1.25 * ranked_rq_inc1.get(shoe, len(shoe_names)) \
                             + ranked_top1_pace.get(shoe, len(shoe_names)) \
                             + 1.2 * ranked_top1_performance.get(shoe, len(shoe_names)) \
                             + ranked_top1_rq.get(shoe, len(shoe_names))
        # print("sum_rank:", sum_rank)
        sum_rank_sorted = sorted(sum_rank.items(), key=lambda x: x[1], reverse=False)
        # print("sum_rank_sorted:", sum_rank_sorted)
        performance_of_the_month_per_month[month] = sum_rank_sorted

    performance_of_the_month_per_shoe_count = {}
    for month in months_for_performance_of_the_month:
        shoe = performance_of_the_month_per_month[month][0][0]
        if performance_of_the_month_per_shoe_count.get(shoe) is None:
            performance_of_the_month_per_shoe_count[shoe] = 1
        else:
            performance_of_the_month_per_shoe_count[shoe] += 1
    rank_detail = [ranked_rq_inc1, ranked_top1_pace, ranked_top1_performance, ranked_top1_rq]
    return performance_of_the_month_per_shoe_count, performance_of_the_month_per_month, rank_detail


def plot4(records):
    # Extracting data from the records dictionary
    shoe_names = list(records.keys())

    shoe_info = read_shoe_info_csv()
    months = sorted(set(month for data in records.values() for month in data.keys()))

    # Extracting the corresponding values for each shoe and each month
    values = np.zeros((len(shoe_names), len(months)))

    for i, shoe_name in enumerate(shoe_names):
        data = records[shoe_name]
        values[i, :] = [data.get(month, 0) for month in months]

    # Plotting the data as a stacked bar chart
    plt.figure(figsize=(12, 8))

    bottoms = np.zeros(len(months))
    total_mileages = []  # To store the total mileage for each shoe

    for i in range(len(shoe_names)):
        price = shoe_info[shoe_names[i]]["price"]
        color = shoe_info[shoe_names[i]]["color"]
        plt.bar(months, values[i, :], bottom=bottoms, color=color,  # shoe_colors[i],
                label=f'{shoe_names[i]} '
                # f'{np.sum(values[i, :]):.2f} km'
                )

        # Annotating each non-zero segment with the corresponding distance value
        for j, value in enumerate(values[i, :]):
            if value != 0:
                plt.annotate(f'{value:.2f}', xy=(months[j], bottoms[j] + value / 2),
                             ha='center', va='center', fontsize=8)

        bottoms += values[i, :]
        total_mileages.append(np.sum(values[i, :]))

    # Adding labels and title
    plt.xlabel('Month-Year')
    plt.ylabel('Distance (in km)')
    plt.title('Distance Covered Each Month for Different Shoes')
    plt.xticks(rotation=45)
    font = FontProperties(fname=r'C:\Windows\Fonts\SimHei.ttf', size=12)
    plt.legend(prop=font, ncol=2)

    # Display the plot
    plt.tight_layout()
    plt.show()


def cal_table_result():
    shoe_info = read_shoe_info_csv()
    # shoe_names = list(records.keys())
    shoe_names = list(shoe_info.keys())
    # months = sorted(set(month for data in records.values() for month in data.keys()))

    record_v2 = read_run_records_csv()

    tmp_list = [record_v2.get(shoe) for shoe in shoe_names if record_v2.get(shoe)]
    month_list = []

    for tmp in tmp_list:
        for obj in tmp:
            dt = obj["date"]
            month_list.append(dt[:7])
    months = sorted(list(set(month_list)))

    # Extracting the corresponding values for each shoe and each month
    values = np.zeros((len(shoe_names), len(months)))

    for i, shoe_name in enumerate(shoe_names):
        data = record_v2[shoe_name]
        # values[i, :] = [data.get(month, 0) for month in months]
        # values[i, :] = [ for r_dict in data for month in months]

        values_list = []
        for month in months:
            month_km = 0
            for r_dict in data:
                if r_dict["date"][:7] == month:
                    month_km += r_dict["distance"]
            values_list.append(month_km)
        values[i, :] = values_list

    # for i, shoe_name in enumerate(shoe_names):
    #     data = records[shoe_name]
    #     values[i, :] = [data.get(month, 0) for month in months]

    result = []

    # 期望每公里钱数
    # expected_unit_price = 0.8

    monthly_result = convert_daily_to_monthly_v2()

    shoe_of_the_month, shoe_of_the_month_per_month = cal_shoe_of_the_month(shoe_names, months, monthly_result)
    # total_30_days_used_km = 0
    # total_90_days_used_km = 0
    # remaining_km = 0
    #
    # for i in range(len(shoe_names)):
    #     shoe_name = shoe_names[i]
    #     total_30_days_used_km += shoe["_30_days_used_km"]
    #     total_90_days_used_km += shoe["_90_days_used_km"]
    #     remaining_km += shoe["remaining_km"]

    today = datetime.date.today()
    # 最近30日消耗量
    # 最近30日活动次数
    _30_day = today - datetime.timedelta(days=30)
    _90_day = today - datetime.timedelta(days=90)
    total_30_days_used_km = 0
    total_90_days_used_km = 0

    for k, v in record_v2.items():
        for r in v:
            if r["date"] >= _30_day.strftime("%F"):
                total_30_days_used_km += r["distance"]
            if r["date"] >= _90_day.strftime("%F"):
                total_90_days_used_km += r["distance"]

    # performance of the history
    months_for_performance_of_the_month = [m for m in months if m >= "2024-02"]
    # performance_of_the_month_per_shoe_count, performance_of_the_month_per_month, rank_detail = cal_performance_of_the_month_or_history(
    #     shoe_names,
    #     months_for_performance_of_the_month, "history")

    # performance_of_the_month_per_shoe_count, performance_of_the_month_per_month, rank_detail = cal_performance_of_the_month_or_history(
    #     shoe_names,
    #     months_for_performance_of_the_month, "history")

    for i in range(len(shoe_names)):
        shoe_name = shoe_names[i]
        end_date = shoe_info[shoe_names[i]]["end_date"]

        df = pd.DataFrame(list(monthly_result[shoe_name].items()), columns=['date', 'distance'])
        df = df.sort_values(by='date', ascending=True)
        df.rename(columns={"date": "ds", "distance": "y"}, inplace=True)
        # print(df)

        if end_date:
            next_month_forecast_km = 0
        else:

            if df.shape[0] <= 1:
                next_month_forecast_km = df["y"][0]
            else:
                next_month_forecast_km = predict_next_value_LinearRegression(df)
            next_month_forecast_km = next_month_forecast_km
            # print(shoe_name, int(next_month_forecast_km))

        next_month_forecast_km = round(next_month_forecast_km, 1)

        used_km = round(np.sum(values[i, :]), 1)
        # price = shoe_prices[shoe_names[i]]
        price = shoe_info[shoe_names[i]]["price"]
        sold_price = shoe_info[shoe_names[i]]["sold_price"]
        if sold_price == "":
            sold_price = 0
        else:
            sold_price = float(sold_price)
        net_price = round(price - sold_price, 2)
        unit_price = round(((price - sold_price) / used_km), 2)
        expected_km = int(price / 0.8)
        marginal_km = round(price / (price / used_km - 0.1) - used_km, 2)  # unit price降低0.1需要的公里数

        # marginal_unit_price 变为100需要的公里数
        # total_km**2 + 100total_km -1000price = 0 计算一元二次方程
        r = fangcheng(1, 100, -1000 * price)
        # print(r)
        expected_total_km = int(r[0])
        if not end_date:
            remaining_km = expected_total_km - used_km
            if remaining_km < 0:
                remaining_km = 0
        else:
            remaining_km = 0
        expected_unit_price = round(price / r[0], 2)
        # marginal_unit_price_100_km = str(
        #     marginal_unit_price_100_km) + " (%s)" % marginal_unit_price_100_km_unit_price

        progress = round(used_km / expected_total_km, 2)

        today = datetime.date.today()
        # 最近30日消耗量
        # 最近30日活动次数
        _30_day = today - datetime.timedelta(days=30)
        _30_days_used_km = 0
        _30_days_activity = 0
        for r in record_v2.get(shoe_name):
            if r["date"] >= _30_day.strftime("%F"):
                _30_days_used_km += r["distance"]
                _30_days_activity += 1
        _30_days_used_km = round(_30_days_used_km, 2)

        # 最近90日消耗量
        _90_day = today - datetime.timedelta(days=90)
        _90_days_used_km = 0
        _90_days_activity = 0
        for r in record_v2.get(shoe_name):
            if r["date"] >= _90_day.strftime("%F"):
                _90_days_used_km += r["distance"]
                _90_days_activity += 1
        _90_days_used_km = round(_90_days_used_km, 2)

        # 最近180日消耗量
        _180_day = today - datetime.timedelta(days=180)
        _180_days_used_km = 0
        _180_days_activity = 0
        for r in record_v2.get(shoe_name):
            if r["date"] >= _180_day.strftime("%F"):
                _180_days_used_km += r["distance"]
                _180_days_activity += 1
        _180_days_used_km = round(_180_days_used_km, 2)

        # 最近360日消耗量
        _360_days = today - datetime.timedelta(days=360)
        _360_days_used_km = 0
        for r in record_v2.get(shoe_name):
            if r["date"] >= _360_days.strftime("%F"):
                _360_days_used_km += r["distance"]
        _360_days_used_km = round(_360_days_used_km, 2)

        # 30d 90d pct
        _30d_km_pct = round(_30_days_used_km / total_30_days_used_km * 100, 1)
        _90d_km_pct = round(_90_days_used_km / total_90_days_used_km * 100, 1)
        # print(shoe_name, _30_days_used_km, total_30_days_used_km)

        # print(_30_days_used_km, _90_days_used_km, _180_days_used_km, _360_days_used_km, used_km)

        # 是否退役
        # 服役月数
        # earliest_day =
        # for r in record_v2.get(shoe_name):
        #     if not earliest_day:
        #         earliest_day = r["date"]
        #     else:
        #         if r["date"] < earliest_day:
        #             earliest_day = r["date"]
        start_date = shoe_info.get(shoe_name)["start_date"]
        end_date = shoe_info.get(shoe_name)["end_date"]

        # earliest_day = datetime.datetime.strptime(earliest_day, "%Y-%m-%d").date()
        if not end_date:
            used_months = round((today - datetime.datetime.strptime(start_date, "%Y-%m-%d").date()).days / 30, 2)
        else:
            used_months = round((datetime.datetime.strptime(end_date, "%Y-%m-%d").date() - datetime.datetime.strptime(
                start_date, "%Y-%m-%d").date()).days / 30, 2)

        if used_months == 0:
            used_months = 0.03
        # print(used_months)
        # 服役期间评价每月消耗量
        used_km_per_month = round(used_km / used_months, 2)

        # 预计达到marginal_unit_price_100_km到还有多少个月

        # 单个鞋子数据
        # 单个鞋子的使用柱状图
        # 距离上次使用的天数

        # score180评分最近1个月 3个月 6个月使用里程加权与Total KM(E)的比值
        # if _90_days_used_km == 0:
        #     score180 = (_30_days_used_km + 3 + _30_days_used_km * 2 + _30_days_used_km * 1) / 500
        # elif _180_days_used_km == 0:
        #     score180 = (_30_days_used_km + 3 + _90_days_used_km * 2 + _90_days_used_km * 1) / 500
        # else:
        #     score180 = (_30_days_used_km + 3 + _90_days_used_km * 2 + _180_days_used_km * 1) / 500
        dynamic_popularity = _30_days_used_km + _90_days_used_km + _180_days_used_km + _360_days_used_km + used_km
        dynamic_popularity = int(dynamic_popularity)
        # print(dynamic_popularity)

        # Expected Retire Date 30日跑量，未来跑完的日期

        days = 0
        # if shoe_name == "adidas adizero Boston 12":
        #     print(shoe_name)
        if not end_date:
            today = datetime.date.today()
            pass_days = (today - datetime.datetime.strptime(start_date, "%Y-%m-%d").date()).days
            if pass_days < 90:
                days = int((expected_total_km - used_km) / (used_km / pass_days))
            else:
                if _90_days_used_km:
                    days = int((expected_total_km - used_km) / (_90_days_used_km / 90))
        if days <= 0:
            days = 0

        if days:
            expected_retire_date = (datetime.datetime.today() + datetime.timedelta(days=days)).strftime("%F")
        else:
            expected_retire_date = ""
        # print(shoe_name, days, expected_retire_date)

        # performance 分析，每次performance按公里数加权平均
        shoe_record_list = record_v2[shoe_name]
        performance = cal_performance_by_shoe_record_list(shoe_record_list)
        # print(performance)

        # shoe of the month
        count_shoe_of_the_month = shoe_of_the_month.get(shoe_name)

        performance_of_the_month_per_shoe_count_, _, _2 = cal_performance_of_the_month_or_history(
            shoe_names,
            months_for_performance_of_the_month, "month")
        count_performance_of_the_month = performance_of_the_month_per_shoe_count_.get(shoe_name, 0)

        result.append({
            "shoe_name": shoe_name, "total_km": used_km, "price": price, "unit_price": unit_price,
            "sold_price": sold_price,
            "net_price": net_price,
            "expected_km": expected_km,
            "marginal_km": marginal_km,
            "expected_total_km": expected_total_km,
            "expected_unit_price": expected_unit_price,
            "progress": progress,
            "_30_days_used_km": _30_days_used_km,
            "_90_days_used_km": _90_days_used_km,
            "_30_days_prog": round(_30_days_used_km / expected_total_km * 100, 2),
            "_90_days_prog": round(_90_days_used_km / expected_total_km * 100, 2),
            "_90_days_activity": _90_days_activity,
            "used_km_per_month": used_km_per_month,
            "dynamic_popularity": dynamic_popularity,
            "next_month_forecast_km": next_month_forecast_km,
            "remaining_km": remaining_km,
            "_30d_km_pct": _30d_km_pct,
            "_90d_km_pct": _90d_km_pct,
            "expected_retire_date": expected_retire_date,
            "performance": performance,
            "count_shoe_of_the_month": count_shoe_of_the_month,
            "count_performance_of_the_month": count_performance_of_the_month,
            "end_date": end_date,
        })
        # print(shoe_name, price, expected_km)
    # print(result)

    # 排序
    result = sorted(result, key=lambda x: x['_30_days_used_km'], reverse=True)

    return result


def cal_shoe_of_the_month(shoe_names, month_list, monthly_result):
    shoe_of_the_month = {}
    shoe_of_the_month_per_month = []
    for shoe in shoe_names:
        shoe_of_the_month[shoe] = 0

    for month in month_list:
        # print(month)
        board_dict = {}
        for shoe in shoe_names:
            distance = monthly_result[shoe].get(month, 0)
            board_dict[shoe] = distance
        # print(board_dict)
        max_distance = max(board_dict.values())
        # max_distance = round(max_distance, 2)
        # max_distance_shoe = max(board_dict, key=board_dict.get)
        for shoe in shoe_names:
            if board_dict[shoe] == max_distance:
                # shoe_of_the_month_list.append(shoe)
                # print(month, shoe)
                shoe_of_the_month_per_month.append((month, shoe, round(max_distance, 2)))
                shoe_of_the_month[shoe] += 1
        # print(month, shoe_of_the_month_list)
    return shoe_of_the_month, shoe_of_the_month_per_month


def cal_performance_by_shoe_record_list(shoe_record_list):
    # performance = 0
    p_list = []
    for record in shoe_record_list:
        # print(record)
        average_heart_rate = record["average_heart_rate"]
        if not average_heart_rate:
            continue
        used_time = record["used_time"]
        minutes = time_to_minutes(used_time)
        km_per_min = minutes / record["distance"]

        p = 60 / km_per_min / average_heart_rate * 100
        p_list.append({"p": p, "distance": record["distance"]})

    weighted_sum = 0
    distance_sum = 0

    for item in p_list:
        weighted_sum += item['p'] * item['distance']
        distance_sum += item['distance']

    if p_list:
        performance = weighted_sum / distance_sum
        performance = round(performance, 2)
    else:
        performance = 0
    return performance


def cal_shoes_stats(result):
    # result = cal_table_result()
    # print(result)

    table = PrettyTable()
    table.field_names = ["No.",
                         "Shoe Name",
                         "Used KM",
                         "Price",
                         # "Net Price",
                         "Unit Price",
                         # "Expected Total KM(0.8/km)",
                         # "Marginal KM",
                         "Target KM",
                         # "Unit Price(E)",
                         "Progress",
                         "30d KM",
                         "90d KM",
                         # "30d Prog",
                         # "90d Prog",
                         # "90d RUN",
                         # "KM/month",
                         # "DP",
                         "30d KM %",
                         "90d KM %",
                         # "Forecast KM",
                         "Performance",
                         "ERD",
                         "SOTM",  # count_shoe_of_the_month
                         "POTM",  # count_performance_of_the_month
                         ]
    count = 1
    for entry in result:
        # print(entry)
        table.add_row(
            [
                count,
                entry['shoe_name'],
                entry['total_km'],
                entry['price'],
                # entry['net_price'],
                entry['unit_price'],
                # entry['expected_km'],
                # entry['marginal_km'],
                entry["expected_total_km"],
                # entry["expected_unit_price"],
                entry["progress"],
                # entry["_90_days_activity"],
                entry["_30_days_used_km"],
                entry["_90_days_used_km"],
                # entry["_30_days_prog"],
                # entry["_90_days_prog"],
                # entry["used_km_per_month"],
                # entry["dynamic_popularity"],

                entry["_30d_km_pct"],
                entry["_90d_km_pct"],
                # entry["next_month_forecast_km"],

                entry["performance"],
                entry["expected_retire_date"],
                entry["count_shoe_of_the_month"],
                entry["count_performance_of_the_month"],
            ])
        count += 1
    print("Shoe Stats:")
    print(table)


def cal_brand_stats(result):
    brand_stats = {}
    # brand_stats_list = []
    # result = cal_table_result()
    # print(result)
    # brand_list = []

    shoe_info_dict = read_shoe_info_csv()
    brand_list = [shoe_info_dict[i]["brand"] for i in shoe_info_dict.keys()]

    # for shoe in result:
    #     brand = shoe["shoe_name"].split(" ")[0]
    #     if brand not in brand_list:
    #         brand_list.append(brand)
    for brand in brand_list:
        brand_stats[brand] = {"brand": brand, "total_km": 0, "total_price": 0, "dynamic_popularity": 0, "count": 0,
                              "avg_total_km": 0, "avg_dynamic_popularity": 0, "_90_days_activity": 0,
                              "remaining_km": 0,
                              "_30_days_used_km": 0, "_90_days_used_km": 0, 'count_shoe_of_the_month': 0,
                              'count_performance_of_the_month': 0}

    # print(brand_stats)
    remaining_km = 0

    total_30_days_used_km = 0
    total_90_days_used_km = 0
    for shoe in result:
        total_30_days_used_km += shoe["_30_days_used_km"]
        total_90_days_used_km += shoe["_90_days_used_km"]
        remaining_km += shoe["remaining_km"]

    total_km = 164.6
    total_expense = 0
    total_count = 0
    total_sold = 0
    total_dynamic_popularity = 0
    price_list = []

    shoe_remain_count = 0  # 现役sheo

    for shoe in result:
        # brand = shoe["shoe_name"].split(" ")[0]
        brand = shoe_info_dict[shoe["shoe_name"]]["brand"]
        if shoe["end_date"] == "":
            shoe_remain_count += 1

        total_km += shoe["total_km"]
        total_expense += shoe["price"]
        total_sold += shoe["sold_price"]
        total_count += 1

        total_dynamic_popularity += shoe["dynamic_popularity"]
        price_list.append(shoe["price"])

        brand_dict = brand_stats[brand]
        brand_dict["remaining_km"] += shoe["remaining_km"]
        brand_dict["total_km"] += shoe["total_km"]
        brand_dict["total_price"] += shoe["price"]
        brand_dict["dynamic_popularity"] += shoe["dynamic_popularity"]
        brand_dict["count"] += 1
        brand_dict["_90_days_activity"] += shoe["_90_days_activity"]
        brand_dict["_30_days_used_km"] += shoe["_30_days_used_km"]
        # print(shoe["_90_days_used_km"])
        brand_dict["_90_days_used_km"] += shoe["_90_days_used_km"]
        # total_30_days_used_km += shoe["_30_days_used_km"]
        brand_dict["_30_days_used_km_pct"] = brand_dict["_30_days_used_km"] / total_30_days_used_km * 100
        brand_dict["_90_days_used_km_pct"] = brand_dict["_90_days_used_km"] / total_90_days_used_km * 100
        brand_dict["avg_total_km"] = round(brand_dict["total_km"] / brand_dict["count"], 2)
        brand_dict["avg_dynamic_popularity"] = round(brand_dict["dynamic_popularity"] / brand_dict["count"], 2)
        brand_dict["avg_total_price"] = int(brand_dict["total_price"] / brand_dict["count"])
        brand_dict['count_shoe_of_the_month'] += shoe["count_shoe_of_the_month"]
        brand_dict['count_performance_of_the_month'] += shoe.get("count_performance_of_the_month", 0)

    # print(brand_stats)
    brand_stats_list = list(brand_stats.values())
    brand_stats_list = sorted(brand_stats_list, key=lambda x: x['_30_days_used_km'], reverse=True)
    # print(brand_stats_list)

    table = PrettyTable()
    table.field_names = ["No.", "Brand", "Count", "Total Expense", "AVG Expense", "Total Used KM", "Unit Price",
                         "Remaining KM",
                         "AVG KM",
                         # "DP",
                         # "AVG DP",
                         # "90D RUN",
                         "30D KM", "30D KM (%)",  # "90D KM (%)",
                         "SOTM", "POTM",
                         ]
    count = 1
    for entry in brand_stats_list:
        table.add_row(
            [count, entry['brand'], entry['count'], entry['total_price'], entry['avg_total_price'],
             # entry['expected_km'],
             round(entry['total_km'], 2),
             round(entry['total_price'] / entry['total_km'], 2),
             round(entry['remaining_km'], 2),
             entry["avg_total_km"],
             # entry["dynamic_popularity"], entry["avg_dynamic_popularity"],
             # entry["_90_days_activity"],
             round(entry["_30_days_used_km"], 2), round(entry["_30_days_used_km_pct"], 1),
             # round(entry["_90_days_used_km_pct"], 1),
             entry["count_shoe_of_the_month"],
             entry["count_performance_of_the_month"],
             ])
        count += 1

    print("Brand Stats:")
    print(table)
    # km_per_month = total_30_days_used_km
    print("total 30 days used km:", round(total_30_days_used_km, 2), "total 90 days used km/3:",
          round(total_90_days_used_km / 3, 2))
    print(
        f"total km：{round(total_km, 2)},remaining km：{round(remaining_km, 2)}")
    print(
        f"avg price: {round(total_expense / total_count, 2)}, stdev: {round(statistics.stdev(price_list), 1)} , total expense: {round(total_expense, 2)}, unit expense: {round(total_expense / total_km, 3)}"
    )
    print(
        f"total expense real: {round(total_expense - total_sold, 2)}, unit expense real: {round((total_expense - total_sold) / total_km, 3)}"
    )
    hoka_remaining_km = 0
    for i in result:
        if i["shoe_name"] == 'HOKA Speedgoat 5':
            hoka_remaining_km = i['remaining_km']
    print(
        f"total km/remaining km: {round(total_km / remaining_km, 2)}, shoe km storage: {round(remaining_km / total_30_days_used_km, 2)}, shoe km storage(250): {round(remaining_km / 250, 2)}")
    print(
        f"shoe 1000km remaining: {round((1000 * shoe_remain_count - total_km) / 250, 2)}")


def predict_next_value_LinearRegression(df):
    """
    预测时间序列下一个周期的值
    """
    # df = pd.DataFrame(data)

    # 将时间戳列转换为 datetime 类型
    df['ds'] = pd.to_datetime(df['ds'])

    # 特征工程 - 添加滞后项
    df['lag_1'] = df['y'].shift(1)

    # 去掉第一行含有 NaN 的数据
    df = df.dropna()

    # 拆分数据集
    # train_size = int(len(df) * 0.8)
    # train, test = df[0:train_size], df[train_size:]
    train = df

    # 准备训练和测试数据
    X_train, y_train = train[['lag_1']], train['y']

    # 创建并训练线性回归模型
    model = LinearRegression()
    model.fit(X_train, y_train)

    # 获取最后一个月的 lag_1 值
    latest_lag_1 = df['lag_1'].iloc[-1]

    # 使用模型进行预测
    next_month_prediction = model.predict([[latest_lag_1]])

    # 预测下一个月的 "y" 值

    predicted_y = next_month_prediction[0]

    # print(f'预测下一个月的 y 值: {predicted_y}')
    return predicted_y


def show_performance_of_the_month_per_month():
    """
    """
    shoe_info = read_shoe_info_csv()
    # shoe_names = list(records.keys())
    shoe_names = list(shoe_info.keys())
    # months = sorted(set(month for data in records.values() for month in data.keys()))

    record_v2 = read_run_records_csv()

    tmp_list = [record_v2.get(shoe) for shoe in shoe_names if record_v2.get(shoe)]
    month_list = []

    for tmp in tmp_list:
        for obj in tmp:
            dt = obj["date"]
            month_list.append(dt[:7])
    months = sorted(list(set(month_list)))
    months_for_performance_of_the_month = [m for m in months if m >= "2024-02"]
    performance_of_the_month_per_shoe_count, performance_of_the_month_per_month, rank_detail = cal_performance_of_the_month_or_history(
        shoe_names,
        months_for_performance_of_the_month, "month")
    # print(performance_of_the_month_per_month)
    table = PrettyTable()
    table.field_names = ["Month",
                         "Performance of the Month",
                         "Sum Rank",
                         ]
    for month, value_list in performance_of_the_month_per_month.items():
        # print(entry)
        table.add_row(
            [
                month, value_list[0][0], round(value_list[0][1], 2)

            ])

    print("Performance of the Month：")
    print(table)

    # 显示当月细节
    current_month = months_for_performance_of_the_month[-1]
    detail_list = performance_of_the_month_per_month[current_month]
    # print(detail_list)

    start_date = current_month + "-01"
    end_date = current_month + "-31"
    sql = text(
        f"""
        SELECT shoe,MAX(rq_inc1) AS rq_inc1,MIN(top1_pace) AS top1_pace,MAX(top1_performance) AS top1_performance, MAX(rq1) AS rq1
        FROM `running_daily_shoe_stats_current_month` 
        WHERE DATE>= '{start_date}' AND DATE<= '{end_date}' AND top1_pace != '00:00'
        GROUP BY shoe
        ORDER BY top1_performance DESC
        """
    )
    # print(sql)
    result = session.execute(sql)
    data = {}
    for row in result:
        top1_pace_value = row[2]
        if top1_pace_value == "00:00":
            top1_pace_value = ""
        top1_performance_value = row[3]
        if top1_performance_value == "0":
            top1_performance_value = ""
        data[row[0]] = {"rq_inc1_value": row[1], "top1_pace_value": top1_pace_value,
                        "top1_performance_value": top1_performance_value, "rq1_value": row[4]}

    table2 = PrettyTable()
    table2.field_names = [current_month,
                          "Performance of The Month",
                          "Sum Rank",
                          # "rank rq_inc1", "rank top1 pace", "ranke top1 performance"
                          "rq1", "value1", "rq_inc1 1.25", "value2", "top1 pace", "value3", "top1 performance 1.2",
                          "value4",

                          ]
    rank = 0
    ranked_rq_inc1, ranked_top1_pace, ranked_top1_performance, ranked_top1_rq = rank_detail[0], rank_detail[1], \
                                                                                rank_detail[2], rank_detail[3]
    for shoe, rank_value in detail_list:
        # print(entry)
        rank += 1
        # if rank_value != len(shoe_names) * 4:
        if data.get(shoe, None):
            table2.add_row(
                [
                    rank, shoe, round(rank_value, 2),
                    ranked_top1_rq.get(shoe, ""), data[shoe]["rq1_value"],
                    ranked_rq_inc1.get(shoe, ""), data[shoe]["rq_inc1_value"],
                    ranked_top1_pace.get(shoe, ""), data[shoe]["top1_pace_value"],
                    ranked_top1_performance.get(shoe, ""), data[shoe]["top1_performance_value"],
                ])
    print("Performance of the Month Detail:")
    print(table2)

    sum_rank, performance_detail_dict = handle_performance_of_history_detail()
    rank = 0
    table3 = PrettyTable()
    table3.field_names = [current_month,
                          "   Performance of History   ",
                          "Sum Rank",
                          "rq1", "value1", "rq_inc1 1.25", "value2", "top1 pace", "value3", "top1 performance 1.2", "value4",

                          ]
    for shoe, rank_sum in sum_rank.items():
        # print(entry)
        rank += 1
        table3.add_row(
            [
                rank, shoe, rank_sum,
                performance_detail_dict["data_rq1"][shoe]["rank"], performance_detail_dict["data_rq1"][shoe]["value"],
                performance_detail_dict["data_rq_inc1"][shoe]["rank"],
                performance_detail_dict["data_rq_inc1"][shoe]["value"],
                performance_detail_dict["data_top1_pace"][shoe]["rank"],
                performance_detail_dict["data_top1_pace"][shoe]["value"],
                performance_detail_dict["data_top1_performance"][shoe]["rank"],
                performance_detail_dict["data_top1_performance"][shoe]["value"],
            ])
    print("Performance of History Detail:")
    print(table3)


def handle_performance_of_history_detail():
    today = datetime.date.today().strftime("%F")
    # print(today)

    # 获取4个维度的rank
    sql_top1_pace = text(
        f"""
        SELECT ROW_NUMBER() OVER (ORDER BY top1_pace) AS serial_number, shoe,top1_pace,top1_performance,rq1,rq_inc1 
        FROM `running_daily_shoe_stats` WHERE DATE = '{today}'
        AND top1_pace != '00:00'
        ORDER BY top1_pace ASC 
        """
    )

    result_top1_pace = session.execute(sql_top1_pace)
    data_top1_pace = {}
    for row in result_top1_pace:
        rank = row[0]
        shoe = row[1]
        top1_pace_value = row[2]
        data_top1_pace[shoe] = {"rank": rank, "value": top1_pace_value}
    # print(data_top1_pace)

    sql_top1_performance = text(
        f"""
        SELECT ROW_NUMBER() OVER (ORDER BY CAST(top1_performance AS FLOAT)) AS serial_number, shoe,top1_pace,top1_performance,rq1,rq_inc1 
        FROM `running_daily_shoe_stats` WHERE DATE = '{today}' 
        AND top1_pace != '00:00'
        ORDER BY CAST(top1_performance AS FLOAT) DESC
        """
    )
    result_top1_performance = session.execute(sql_top1_performance)
    data_top1_performance = {}
    for row in result_top1_performance:
        rank = row[0]
        shoe = row[1]
        value = row[3]
        data_top1_performance[shoe] = {"rank": rank, "value": value}
    count_1 = len(data_top1_performance) + 1
    for k, v in data_top1_performance.items():
        v["rank"] = count_1 - v["rank"]
    # print(data_top1_performance)

    sql_rq1 = text(
        f"""
        SELECT ROW_NUMBER() OVER (ORDER BY rq1) AS serial_number, shoe,top1_pace,top1_performance,rq1,rq_inc1 
        FROM `running_daily_shoe_stats` WHERE DATE = '{today}'
        AND top1_pace != '00:00' AND rq  != ''
        ORDER BY rq1 DESC
        """
    )
    result_rq1 = session.execute(sql_rq1)
    data_rq1 = {}
    for row in result_rq1:
        rank = row[0]
        shoe = row[1]
        value = row[4]
        data_rq1[shoe] = {"rank": rank, "value": value}
    count_1 = len(data_rq1) + 1
    for k, v in data_rq1.items():
        v["rank"] = count_1 - v["rank"]
    # print(data_rq1)

    sql_rq_inc1 = text(
        f"""
        SELECT ROW_NUMBER() OVER (ORDER BY rq_inc1) AS serial_number, shoe,top1_pace,top1_performance,rq1,rq_inc1 
        FROM `running_daily_shoe_stats` WHERE DATE = '{today}'
        AND top1_pace != '00:00' AND rq_inc1  != ''
        ORDER BY rq_inc1 DESC
        """
    )
    result_rq_inc1 = session.execute(sql_rq_inc1)
    data_rq_inc1 = {}
    for row in result_rq_inc1:
        rank = row[0]
        shoe = row[1]
        value = row[5]
        data_rq_inc1[shoe] = {"rank": rank, "value": value}
    count_1 = len(data_rq_inc1) + 1
    for k, v in data_rq_inc1.items():
        v["rank"] = count_1 - v["rank"]
    # print(data_rq_inc1)

    # 4个维度数值相加
    sum_rank = {}
    shoe_list = data_top1_pace.keys()
    for shoe in data_top1_pace:
        rank_top_pace = data_top1_pace.get(shoe)["rank"]
        rank_top1_performance = data_top1_performance.get(shoe)["rank"]
        rq1 = data_rq1.get(shoe, None)
        if rq1:
            rank_rq1 = rq1["rank"]
        else:
            rank_rq1 = len(shoe_list)
            data_rq1[shoe] = {"rank": len(shoe_list), "value": ""}

        rq_inc1 = data_rq_inc1.get(shoe, None)
        if rq_inc1:
            rank_rq_inc1 = rq_inc1["rank"]
        else:
            rank_rq_inc1 = len(shoe_list)
            data_rq_inc1[shoe] = {"rank": len(shoe_list), "value": ""}

        sum_rank[shoe] = rank_top_pace + 1.2 * rank_top1_performance + rank_rq1 + 1.25 * rank_rq_inc1
    sorted_sum_rank = dict(sorted(sum_rank.items(), key=lambda item: item[1], reverse=False))
    # print(sorted_sum_rank)
    return sorted_sum_rank, {"data_top1_pace": data_top1_pace, "data_top1_performance": data_top1_performance,
                             "data_rq1": data_rq1, "data_rq_inc1": data_rq_inc1}


def show_shoe_of_the_month_per_month(monthly_result):
    shoe_info = read_shoe_info_csv()
    # shoe_names = list(records.keys())
    shoe_names = list(shoe_info.keys())
    # months = sorted(set(month for data in records.values() for month in data.keys()))

    record_v2 = read_run_records_csv()

    tmp_list = [record_v2.get(shoe) for shoe in shoe_names if record_v2.get(shoe)]
    month_list = []

    for tmp in tmp_list:
        for obj in tmp:
            dt = obj["date"]
            month_list.append(dt[:7])
    months = sorted(list(set(month_list)))

    shoe_of_the_month, shoe_of_the_month_per_month = cal_shoe_of_the_month(shoe_names, months, monthly_result)
    # print(shoe_of_the_month_per_month)

    table = PrettyTable()
    table.field_names = ["Month",
                         "Shoe of the Month",
                         "Distance",
                         ]
    for entry in shoe_of_the_month_per_month:
        # print(entry)
        table.add_row(
            [
                entry[0],
                entry[1],
                entry[2],
            ])
    print(table)


if __name__ == '__main__':
    # df = pd.read_csv('records.csv')
    # # 将'date'列转换为日期类型
    # df['date'] = pd.to_datetime(df['date'])
    # # 筛选出日期在2023年12月的行
    # december_data = df[(df['date'].dt.year == 2023) & (df['date'].dt.month == 12)]
    # # 计算distance列的和
    # total_distance_december = december_data['distance'].sum()
    # print(f"2023年12月的总距离为: {total_distance_december} 公里")
    now = datetime.datetime.now()
    monthly_result = convert_daily_to_monthly_v2()
    # plot1()
    print("used time:", datetime.datetime.now() - now)
    # plot3()
    # plot2()
    result = cal_table_result()
    print("used time2:", datetime.datetime.now() - now)

    show_shoe_of_the_month_per_month(monthly_result)
    show_performance_of_the_month_per_month()
    cal_shoes_stats(result)
    cal_brand_stats(result)
    plot4(monthly_result)
