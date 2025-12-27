"""
================================================================================
统一数据库查询接口使用说明
================================================================================

本文件中的数据库查询逻辑已被提取到 Running/db_queries.py 中。

使用新接口的方式：
-----------------
from Running.db_queries import get_daily_shoe_score_by_date

# 获取指定日期的跑鞋评分数据
today = datetime.date.today().strftime("%Y-%m-%d")
scores = get_daily_shoe_score_by_date(today)

for score in scores:
    print(f"{score.order}. {score.shoe}: {score.score}")

优势：
-----
- 代码复用，避免重复逻辑
- 统一的接口，易于维护
- 清晰的函数名和文档

原始查询位置：第36-37行
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
from Running.running_models import engine_running, ShoeInfo, DailyShoeRecord, session, DailyShoeStats, \
    DailyShoeScore
from Running.utils import time_to_second, second_to_time, pace1_to_pace2


def main():
    today = datetime.date.today()
    today = today.strftime("%F")
    order = 1
    table = PrettyTable()
    table.field_names = ["date", "order", "shoe",
                         "score", "distance",
                         "special", "SOTM", "POTM",
                         "E",
                         "M", "T", "I", "R", "pace", "performance", "rq", "rq_inc"
                         ]

    # last_month_end_date = 0
    first_day_of_current_month = datetime.datetime.strptime(today, "%Y-%m-%d").replace(day=1)
    last_day_of_previous_month = first_day_of_current_month - datetime.timedelta(days=1)
    last_month_end_date = last_day_of_previous_month.strftime("%Y-%m-%d")

    for i in session.query(DailyShoeScore).filter(DailyShoeScore.date == today).order_by(
            DailyShoeScore.order.asc()):
        table.add_row(
            [
                i.date, i.order, i.shoe,
                i.score, str(i.distance_score) + " / " + str(int(500 * i.distance_score)),
                i.special_score, int(i.count_shoe_of_the_month), int(i.count_performance_of_the_month),
                i.E,
                i.M, i.T, i.I, i.R, i.E_avg_pace, round(i.E_avg_performance, 2), i.E_rq, round(i.E_rq_inc, 2)
            ])
        order += 1
    print("daily shoe score")
    print(table)


if __name__ == '__main__':
    main()
