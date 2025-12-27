"""
计算鞋各类型下的分数，统计总分数
"""
import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

from Home.Running.Shoe.display.shoe_table import cal_table_result
from confs.mysql import mysql_conf
from sqlalchemy import create_engine, text
import pandas as pd
from sqlalchemy.engine import reflection
# from util.util import pickle_load, pickle_dump
from Home.Running.running_models import engine_running, ShoeInfo, DailyShoeStatsEMTIR, DailyShoeScore
import numpy as np


# def cal_shoe_score():
#     df_sql = text(
#         f"""
#         SELECT shoe, distance,rq,rq_inc,EMTIR FROM running_shoe_record
#         """
#     )
#     df = pd.read_sql(df_sql, engine_running)
#     df["EMTIR"] = df["EMTIR"].fillna("E")
#     # df[df["rq"]==""]
#     df["rq_inc"] = df["rq_inc"].fillna(0)
#
#     shoe_list = list(set(df["shoe"].tolist()))
#
#     for shoe in shoe_list:
#         shoe_df = df[df["shoe"] == shoe]
#         print(shoe_df)

def cal_shoe_score(today):
    # 获取shoe of the month
    result = cal_table_result()

    shoe_name_list = ShoeInfo.get_all_shoe()
    Shoe_Score = {}
    for shoe in shoe_name_list:
        Shoe_Score[shoe] = {"E": 0, "M": 0, "T": 0, "I": 0, "R": 0}
    E_df = None
    for EMTIR in ("E", "M", "T", "I", "R"):
        # df_sql = text(
        #     f"""
        #         SELECT shoe, total_distance,top1_pace, top1_performance, rq1,rq_inc1 FROM `running_daily_shoe_stats_emtir`
        #         WHERE DATE = '{today}' and EMTIR = '{EMTIR}'
        #         """
        # )
        df_sql = text(
            f"""
                SELECT shoe, total_distance,avg_pace, avg_performance, rq,rq_inc FROM `running_daily_shoe_stats_emtir`
                WHERE DATE = '{today}' and EMTIR = '{EMTIR}'
                """
        )
        df = pd.read_sql(df_sql, engine_running)
        df.loc[df["avg_pace"] == "00:00", "avg_pace"] = "12:00"
        df.loc[df["rq"] == "", "rq"] = "0"
        df.loc[df["rq_inc"] == "", "rq_inc"] = "0"

        # if total_df.empty:
        #     total_df = df
        # else:
        #     total_df = pd.merge(total_df, df, on="shoe", how='outer')

        # 补全df
        for shoe in shoe_name_list:
            if shoe not in df["shoe"].tolist():
                new_line = {
                    'shoe': shoe,
                    'total_distance': 1,
                    'avg_pace': '12:00',
                    'avg_performance': 1,
                    'rq': 0,
                    'rq_inc': -5
                }

                # 将新行数据转换为 DataFrame
                new_df = pd.DataFrame([new_line])

                # 合并原始 DataFrame 和新行数据 DataFrame
                df = pd.concat([df, new_df], ignore_index=True)

        # 计算单项分数
        shoe_number = len(shoe_name_list)
        df['avg_pace_order_score'] = round((shoe_number - df['avg_pace'].rank() + 1) / shoe_number, 2) * 10
        df['avg_performance_order_score'] = round((df['avg_performance'].astype(float).rank()) / shoe_number, 2) * 10
        df['rq_order_score'] = round((df['rq'].astype(float).rank()) / shoe_number, 2) * 10
        df['rq_inc_order_score'] = round((df['rq_inc'].astype(float).rank()) / shoe_number, 2) * 10

        df["_sum_score"] = (df['avg_pace_order_score'] + df['avg_performance_order_score'] + df[
            'rq_order_score'] + df['rq_inc_order_score']) / 4
        # print(df)
        avalable_shoe_list = df["shoe"].tolist()
        for shoe in avalable_shoe_list:
            Shoe_Score[shoe][EMTIR] = df.loc[df["shoe"] == shoe, "_sum_score"].tolist()[0]

        if EMTIR == "E":
            E_df = df

    # 获取里程分数，每600公里 1分
    distance_df = DailyShoeStatsEMTIR.get_group_total_distance(today)
    for shoe in distance_df["shoe"].tolist():
        Shoe_Score[shoe]["distance_score"] = round(
            distance_df.loc[distance_df["shoe"] == shoe, "distance_score"].tolist()[0], 2)

    # 获取特殊附加分数
    special_df = pd.read_csv("C:\git\Quant\Home\Running\Shoe\special_record.csv")
    # special_dict = {}
    for shoe in shoe_name_list:
        # if special_dict.get(shoe, None) is None:
        #     special_dict[shoe] = 0
        if shoe in special_df["shoe"].tolist():
            # special_dict[shoe] = sum(special_df.loc[special_df["shoe"]==shoe, "score"].tolist())
            Shoe_Score[shoe]["special_score"] = sum(special_df.loc[special_df["shoe"] == shoe, "score"].tolist())
        else:
            Shoe_Score[shoe]["special_score"] = 0
        print(shoe)
        Shoe_Score[shoe]["E_avg_pace"] = E_df.loc[E_df["shoe"] == shoe, "avg_pace"].to_list()[0]
        Shoe_Score[shoe]["E_avg_performance"] = E_df.loc[E_df["shoe"] == shoe, "avg_performance"].to_list()[0]
        Shoe_Score[shoe]["E_rq"] = E_df.loc[E_df["shoe"] == shoe, "rq"].to_list()[0]
        Shoe_Score[shoe]["E_rq_inc"] = E_df.loc[E_df["shoe"] == shoe, "rq_inc"].to_list()[0]

            # special_dict[shoe] = 0
    # for k, v in special_dict.items():

    distance_dict = {}

    # 计算总成绩, EMTIR出现一次0，减去0.1
    for shoe, v in Shoe_Score.items():
        count_EMTIR_0 = 0
        EMTIR_sum = 0
        for EMTIR in ("E", "M", "T", "I", "R"):
            # if v[EMTIR] < v["E"]:  # 如果比E小，就不算进去
            #     count_EMTIR_0 += 1
            # else:
            #     EMTIR_sum += v[EMTIR]

            from Home.Running.running_models import session

            sql = text(f"""
            SELECT SUM(total_distance) AS distance FROM `running_daily_shoe_stats_emtir`
            WHERE DATE = '{datetime.date.today().strftime('%F')}' AND shoe = '{shoe}' AND EMTIR = '{EMTIR}'
            """)
            cursor = session.execute(sql)
            distance = cursor.fetchone()[0]
            if not distance:
                distance = 0
            print(distance)
            Shoe_Score[shoe][EMTIR+"_distance"] = distance

        # 修改为EMTIR加权平均值
        EMTIR_sum = (Shoe_Score[shoe]["E"] * Shoe_Score[shoe]["E_distance"] + Shoe_Score[shoe]["M"] * Shoe_Score[shoe]["M_distance"] + Shoe_Score[shoe]["T"] * Shoe_Score[shoe]["T_distance"] +
        Shoe_Score[shoe]["I"] * Shoe_Score[shoe]["I_distance"] + Shoe_Score[shoe]["R"] * Shoe_Score[shoe]["R_distance"]) / (Shoe_Score[shoe]["E_distance"] + Shoe_Score[shoe]["M_distance"]+Shoe_Score[shoe]["T_distance"]+Shoe_Score[shoe]["I_distance"]+Shoe_Score[shoe]["R_distance"])

        Shoe_Score[shoe]["EMTIR_sum"] = round(EMTIR_sum, 2)

        for i in result:
            if i["shoe_name"] == shoe:
                Shoe_Score[shoe]["count_shoe_of_the_month"] = i["count_shoe_of_the_month"]
                Shoe_Score[shoe]["count_performance_of_the_month"] = i["count_performance_of_the_month"]
                break


        Shoe_Score[shoe]["score"] = Shoe_Score[shoe]["EMTIR_sum"] + Shoe_Score[shoe]["distance_score"] + \
                                    Shoe_Score[shoe]["special_score"] + Shoe_Score[shoe][
                                        "count_shoe_of_the_month"] * 0.1 + Shoe_Score[shoe][
                                        "count_performance_of_the_month"] * 0.1

    # 先按照分数从高到低排序
    sorted_shoes = sorted(Shoe_Score.items(), key=lambda x: x[1]['score'], reverse=True)

    # 给每个鞋子添加排名
    for idx, (shoe_name, shoe_info) in enumerate(sorted_shoes):
        shoe_info['order'] = idx + 1

    for shoe, v in Shoe_Score.items():
        data_dict = Shoe_Score[shoe]
        DailyShoeScore.add_record(today, shoe, data_dict)

    # print(Shoe_Score)


if __name__ == '__main__':
    today = datetime.datetime.today()
    cal_shoe_score(today.strftime("%F"))
