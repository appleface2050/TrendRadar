"""
================================================================================
统一数据库查询接口使用说明
================================================================================

本文件中的数据库查询逻辑已被提取到 Running/db_queries.py 中。

使用新接口的方式：
-----------------
from Running.db_queries import get_daily_shoe_stats_by_date_with_performance

# 获取指定日期的跑鞋统计数据（已计算performance）
today = datetime.date.today().strftime("%Y-%m-%d")
results = get_daily_shoe_stats_by_date_with_performance(today)

for item in results:
    print(f"{item['shoe']}: {item['performance']}")

优势：
-----
- 代码复用，避免重复逻辑
- 统一的接口，易于维护
- 清晰的函数名和文档

原始查询位置：第36-56行
================================================================================
"""

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
from Running.running_models import engine_running, ShoeInfo, DailyShoeRecord, session, DailyShoeStats
from Running.utils import time_to_second, second_to_time, pace1_to_pace2

def main():
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
    table.field_names = ["date", "shoe", "使用次数", "总距离", "平均距离", "平均时长",
                         "平均心率",
                         "平均步频", "平均步幅", "pace1", "performance1","pace",  "performance"
                         ]

    for i in session.query(DailyShoeStats).filter(DailyShoeStats.date == today).order_by(
            DailyShoeStats.top1_performance.desc()):
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
                i.date, i.shoe, i.total_used_times, i.total_distance, i.avg_distance, i.weight_avg_run_time, i.weight_avg_heart_rate,
                i.weight_avg_cadence, i.weight_avg_stride_length,
                i.top1_pace,i.top1_performance,i.weight_avg_pace, performance
            ])
        count += 1
    print("history performance 1")
    print(table)

if __name__ == '__main__':
    from Home.Running.Crontab.rq_2_db import main as rq_2_db_main
    rq_2_db_main()

    from Home.Running.Crontab.daily_shoe_stats import main as daily_shoe_stats_main
    daily_shoe_stats_main()

    main()

