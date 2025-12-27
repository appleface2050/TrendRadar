import datetime
import csv
import pandas as pd
import numpy as np

from Home.Running.running_models import engine_running, ShoeInfo, DailyShoeRecord, DailyShoeStats, DailyRQRecord


def handle_shoe_info():
    csv_dir = "C:\git\Quant\Home\Running\Shoe\shoe_info.csv"
    df = pd.read_csv(csv_dir)
    df.rename(inplace=True, columns={"name": "shoe"})
    df = df.fillna("")
    df.to_sql(ShoeInfo.__tablename__, con=engine_running, index=False, if_exists='append')


def handle_shoe_record():
    csv_dir = "C:\git\Quant\Home\Running\Shoe\\records.csv"
    df = pd.read_csv(csv_dir)
    # df.rename(inplace=True, columns={"name": "shoe"})
    df = df.fillna("")
    df.to_sql(DailyShoeRecord.__tablename__, con=engine_running, index=False, if_exists='append')


def handle_rq_record():
    csv_dir = "C:\git\Quant\Home\Running\RQ\\rq.csv"
    df = pd.read_csv(csv_dir)
    # df = df.rename(columns={"日期", "date"})
    df.rename(columns={"日期": "date", "physical power": "physical_power", "RQ": "rq"}, inplace=True)
    df = df.fillna("")
    df.to_sql(DailyRQRecord.__tablename__, con=engine_running, index=False, if_exists='append')




def main():
    # handle_shoe_info()
    # handle_shoe_record()
    # handle_rq_record()
    pass


if __name__ == '__main__':
    main()
