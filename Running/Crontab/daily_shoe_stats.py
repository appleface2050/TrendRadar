import datetime
import pandas as pd
import numpy as np
from sqlalchemy import text
from sqlalchemy.sql import exists
import csv

from Home.Running.Crontab.cal_shoe_score import cal_shoe_score
from Home.Running.Shoe.display.shoe_table import read_shoe_info_csv, cal_table_result
from Home.Running.running_models import engine_running, ShoeInfo, DailyShoeRecord, session, DailyShoeStats, \
    DailyRQRecord, DailyShoeStatsCurrentMonth, DailyShoeStatsEMTIR
from Home.Running.utils import time_to_second, second_to_time, pace1_to_pace2


def handle_daily_shoe_stats_current_month(start):
    """当月数据"""
    print(start)
    current_month = start[:7]
    start_date = current_month + "-01"
    end_date = current_month + "-31"

    for shoe_info in session.query(ShoeInfo).all():
        # if shoe_info.shoe != "adidas adizero Boston 12":
        #     continue

        count = session.query(DailyShoeStatsCurrentMonth).filter(DailyShoeStatsCurrentMonth.date == start,
                                                                 DailyShoeStatsCurrentMonth.shoe == shoe_info.shoe).count()
        if count != 0:  # 可以一日多次运行，进行update操作
            a = session.query(DailyShoeStatsCurrentMonth).filter(DailyShoeStatsCurrentMonth.date == start,
                                                                 DailyShoeStatsCurrentMonth.shoe == shoe_info.shoe).first()
        else:
            a = DailyShoeStatsCurrentMonth()
        a.date = start
        a.shoe = shoe_info.shoe
        a.uptime = datetime.datetime.now()

        a.used_times = session.query(DailyShoeRecord).filter(DailyShoeRecord.shoe == shoe_info.shoe,
                                                             DailyShoeRecord.date >= start_date,
                                                             DailyShoeRecord.date <= end_date,
                                                             DailyShoeRecord.distance >= 1).count()
        if a.used_times == 0:
            continue

        sql = text(
            f"select sum(distance) from `running_shoe_record` where date <= '{end_date}' and date>='{start_date}' and shoe = '{shoe_info.shoe}'")
        print(sql)
        result = session.execute(sql)
        for row in result:
            a.distance = row[0]
        if a.distance is None:
            a.distance = 0
        a.distance = round(a.distance, 2)

        # if a.total_used_times != 0:
        #     a.avg_distance = round(a.total_distance / a.total_used_times, 2)
        # else:
        #     a.avg_distance = 0

        distance_mul_heart_rate = 0
        distance_mul_run_time_second = 0
        distance_mul_cadence = 0
        distance_mul_stride_length = 0
        distance_mul_speed = 0

        distance_sum = 0
        used_time_sum = 0

        # real_used_times = 0 # 里程大于1的使用次数
        # real_used_distance = 0 # 里程大于1的使用距离

        for record in session.query(DailyShoeRecord).filter(DailyShoeRecord.shoe == shoe_info.shoe,
                                                            DailyShoeRecord.date >= start_date,
                                                            DailyShoeRecord.date <= end_date,
                                                            DailyShoeRecord.distance >= 1):
            if int(record.average_heart_rate) == 0 or int(record.cadence) == 0:
                continue
            else:
                record_distance = float(record.distance)
                if record_distance < 1:
                    continue
                    # real_used_times += 1
                    # real_used_distance += record.distance

                second = time_to_second(record.used_time)
                speed = 1000 * record_distance / second  # 米/秒
                stride_length = round(speed / (int(record.cadence) / 60), 4)  # 先转换为步/秒
                pace1 = 1 / (speed * 60 / 1000)
                pace = pace1_to_pace2(pace1)

                distance_mul_speed += record_distance * speed
                distance_mul_stride_length += record_distance * stride_length

                distance_sum += record_distance
                used_time_sum += 1
                distance_mul_heart_rate += record_distance * int(record.average_heart_rate)
                distance_mul_cadence += record_distance * int(record.cadence)
                distance_mul_run_time_second += record_distance * second

        if distance_sum != 0:
            a.weight_avg_heart_rate = round(distance_mul_heart_rate / distance_sum, 2)
            a.weight_avg_cadence = round(distance_mul_cadence / distance_sum, 2)
            a.weight_avg_run_time = second_to_time(distance_mul_run_time_second / distance_sum)
            a.weight_avg_stride_length = round(distance_mul_stride_length / distance_sum, 2)
            weight_avg_speed = distance_mul_speed / distance_sum
            a.weight_avg_pace = pace1_to_pace2(1 / (weight_avg_speed * 60 / 1000))
        else:
            a.weight_avg_heart_rate = 0
            a.weight_avg_cadence = 0
            a.weight_avg_run_time = ""
            a.weight_avg_stride_length = 0
            a.weight_avg_pace = ""

        # if real_used_distance == 0:
        #     a.avg_distance = 0
        # else:
        if used_time_sum == 0:
            a.avg_distance = 0
        else:
            a.avg_distance = round(distance_sum / used_time_sum, 2)

        # 每个shoe的top3跑步数据
        top1_pace1 = 0
        top1_performance = 0

        top3_weight_avg_pace1 = 0
        top3_weight_avg_performance = 0

        top3_sum_distance = 0
        top3_mul_pace1 = 0
        top3_mul_performance = 0

        sql_top3 = text(f"""
        SELECT `date`, shoe, distance, TIME_TO_SEC(STR_TO_DATE(used_time, '%H:%i:%s'))/60/distance AS pace1, 
        60/(TIME_TO_SEC(STR_TO_DATE(used_time, '%H:%i:%s'))/60/distance)/average_heart_rate*100 AS performance_schema,
        average_heart_rate, cadence, `type`
        FROM `running_shoe_record` WHERE distance >= 1 AND average_heart_rate != 0
        AND date >= '{start_date}' and date <= '{end_date}'
        AND shoe = '{shoe_info.shoe}'
        ORDER BY pace1 ASC LIMIT 3
        """)
        print(sql_top3)
        result = session.execute(sql_top3)
        for row in result:
            # print(row)
            distance = float(row[2])
            pace1 = row[3]
            performance = row[4]

            if top1_pace1 == 0:
                top1_pace1 = pace1
                top1_performance = performance

            if top1_pace1 > pace1:
                top1_pace1 = pace1
            if top1_performance < performance:
                top1_performance = performance

            top3_sum_distance += distance
            top3_mul_pace1 += distance * pace1
            top3_mul_performance += distance * performance

        if top3_sum_distance != 0:
            top3_weight_avg_pace1 = top3_mul_pace1 / top3_sum_distance
            top3_weight_avg_performance = top3_mul_performance / top3_sum_distance
        print("top1:", top1_pace1, pace1_to_pace2(top1_pace1), top1_performance)
        print("top3:", top3_weight_avg_pace1, pace1_to_pace2(top3_weight_avg_pace1), top3_weight_avg_performance)

        a.top1_pace = pace1_to_pace2(top1_pace1)
        a.top1_performance = round(top1_performance, 2)
        a.top3_pace = pace1_to_pace2(top3_weight_avg_pace1)
        a.top3_performance = round(top3_weight_avg_performance, 2)

        # rq1，rq3，rq数据
        rq1 = ""
        rq3 = ""
        rq = ""

        rq_sql = text(f"""
        SELECT shoe, distance, rq 
        FROM `running_shoe_record`
        WHERE distance >= 1 AND average_heart_rate != 0 AND rq != ''
        AND date >= '{start_date}' and date <= '{end_date}'
        AND shoe='{shoe_info.shoe}' ORDER BY rq DESC""")
        result = session.execute(rq_sql)
        for row in result:
            # distance = float(row[1])
            rq1 = float(row[2])
            break

        distance_mul_rq3 = 0
        distance_sum3 = 0
        count = 0  # 循环3次
        result = session.execute(rq_sql)
        for row in result:
            if row[2]:
                distance = float(row[1])
                rq = float(row[2])
                distance_sum3 += distance
                distance_mul_rq3 += distance * rq
            else:
                distance_sum += 0
            count += 1
            if count >= 3:
                break

        if distance_sum3 != 0:
            rq3 = round(distance_mul_rq3 / distance_sum3, 2)

        distance_mul_rq = 0
        distance_sum = 0
        result = session.execute(rq_sql)
        for row in result:
            if row[2]:
                distance = float(row[1])
                rq = float(row[2])
                distance_sum += distance
                distance_mul_rq += distance * rq
            else:
                distance_sum += 0

        if distance_sum != 0:
            rq = round(distance_mul_rq / distance_sum, 2)

        a.rq1 = rq1
        a.rq3 = rq3
        a.rq = rq

        # 处理rq_inc
        rq_inc_sql = text(f"""
        SELECT shoe, rq_inc
        FROM `running_shoe_record`
        WHERE distance >= 1 AND average_heart_rate != 0 AND rq_inc != '' and rq_inc >0
        AND date >= '{start_date}' and date <= '{end_date}'
        AND shoe='{shoe_info.shoe}' ORDER BY rq_inc DESC""")
        result = session.execute(rq_inc_sql)
        rq_inc1 = ""
        for row in result:
            rq_inc1 = float(row[1])
            break

        result = session.execute(rq_inc_sql)
        rq_inc3 = 0
        rq_inc3_sum = 0
        count = 0
        for row in result:
            rq_inc = float(row[1])
            rq_inc3_sum += rq_inc
            count += 1
            if count >= 3:
                break
        if count == 0:
            rq_inc3 = ""
        else:
            rq_inc3 = rq_inc3_sum / count

        rq_inc_sql = text(f"""
        SELECT shoe, rq_inc
        FROM `running_shoe_record`
        WHERE distance >= 1 AND average_heart_rate != 0 AND rq_inc != ''  
        AND date >= '{start_date}' and date <= '{end_date}'
        AND shoe='{shoe_info.shoe}' ORDER BY rq_inc DESC""")  # 保留rq_inc为负的
        result = session.execute(rq_inc_sql)
        rq_inc_sum = 0
        count = 0
        for row in result:
            rq_inc_ = float(row[1])
            rq_inc_sum += rq_inc_
            count += 1
        if count == 0:
            rq_inc = ""
        else:
            rq_inc = rq_inc_sum / count

        a.rq_inc1 = rq_inc1
        a.rq_inc3 = rq_inc3
        a.rq_inc = rq_inc
        print(a)

        try:
            session.add(a)
            session.commit()
        except Exception as e:
            session.rollback()
            print(e)


def handle_daily_shoe_stats_EMTIR(start):
    for EMTIR in ("E", "M", "T", "I", "R"):

        for shoe_info in session.query(ShoeInfo).all():
            # if shoe_info.shoe != "乔丹 强风SE":
            #     continue
            # if session.query(DailyShoeStats).filter(DailyShoeStats.date == start).filter(
            #         DailyShoeStats.shoe == shoe_info.shoe).count != 0:
            count = session.query(DailyShoeStatsEMTIR).filter(DailyShoeStatsEMTIR.date == start,
                                                              DailyShoeStatsEMTIR.shoe == shoe_info.shoe,
                                                              DailyShoeStatsEMTIR.EMTIR == EMTIR).count()
            if count != 0:  # 可以一日多次运行，进行update操作
                a = session.query(DailyShoeStatsEMTIR).filter(DailyShoeStatsEMTIR.date == start,
                                                              DailyShoeStatsEMTIR.shoe == shoe_info.shoe,
                                                              DailyShoeStatsEMTIR.EMTIR == EMTIR).first()
            else:
                a = DailyShoeStatsEMTIR()
            a.date = start
            a.shoe = shoe_info.shoe
            a.EMTIR = EMTIR
            a.uptime = datetime.datetime.now()

            # if a.shoe == "李宁 赤兔6 PRO":
            #     print(a)

            a.total_used_times = session.query(DailyShoeRecord).filter(DailyShoeRecord.shoe == shoe_info.shoe,
                                                                       DailyShoeRecord.date <= start,
                                                                       DailyShoeRecord.EMTIR == EMTIR).count()
            if a.total_used_times == 0:
                continue

            sql = text(
                f"select sum(distance) from `running_shoe_record` where date <= '{start}' and shoe = '{shoe_info.shoe}' and EMTIR = '{EMTIR}'")
            print(sql)
            result = session.execute(sql)
            for row in result:
                a.total_distance = row[0]
            if a.total_distance is None:
                a.total_distance = 0
            a.total_distance = round(a.total_distance, 2)

            # if a.total_used_times != 0:
            #     a.avg_distance = round(a.total_distance / a.total_used_times, 2)
            # else:
            #     a.avg_distance = 0

            # 计算每个鞋，每个EMTIR的平均配速和平均performance
            avg_pace_sql = text(f"""
            SELECT `date`, shoe, distance, TIME_TO_SEC(STR_TO_DATE(used_time, '%H:%i:%s'))/60/distance AS pace1,
            60/(TIME_TO_SEC(STR_TO_DATE(used_time, '%H:%i:%s'))/60/distance)/average_heart_rate*100 AS performance
            FROM `running_shoe_record` WHERE distance >= 1 AND average_heart_rate != 0
            AND shoe = '{shoe_info.shoe}' AND EMTIR = '{EMTIR}'
            ORDER BY pace1 ASC 
            """)
            print(avg_pace_sql)
            result = session.execute(avg_pace_sql)

            total_distance = 0
            mul_pace1 = 0
            mul_performance = 0
            for row in result:
                # print(row)
                distance = float(row[2])
                pace1 = row[3]
                performance = row[4]
                total_distance += distance
                mul_pace1 += distance * pace1
                mul_performance += distance * performance

            if total_distance != 0:
                avg_pace1 = mul_pace1 / total_distance
                avg_performance = mul_performance /total_distance
                avg_pace = pace1_to_pace2(avg_pace1)
            else:
                avg_pace = "10:00"
                avg_performance = 1


            distance_mul_heart_rate = 0
            distance_mul_run_time_second = 0
            distance_mul_cadence = 0
            distance_mul_stride_length = 0
            distance_mul_speed = 0

            distance_sum = 0
            used_time_sum = 0

            # real_used_times = 0 # 里程大于1的使用次数
            # real_used_distance = 0 # 里程大于1的使用距离

            for record in session.query(DailyShoeRecord).filter(DailyShoeRecord.shoe == shoe_info.shoe,
                                                                DailyShoeRecord.EMTIR == EMTIR,
                                                                DailyShoeRecord.date <= start,
                                                                DailyShoeRecord.distance >= 1):
                if int(record.average_heart_rate) == 0 or int(record.cadence) == 0:
                    continue
                else:
                    record_distance = float(record.distance)
                    if record_distance < 1:
                        continue
                        # real_used_times += 1
                        # real_used_distance += record.distance

                    second = time_to_second(record.used_time)
                    speed = 1000 * record_distance / second  # 米/秒
                    stride_length = round(speed / (int(record.cadence) / 60), 2)  # 线转换为步/秒
                    pace1 = 1 / (speed * 60 / 1000)
                    pace = pace1_to_pace2(pace1)

                    distance_mul_speed += record_distance * speed
                    distance_mul_stride_length += record_distance * stride_length

                    distance_sum += record_distance
                    used_time_sum += 1
                    distance_mul_heart_rate += record_distance * int(record.average_heart_rate)
                    distance_mul_cadence += record_distance * int(record.cadence)
                    distance_mul_run_time_second += record_distance * second

            if distance_sum != 0:
                a.weight_avg_heart_rate = round(distance_mul_heart_rate / distance_sum, 2)
                a.weight_avg_cadence = round(distance_mul_cadence / distance_sum, 2)
                a.weight_avg_run_time = second_to_time(distance_mul_run_time_second / distance_sum)
                a.weight_avg_stride_length = round(distance_mul_stride_length / distance_sum, 2)
                weight_avg_speed = distance_mul_speed / distance_sum
                a.weight_avg_pace = pace1_to_pace2(1 / (weight_avg_speed * 60 / 1000))
            else:
                a.weight_avg_heart_rate = 0
                a.weight_avg_cadence = 0
                a.weight_avg_run_time = ""
                a.weight_avg_stride_length = 0
                a.weight_avg_pace = ""

            # if real_used_distance == 0:
            #     a.avg_distance = 0
            # else:
            if used_time_sum == 0:
                a.avg_distance = 0
            else:
                a.avg_distance = round(distance_sum / used_time_sum, 2)

            # 每个shoe的top3跑步数据
            top1_pace1 = 0
            top1_performance = 0

            top3_weight_avg_pace1 = 0
            top3_weight_avg_performance = 0

            top3_sum_distance = 0
            top3_mul_pace1 = 0
            top3_mul_performance = 0

            # todo: bug,按照pace1排序，可能top1 performance无法获取到
            sql_top3 = text(f"""
            SELECT `date`, shoe, distance, TIME_TO_SEC(STR_TO_DATE(used_time, '%H:%i:%s'))/60/distance AS pace1,
            60/(TIME_TO_SEC(STR_TO_DATE(used_time, '%H:%i:%s'))/60/distance)/average_heart_rate*100 AS performance_schema,
            average_heart_rate, cadence, `type`
            FROM `running_shoe_record` WHERE distance >= 1 AND average_heart_rate != 0
            AND shoe = '{shoe_info.shoe}' and EMTIR = '{EMTIR}'
            ORDER BY pace1 ASC 
            """)
            print(sql_top3)
            result = session.execute(sql_top3)
            for row in result:
                # print(row)
                distance = float(row[2])
                pace1 = row[3]
                performance = row[4]

                if top1_pace1 == 0:
                    top1_pace1 = pace1
                    top1_performance = performance

                if top1_pace1 > pace1:
                    top1_pace1 = pace1
                if top1_performance < performance:
                    top1_performance = performance

            #     top3_sum_distance += distance
            #     top3_mul_pace1 += distance * pace1
            #     top3_mul_performance += distance * performance
            #
            # if top3_sum_distance != 0:
            #     top3_weight_avg_pace1 = top3_mul_pace1 / top3_sum_distance
            #     top3_weight_avg_performance = top3_mul_performance / top3_sum_distance
            # print("top1:", top1_pace1, pace1_to_pace2(top1_pace1), top1_performance)
            # print("top3:", top3_weight_avg_pace1, pace1_to_pace2(top3_weight_avg_pace1), top3_weight_avg_performance)

            a.top1_pace = pace1_to_pace2(top1_pace1)
            a.top1_performance = round(top1_performance, 2)

            # a.top3_pace = pace1_to_pace2(top3_weight_avg_pace1)
            # a.top3_performance = round(top3_weight_avg_performance, 2)

            # rq1，rq3，rq数据
            rq1 = ""
            rq3 = ""
            rq = ""

            rq_sql = text(f"""
            SELECT shoe, distance, rq 
            FROM `running_shoe_record`
            WHERE distance >= 1 AND average_heart_rate != 0 AND rq != ''
            AND shoe='{shoe_info.shoe}' and EMTIR = '{EMTIR}'
            ORDER BY rq DESC""")
            result = session.execute(rq_sql)
            for row in result:
                # distance = float(row[1])
                rq1 = float(row[2])
                break

            distance_mul_rq3 = 0
            distance_sum3 = 0
            count = 0  # 循环3次
            result = session.execute(rq_sql)
            for row in result:
                if row[2]:
                    distance = float(row[1])
                    rq = float(row[2])
                    distance_sum3 += distance
                    distance_mul_rq3 += distance * rq
                else:
                    distance_sum += 0
                count += 1
                if count >= 3:
                    break

            if distance_sum3 != 0:
                rq3 = round(distance_mul_rq3 / distance_sum3, 2)

            distance_mul_rq = 0
            distance_sum = 0
            result = session.execute(rq_sql)
            for row in result:
                if row[2]:
                    distance = float(row[1])
                    rq = float(row[2])
                    distance_sum += distance
                    distance_mul_rq += distance * rq
                else:
                    distance_sum += 0

            if distance_sum != 0:
                rq = round(distance_mul_rq / distance_sum, 2)

            a.rq1 = rq1
            a.rq3 = rq3
            a.rq = rq

            # 处理rq_inc
            rq_inc_sql = text(f"""
            SELECT shoe, rq_inc
            FROM `running_shoe_record`
            WHERE distance >= 1 AND average_heart_rate != 0 AND rq_inc != '' and rq_inc >0
            AND shoe='{shoe_info.shoe}' 
            AND EMTIR = '{EMTIR}'
            ORDER BY rq_inc DESC""")
            result = session.execute(rq_inc_sql)
            rq_inc1 = ""
            for row in result:
                rq_inc1 = float(row[1])
                break

            result = session.execute(rq_inc_sql)
            rq_inc3 = 0
            rq_inc3_sum = 0
            count = 0
            for row in result:
                rq_inc = float(row[1])
                rq_inc3_sum += rq_inc
                count += 1
                if count >= 3:
                    break
            if count == 0:
                rq_inc3 = ""
            else:
                rq_inc3 = rq_inc3_sum / count

            rq_inc_sql = text(f"""
            SELECT shoe, rq_inc
            FROM `running_shoe_record`
            WHERE distance >= 1 AND average_heart_rate != 0 AND rq_inc != ''  
            AND shoe='{shoe_info.shoe}' 
            AND EMTIR = '{EMTIR}'
            ORDER BY rq_inc DESC""")  # 保留rq_inc为负的
            result = session.execute(rq_inc_sql)
            rq_inc_sum = 0
            count = 0
            for row in result:
                rq_inc_ = float(row[1])
                rq_inc_sum += rq_inc_
                count += 1
            if count == 0:
                rq_inc = ""
            else:
                rq_inc = rq_inc_sum / count

            a.rq_inc1 = rq_inc1
            a.rq_inc3 = rq_inc3
            a.rq_inc = rq_inc

            a.avg_performance = avg_performance
            a.avg_pace = avg_pace
            try:
                session.add(a)
                session.commit()
            except Exception as e:
                session.rollback()
                print(e)


def handle_daily_shoe_stats(start):
    print(start)
    for shoe_info in session.query(ShoeInfo).all():
        # if shoe_info.shoe != "乔丹 强风SE":
        #     continue
        # if session.query(DailyShoeStats).filter(DailyShoeStats.date == start).filter(
        #         DailyShoeStats.shoe == shoe_info.shoe).count != 0:
        count = session.query(DailyShoeStats).filter(DailyShoeStats.date == start,
                                                     DailyShoeStats.shoe == shoe_info.shoe).count()
        if count != 0:  # 可以一日多次运行，进行update操作
            a = session.query(DailyShoeStats).filter(DailyShoeStats.date == start,
                                                     DailyShoeStats.shoe == shoe_info.shoe).first()
        else:
            a = DailyShoeStats()
        a.date = start
        a.shoe = shoe_info.shoe
        a.uptime = datetime.datetime.now()

        if a.shoe == "李宁 赤兔6 PRO":
            print(a)

        a.total_used_times = session.query(DailyShoeRecord).filter(DailyShoeRecord.shoe == shoe_info.shoe,
                                                                   DailyShoeRecord.date <= start).count()
        if a.total_used_times == 0:
            continue

        sql = text(
            f"select sum(distance) from `running_shoe_record` where date <= '{start}' and shoe = '{shoe_info.shoe}'")
        print(sql)
        result = session.execute(sql)
        for row in result:
            a.total_distance = row[0]
        if a.total_distance is None:
            a.total_distance = 0
        a.total_distance = round(a.total_distance, 2)

        # if a.total_used_times != 0:
        #     a.avg_distance = round(a.total_distance / a.total_used_times, 2)
        # else:
        #     a.avg_distance = 0

        distance_mul_heart_rate = 0
        distance_mul_run_time_second = 0
        distance_mul_cadence = 0
        distance_mul_stride_length = 0
        distance_mul_speed = 0

        distance_sum = 0
        used_time_sum = 0

        # real_used_times = 0 # 里程大于1的使用次数
        # real_used_distance = 0 # 里程大于1的使用距离

        for record in session.query(DailyShoeRecord).filter(DailyShoeRecord.shoe == shoe_info.shoe,
                                                            DailyShoeRecord.date <= start,
                                                            DailyShoeRecord.distance >= 1):
            if int(record.average_heart_rate) == 0 or int(record.cadence) == 0:
                continue
            else:
                record_distance = float(record.distance)
                if record_distance < 1:
                    continue
                    # real_used_times += 1
                    # real_used_distance += record.distance

                second = time_to_second(record.used_time)
                speed = 1000 * record_distance / second  # 米/秒
                stride_length = round(speed / (int(record.cadence) / 60), 2)  # 线转换为步/秒
                pace1 = 1 / (speed * 60 / 1000)
                pace = pace1_to_pace2(pace1)

                distance_mul_speed += record_distance * speed
                distance_mul_stride_length += record_distance * stride_length

                distance_sum += record_distance
                used_time_sum += 1
                distance_mul_heart_rate += record_distance * int(record.average_heart_rate)
                distance_mul_cadence += record_distance * int(record.cadence)
                distance_mul_run_time_second += record_distance * second

        if distance_sum != 0:
            a.weight_avg_heart_rate = round(distance_mul_heart_rate / distance_sum, 2)
            a.weight_avg_cadence = round(distance_mul_cadence / distance_sum, 2)
            a.weight_avg_run_time = second_to_time(distance_mul_run_time_second / distance_sum)
            a.weight_avg_stride_length = round(distance_mul_stride_length / distance_sum, 2)
            weight_avg_speed = distance_mul_speed / distance_sum
            a.weight_avg_pace = pace1_to_pace2(1 / (weight_avg_speed * 60 / 1000))
        else:
            a.weight_avg_heart_rate = 0
            a.weight_avg_cadence = 0
            a.weight_avg_run_time = ""
            a.weight_avg_stride_length = 0
            a.weight_avg_pace = ""

        # if real_used_distance == 0:
        #     a.avg_distance = 0
        # else:
        if used_time_sum == 0:
            a.avg_distance = 0
        else:
            a.avg_distance = round(distance_sum / used_time_sum, 2)

        # 每个shoe的top3跑步数据
        top1_pace1 = 0
        top1_performance = 0

        top3_weight_avg_pace1 = 0
        top3_weight_avg_performance = 0

        top3_sum_distance = 0
        top3_mul_pace1 = 0
        top3_mul_performance = 0

        # todo: bug,按照pace1排序，可能top1 performance无法获取到
        sql_top3 = text(f"""
        SELECT `date`, shoe, distance, TIME_TO_SEC(STR_TO_DATE(used_time, '%H:%i:%s'))/60/distance AS pace1,
        60/(TIME_TO_SEC(STR_TO_DATE(used_time, '%H:%i:%s'))/60/distance)/average_heart_rate*100 AS performance_schema,
        average_heart_rate, cadence, `type`
        FROM `running_shoe_record` WHERE distance >= 1 AND average_heart_rate != 0
        AND shoe = '{shoe_info.shoe}'
        ORDER BY pace1 ASC 
        """)
        print(sql_top3)
        result = session.execute(sql_top3)
        for row in result:
            # print(row)
            distance = float(row[2])
            pace1 = row[3]
            performance = row[4]

            if top1_pace1 == 0:
                top1_pace1 = pace1
                top1_performance = performance

            if top1_pace1 > pace1:
                top1_pace1 = pace1
            if top1_performance < performance:
                top1_performance = performance

        #     top3_sum_distance += distance
        #     top3_mul_pace1 += distance * pace1
        #     top3_mul_performance += distance * performance
        #
        # if top3_sum_distance != 0:
        #     top3_weight_avg_pace1 = top3_mul_pace1 / top3_sum_distance
        #     top3_weight_avg_performance = top3_mul_performance / top3_sum_distance
        # print("top1:", top1_pace1, pace1_to_pace2(top1_pace1), top1_performance)
        # print("top3:", top3_weight_avg_pace1, pace1_to_pace2(top3_weight_avg_pace1), top3_weight_avg_performance)

        a.top1_pace = pace1_to_pace2(top1_pace1)
        a.top1_performance = round(top1_performance, 2)

        # a.top3_pace = pace1_to_pace2(top3_weight_avg_pace1)
        # a.top3_performance = round(top3_weight_avg_performance, 2)

        # rq1，rq3，rq数据
        rq1 = ""
        rq3 = ""
        rq = ""

        rq_sql = text(f"""
        SELECT shoe, distance, rq 
        FROM `running_shoe_record`
        WHERE distance >= 1 AND average_heart_rate != 0 AND rq != ''
        AND shoe='{shoe_info.shoe}' ORDER BY rq DESC""")
        result = session.execute(rq_sql)
        for row in result:
            # distance = float(row[1])
            rq1 = float(row[2])
            break

        distance_mul_rq3 = 0
        distance_sum3 = 0
        count = 0  # 循环3次
        result = session.execute(rq_sql)
        for row in result:
            if row[2]:
                distance = float(row[1])
                rq = float(row[2])
                distance_sum3 += distance
                distance_mul_rq3 += distance * rq
            else:
                distance_sum += 0
            count += 1
            if count >= 3:
                break

        if distance_sum3 != 0:
            rq3 = round(distance_mul_rq3 / distance_sum3, 2)

        distance_mul_rq = 0
        distance_sum = 0
        result = session.execute(rq_sql)
        for row in result:
            if row[2]:
                distance = float(row[1])
                rq = float(row[2])
                distance_sum += distance
                distance_mul_rq += distance * rq
            else:
                distance_sum += 0

        if distance_sum != 0:
            rq = round(distance_mul_rq / distance_sum, 2)

        a.rq1 = rq1
        a.rq3 = rq3
        a.rq = rq

        # 处理rq_inc
        rq_inc_sql = text(f"""
        SELECT shoe, rq_inc
        FROM `running_shoe_record`
        WHERE distance >= 1 AND average_heart_rate != 0 AND rq_inc != '' and rq_inc >0
        AND shoe='{shoe_info.shoe}' ORDER BY rq_inc DESC""")
        result = session.execute(rq_inc_sql)
        rq_inc1 = ""
        for row in result:
            rq_inc1 = float(row[1])
            break

        result = session.execute(rq_inc_sql)
        rq_inc3 = 0
        rq_inc3_sum = 0
        count = 0
        for row in result:
            rq_inc = float(row[1])
            rq_inc3_sum += rq_inc
            count += 1
            if count >= 3:
                break
        if count == 0:
            rq_inc3 = ""
        else:
            rq_inc3 = rq_inc3_sum / count

        rq_inc_sql = text(f"""
        SELECT shoe, rq_inc
        FROM `running_shoe_record`
        WHERE distance >= 1 AND average_heart_rate != 0 AND rq_inc != ''  
        AND shoe='{shoe_info.shoe}' ORDER BY rq_inc DESC""")  # 保留rq_inc为负的
        result = session.execute(rq_inc_sql)
        rq_inc_sum = 0
        count = 0
        for row in result:
            rq_inc_ = float(row[1])
            rq_inc_sum += rq_inc_
            count += 1
        if count == 0:
            rq_inc = ""
        else:
            rq_inc = rq_inc_sum / count

        a.rq_inc1 = rq_inc1
        a.rq_inc3 = rq_inc3
        a.rq_inc = rq_inc

        try:
            session.add(a)
            session.commit()
        except Exception as e:
            session.rollback()
            print(e)


def raw_data_2_db(start):
    shoe_info_dict = read_shoe_info_csv()
    for shoe, v in shoe_info_dict.items():
        # if session.query(ShoeInfo).filter(ShoeInfo.shoe == shoe)
        if not session.query(exists().where(ShoeInfo.shoe == shoe)).scalar():  # 新鞋
            a = ShoeInfo()
            a.shoe = shoe
            a.brand = v["brand"]
            a.price = v["price"]
            a.color = v["color"]
            a.start_date = v["start_date"]
            a.end_date = v["end_date"]
            a.shortage = v["shortage"]
            a.uptime = datetime.datetime.now()

            try:
                session.add(a)
                session.commit()
            except Exception as e:
                session.rollback()
                print(e)

    # Read CSV data from the file
    with open('C:\git\Quant\Home\Running\Shoe\\records.csv', 'r', encoding='utf-8') as csv_file:
        # Parse CSV data and populate the dictionary
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            if not session.query(exists().where(DailyShoeRecord.date == row["date"],
                                                DailyShoeRecord.shoe == row["shoe"],
                                                DailyShoeRecord.distance == row["distance"],
                                                DailyShoeRecord.used_time == row["used_time"],
                                                DailyShoeRecord.average_heart_rate == row["average_heart_rate"],
                                                DailyShoeRecord.cadence == row["cadence"],
                                                DailyShoeRecord.type == row["type"])).scalar():  # 新record

                print(row)
                o = DailyShoeRecord()
                o.date = row["date"]
                o.shoe = row["shoe"]
                o.distance = row["distance"]
                o.used_time = row["used_time"]
                o.average_heart_rate = row["average_heart_rate"]
                o.cadence = row["cadence"]
                o.type = row["type"]
                o.rq = row["rq"]
                o.EMTIR = row["EMTIR"]

                # 计算rq_inc
                rq_inc = float(row["rq"]) - float(DailyRQRecord.get_recent_rq(row["date"]))
                o.rq_inc = round(rq_inc, 2)
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
    raw_data_2_db(today.strftime("%F"))

    # 计算统计数据
    handle_daily_shoe_stats(today.strftime("%F"))

    # 计算EMTIR各类型的统计数据
    handle_daily_shoe_stats_EMTIR(today.strftime("%F"))
    cal_shoe_score(today.strftime("%F"))

    # 计算当月鞋子数据
    # handle_daily_shoe_stats_current_month("2024-02-29")
    handle_daily_shoe_stats_current_month(today.strftime("%F"))


if __name__ == '__main__':
    # 处理rq record数据到mysql
    from rq_2_db import main as rq_2_db_main

    rq_2_db_main()

    main()
