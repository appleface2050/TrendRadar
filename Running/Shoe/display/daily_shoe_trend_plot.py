import datetime
import pandas as pd
import numpy
from prettytable import PrettyTable
import os
import sys
import plotly.express as px
from pandasql import sqldf
import seaborn as sns
import matplotlib.pyplot as plt
import prettytable
from matplotlib.font_manager import FontProperties

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# sqldf(query, globals())
# from Running.Shoe.shoe import read_shoe_info_csv
from Running.Shoe.display.shoe_table import read_shoe_info_csv

# 获取脚本所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
records = pd.read_csv(os.path.join(script_dir, '..', 'records.csv'))
shoe_info = pd.read_csv(os.path.join(script_dir, '..', 'shoe_info.csv'))

pysqldf = lambda query: sqldf(query, globals())

csv_data_start_ = "2023-12-24"


def used_km_plot():
    global records
    global shoe_info

    shoe_list = shoe_info["name"].tolist()
    # print(shoe_list)
    all_data = {}
    for shoe in shoe_list:
        start = datetime.datetime.strptime(csv_data_start_, "%Y-%m-%d").date()
        today = datetime.date.today()
        # print(records)
        data = {}
        while start <= today:
            sql = f"""
            SELECT sum(distance) FROM records where shoe='{shoe}' and date <= '{start.strftime("%F")}'
            """
            # print(sql)
            r = pysqldf(sql)
            result = r.loc[0][0]
            if result is None:
                result = 0
            # print(shoe, start, round(result, 2))
            try:
                data[start.strftime("%F")] = round(result, 2)
            except Exception as e:
                print(e)
            start += datetime.timedelta(days=1)
        all_data[shoe] = data
    # print(all_data)

    # plot
    df = pd.DataFrame.from_dict(all_data)
    df.index = pd.to_datetime(df.index)
    print(df)
    # 使用Seaborn绘制折线图
    plt.figure(figsize=(12, 8))
    sns.set_style("whitegrid")

    # 选择要绘制的列
    columns_to_plot = shoe_list

    # 绘制折线图
    sns.lineplot(data=df[columns_to_plot])

    # 设置图形标题和标签
    plt.title('鞋子销售量折线图', fontsize=16)
    plt.xlabel('日期', fontsize=14)
    plt.ylabel('销售量', fontsize=14)

    # 显示图例
    font = FontProperties(fname=r'C:\Windows\Fonts\SimHei.ttf', size=12)
    # plt.legend()
    plt.legend(title='鞋子型号', loc='upper left', bbox_to_anchor=(1, 1), prop=font, ncol=2)

    # 旋转日期标签，使其更易读
    plt.xticks(rotation=45)

    # 显示图形
    plt.show()


def used_km():
    global records
    global shoe_info

    shoe_list = shoe_info["name"].tolist()
    # print(shoe_list)
    all_data = {}
    for shoe in shoe_list:
        start = datetime.datetime.strptime(csv_data_start_, "%Y-%m-%d").date()
        today = datetime.date.today()
        # print(records)
        data = {}
        while start <= today:
            sql = f"""
            SELECT sum(distance) FROM records where shoe='{shoe}' and date <= '{start.strftime("%F")}'
            """
            # print(sql)
            r = pysqldf(sql)
            result = r.loc[0][0]
            if result is None:
                result = 0
            # print(shoe, start, round(result, 2))
            try:
                data[start.strftime("%F")] = round(result, 2)
            except Exception as e:
                print(e)
            start += datetime.timedelta(days=1)
        all_data[shoe] = data

    df = pd.DataFrame.from_dict(all_data)

    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)

    print(df)

    # table = PrettyTable()
    # # 设置 PrettyTable 参数
    # table.max_width = 4  # 控制表格的最大宽度
    # table.align = "l"  # 设置对齐方式为左对齐
    #
    # # # 添加列名
    # # table.field_names = ['日期'] + shoe_list
    #
    # table.field_names = df.columns
    #
    # for row in df.itertuples(index=False):
    #     table.add_row(row)
    #
    # print(table)


def used_km_plotly():
    global records
    global shoe_info

    shoe_info_dict = read_shoe_info_csv()
    color_map = {}
    shoe_list = shoe_info["name"].tolist()
    for shoe in shoe_list:
        color_map[shoe] = shoe_info_dict[shoe]["color"]


    # print(shoe_list)
    all_data = {}
    for shoe in shoe_list:
        start = datetime.datetime.strptime(csv_data_start_, "%Y-%m-%d").date()
        today = datetime.date.today()
        # print(records)
        data = {}
        while start <= today:
            sql = f"""
            SELECT sum(distance) FROM records where shoe='{shoe}' and date <= '{start.strftime("%F")}'
            """
            # print(sql)
            r = pysqldf(sql)
            result = r.loc[0][0]
            if result is None:
                result = 0
            # print(shoe, start, round(result, 2))
            try:
                data[start.strftime("%F")] = round(result, 2)
            except Exception as e:
                print(e)
            start += datetime.timedelta(days=1)
        all_data[shoe] = data

    df = pd.DataFrame.from_dict(all_data)
    df = df.reset_index()
    df = df.rename(columns={"index": "date"})
    # factor_value_df.rename(columns={"value": factor["factor"]}, inplace=True)
    # print(df)
    fig = px.line(df, x='date', y=shoe_list, title='used km', color_discrete_map=color_map)
    fig.show()


def main():
    # used_km_plot()
    # used_km()
    used_km_plotly()


if __name__ == '__main__':
    now = datetime.datetime.now()
    main()
    print(datetime.datetime.now() - now)
