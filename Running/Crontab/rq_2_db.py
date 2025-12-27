import datetime
import pandas as pd
import numpy as np
from sqlalchemy import text
from sqlalchemy.sql import exists
import csv

from Home.Running.Shoe.display.shoe_table import read_shoe_info_csv
from Home.Running.running_models import engine_running, ShoeInfo, DailyShoeRecord, session, DailyShoeStats, DailyRQRecord
from Home.Running.utils import time_to_second, second_to_time, pace1_to_pace2

def rq_2_db(start):
    # Read CSV data from the file
    with open('C:\git\Quant\Home\Running\RQ\\rq.csv', 'r', encoding='utf-8') as csv_file:
        # Parse CSV data and populate the dictionary
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if not session.query(exists().where(DailyRQRecord.date == row["日期"]
                                                )).scalar():  # 新record

                print(row)
                o = DailyRQRecord()
                o.date = row["日期"]
                o.rq = row["RQ"]
                o.status = row["status"]
                o.physical_power = row["physical power"]
                o.fatigue = row["fatigue"]
                o.uptime = datetime.datetime.now()

                try:
                    session.add(o)
                    session.commit()
                except Exception as e:
                    session.rollback()
                    print(e)

def main():
    # 从2023-12-26开始
    # for i in range(35):
    #     print(i)
    #     today = datetime.date.today() - datetime.timedelta(days=i)
    #     handle_daily_shoe_stats(today.strftime("%F"))

    today = datetime.date.today()  # - datetime.timedelta(days=33)

    # 将record.csv, shoe_info.csv新增数据存入mysql
    rq_2_db(today.strftime("%F"))



if __name__ == '__main__':
    main()
