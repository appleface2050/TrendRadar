from prettytable import PrettyTable
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import datetime
import pandas as pd
import numpy as np
from sqlalchemy import text

from Running.Shoe.display.util import time_to_minutes
from Running.running_models import engine_running, ShoeInfo, DailyShoeRecord, session, DailyShoeStatsCurrentMonth
from Running.utils import time_to_second, second_to_time, pace1_to_pace2

def main_performance_current_month():
    today = datetime.date.today()
    today = today - datetime.timedelta(days=0)
    today = today.strftime("%F")

    # sql = text(
    #     f"SELECT * FROM running_daily_shoe_stats WHERE DATE = '{today}'")
    # # print(sql)
    # result = session.execute(sql)
    # for row in result:
    #     print(row)

    count = 0
    table = PrettyTable()
    table.field_names = ["date", "shoe","间隔日", "使用次数", "总距离", "平均距离", "平均时长",
                         "平均心率",
                         "平均步频", "平均步幅", " pace1 ", "perfor1","pace",  "perfor"
                         ]

    for i in session.query(DailyShoeStatsCurrentMonth).filter(DailyShoeStatsCurrentMonth.date == today).order_by(
            DailyShoeStatsCurrentMonth.top1_performance.desc()):
            # DailyShoeStats.total_distance.desc()):

        # if i.shoe == "adidas adizero Boston 12":
        #     print(i.shoe)
        last_use_date = DailyShoeRecord.get_last_used_date(i.shoe)
        if last_use_date:
            interval_days = (datetime.datetime.today() - datetime.datetime.strptime(last_use_date, "%Y-%m-%d")).days
        else:
            interval_days = 0
        used_time = i.weight_avg_run_time
        minutes = time_to_minutes(used_time)
        if i.avg_distance == 0:
            performance = 0
        else:
            min = i.weight_avg_pace.split(":")[0]
            sec = i.weight_avg_pace.split(":")[1]
            km_per_min = int(min) + int(sec)/60
            performance = round(60 / km_per_min / i.weight_avg_heart_rate * 100, 2)

        table.add_row(
            [
                i.date, i.shoe, interval_days, i.used_times, i.distance, i.avg_distance, i.weight_avg_run_time, i.weight_avg_heart_rate,
                i.weight_avg_cadence, i.weight_avg_stride_length,
                i.top1_pace,i.top1_performance,i.weight_avg_pace, performance
            ])
        count += 1

    print(table)

def main_performance2_current_month():
    today = datetime.date.today()
    today = today - datetime.timedelta(days=0)
    today = today.strftime("%F")

    # sql = text(
    #     f"SELECT * FROM running_daily_shoe_stats WHERE DATE = '{today}'")
    # # print(sql)
    # result = session.execute(sql)
    # for row in result:
    #     print(row)

    count = 0
    table = PrettyTable()
    table.field_names = ["date", "shoe", #"使用次数", "总距离", "平均距离",
                         #"平均时长",

                         "rq1",
                         "rq3", "rq", "rq_inc1","rq_inc3","rq_inc","pace1", "performance1","pace",  "performance"
                         ]

    for i in session.query(DailyShoeStatsCurrentMonth).filter(DailyShoeStatsCurrentMonth.date == today).order_by(
            DailyShoeStatsCurrentMonth.top1_performance.desc()):
            # DailyShoeStats.total_distance.desc()):
        # print(i.shoe)
        used_time = i.weight_avg_run_time
        minutes = time_to_minutes(used_time)
        if i.avg_distance == 0:
            performance = 0
        else:
            min = i.weight_avg_pace.split(":")[0]
            sec = i.weight_avg_pace.split(":")[1]
            km_per_min = int(min) + int(sec)/60
            performance = round(60 / km_per_min / i.weight_avg_heart_rate * 100, 2)

        table.add_row(
            [
                i.date, i.shoe,
                #i.total_used_times, i.total_distance, i.avg_distance,
                #i.weight_avg_run_time,
                i.rq1[:4],
                i.rq3[:4],
                i.rq[:4],
                i.rq_inc1[:4],
                i.rq_inc3[:4],
                i.rq_inc[:4],
                i.top1_pace,i.top1_performance,i.weight_avg_pace, performance
            ])
        count += 1

    print(table)

if __name__ == '__main__':
    # from Home.Running.Crontab.daily_shoe_stats import main as daily_shoe_stats_main
    # daily_shoe_stats_main()
    print("show performance 1 current month")
    main_performance_current_month()
    print("show performance 2 current month")
    main_performance2_current_month()


