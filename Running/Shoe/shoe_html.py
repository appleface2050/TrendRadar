from jinja2 import Environment, FileSystemLoader
import pandas as pd
import numpy as np
import datetime

# Your data


from Home.Running.Shoe.shoe import cal_table_result, read_shoe_info_csv, records, fangcheng, read_run_records_csv


def cal_html_data():
    shoe_info = read_shoe_info_csv()
    # shoe_names = list(records.keys())
    shoe_names = list(shoe_info.keys())
    records_v2 = read_run_records_csv()

    months = sorted(set(month for data in records.values() for month in data.keys()))

    # Extracting the corresponding values for each shoe and each month
    values = np.zeros((len(shoe_names), len(months)))

    for i, shoe_name in enumerate(shoe_names):
        data = records[shoe_name]
        values[i, :] = [data.get(month, 0) for month in months]

    result = []

    # 期望每公里钱数
    # expected_unit_price = 0.8

    for i in range(len(shoe_names)):
        shoe_name = shoe_names[i]
        used_km = round(np.sum(values[i, :]), 1)
        # price = shoe_prices[shoe_names[i]]
        price = shoe_info[shoe_names[i]]["price"]

        unit_price = round((price / used_km), 2)
        expected_km = int(price / 0.8)
        marginal_km = round(price / (price / used_km - 0.1) - used_km, 2)  # unit price降低0.1需要的公里数

        # marginal_unit_price 变为100需要的公里数
        # total_km**2 + 100total_km -1000price = 0 计算一元二次方程
        r = fangcheng(1, 100, -1000 * price)
        # print(r)
        expected_total_km = int(r[0])
        expected_unit_price = round(price / r[0], 2)
        # marginal_unit_price_100_km = str(
        #     marginal_unit_price_100_km) + " (%s)" % marginal_unit_price_100_km_unit_price

        progress = round(used_km / expected_total_km, 2)

        start_date = shoe_info[shoe_names[i]]["start_date"]
        end_date = shoe_info[shoe_names[i]]["end_date"]

        # 最近30日消耗量
        # 最近90日消耗量
        # 最近365日消耗量
        # 是否退役
        # 服役月数
        start_datetime = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_datetime = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        else:
            end_datetime = datetime.datetime.now()

        days_difference = (end_datetime - start_datetime).days
        used_month = int(days_difference / 30)
        # 服役期间评价每月消耗量
        used_km_per_month = round(used_km / (days_difference / 30), 2)
        # 预计达到marginal_unit_price_100_km到还有多少个月

        # 单个鞋子数据
        # 单个鞋子的使用柱状图
        # 距离上次使用的天数
        last_used_date = ""

        result.append({
            "shoe_name": shoe_name, "total_km": used_km, "price": price, "unit_price": unit_price,
            "expected_km": expected_km,
            "marginal_km": marginal_km,
            "expected_total_km": expected_total_km,
            "expected_unit_price": expected_unit_price,
            "progress": progress,
            "start_date": start_date,
            "end_date": end_date,
            "used_month": used_month,
            "used_km_per_month": used_km_per_month,
        })
    # print(result)

    # 排序
    result = sorted(result, key=lambda x: x['start_date'], reverse=True)

    return result


def shoe_stats_html():
    data = cal_html_data()

    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('template/shoes_stats.html')
    html_output = template.render(data=data)
    with open('shoe_stats.html', 'w', encoding='utf-8') as f:
        f.write(html_output)
        print('shoe_stats.html')


if __name__ == '__main__':
    shoe_stats_html()
