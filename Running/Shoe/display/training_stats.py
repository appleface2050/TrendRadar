import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import pandas as pd
import numpy as np

from Home.Running.Shoe.display.util import cal_pace_performance

df = pd.read_csv('C:\\git\\Quant\\Home\\Running\\Shoe\\records.csv')
rq = pd.read_csv('C:\\git\\Quant\\Home\\Running\\RQ\\rq.csv')
rq.rename(columns={"日期": "date"}, inplace=True)
rq.set_index("date", inplace=True)
rq = rq[["RQ"]]

df.set_index("date", inplace=True)
df = cal_pace_performance(df)
df = df.rename(columns={"average_heart_rate": "bpm"})
df = df.rename(columns={"performance": "PFM"})

df = pd.merge(df, rq, left_on=df.index, right_on=rq.index).set_index("key_0")
df["rq_inc"] = df["rq"] - df["RQ"]
df.drop(["RQ", "type"], axis=1, inplace=True)
df.dropna(inplace=True)
df.index.names = ["date"]

# df["month"] = df.index.astype("datetime64[M]")
df.index = pd.to_datetime(df.index)
df['month'] = df.index.to_period('M').astype(str)

SHOE_LIST = ["特步 160X 3.0 PRO", "Saucony Triumph 18", "乔丹 飞影Plaid 1.5", "鸿星尔克 芷境2", "必迈 远征者5.0",
             "必迈 惊碳Fly", "特步 160X 5.0", "adidas adizero Boston 12", "乔丹 强风2.0", "New Balance FuelCell Rebel v3",
             "必迈 惊碳3.0 TURBO"]
SHOE_LIST_3_2 = ["特步 160X 3.0 PRO", "乔丹 飞影Plaid 1.5", "鸿星尔克 芷境2", "必迈 远征者5.0",
                 "必迈 惊碳Fly", "特步 160X 5.0", "adidas adizero Boston 12", "乔丹 强风2.0", "New Balance FuelCell Rebel v3",
                 "必迈 惊碳3.0 TURBO"]
# 显示所有行和列
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
print(
    "---------------------------------------1. --------------------------------------------------------------------------------------")

print(df[["rq_inc", "PFM", "rq"]].loc[(df["distance"] >= 1)].dropna().tail(200).agg(["mean", "std"]).round(3))
print(df[["rq_inc", "PFM", "rq"]].loc[(df["distance"] >= 1)].dropna().tail(100).agg(["mean", "std"]).round(3))
print(df[["rq_inc", "PFM", "rq"]].loc[(df["distance"] >= 1)].dropna().tail(50).agg(["mean", "std"]).round(3))
print(df[["rq_inc", "PFM", "rq"]].loc[(df["distance"] >= 1)].dropna().tail(25).agg(["mean", "std"]).round(3))
print(df[["rq_inc", "PFM", "rq"]].loc[(df["distance"] >= 1)].dropna().tail(13).agg(["mean", "std"]).round(3))
print(
    "---------------------------------------2. --------------------------------------------------------------------------------------")

print(df[["EMTIR", "rq_inc", "PFM", "rq"]].loc[(df["distance"] >= 1)].dropna().groupby(["EMTIR"]).agg(
    ["mean", "std"]).round(2))

print(
    "---------------------------------------3.1 每种EMTIR，每个鞋子的数据--------------------------------------------------------------------------------------")

print(df[["EMTIR", "shoe", "rq_inc", "rq", "PFM"]].loc[(df["distance"] >= 1)].dropna().groupby(["EMTIR", "shoe"]).agg(
    ["mean", "std"]).round(2))

print(
    "---------------------------------------3.2 每双鞋子，每种EMTIR的数据--------------------------------------------------------------------------------------")

# print(df[["EMTIR", "shoe", "rq_inc", "rq", "PFM"]].loc[(df["distance"] >= 1)].dropna().groupby(["shoe", "EMTIR"]).agg(
#     ["mean", "std"]).round(2))
# SHOE_LIST_3_2
# df_33_tmp = df.loc[df["shoe"].isin(SHOE_LIST)]
# df_33_tmp = df[["EMTIR", "shoe", "rq_inc", "rq", "PFM"]].loc[
#     (df["distance"] >= 1)].dropna().groupby(
#     ["shoe", "EMTIR"]).agg(
#     {"rq": ["mean", "std"], "rq_inc": ["mean", "std"], "PFM": ["mean", "std"]}).round(2)

df_33_tmp = df[["EMTIR", "shoe", "rq_inc", "rq", "PFM"]].loc[
    (df["distance"] >= 1) & (df["shoe"].isin(SHOE_LIST))].dropna().groupby(
    ["shoe", "EMTIR"]).agg(
    {"rq": ["mean", "std"], "rq_inc": ["mean", "std"], "PFM": ["mean", "std"]}).round(2)
df_33_tmp.columns = ["rq_mean", "rq_std", "rq_inc_mean", "rq_inc_std", "PFM_mean", "PFM_std"]
df_33_tmp.reset_index(inplace=True, drop=True)

df_33 = df[["EMTIR", "shoe", "rq_inc", "rq", "PFM"]].loc[
    (df["distance"] >= 1) & (df["shoe"].isin(SHOE_LIST))].dropna().groupby(["shoe", "EMTIR"]).agg(
    {"rq": ["count"]}).round(2)
df_33.reset_index(inplace=True)
df_33.columns = ["shoe", "EMTIR", "count"]
df_33['total'] = df_33.groupby('shoe')['count'].transform('sum')
df_33['proportion'] = df_33['count'] / df_33['total']

df_33 = pd.merge(df_33, df_33_tmp, left_on=df_33.index, right_on=df_33_tmp.index, how="inner")

df_33 = df_33[['shoe', 'EMTIR', 'count', 'proportion', "rq_inc_mean", "rq_mean", "PFM_mean", "rq_inc_std", "rq_std",
               "PFM_std"
               ]]
df_33 = df_33[df_33["shoe"].isin(SHOE_LIST_3_2)]

pd.set_option("display.width", 5000)

print(df_33[['shoe', 'EMTIR', 'count', 'proportion', "rq_inc_mean", "rq_mean", "PFM_mean", "rq_inc_std", "rq_std",
             "PFM_std"
             ]].set_index("shoe").round(2))

print(
    "---------------------------------------4. 月度数据--------------------------------------------------------------------------------------")

print(df[["month", "rq_inc", "PFM", "rq"]].loc[(df["distance"] >= 1)].dropna().groupby(["month"]).agg(
    ["mean", "std"]).round(2))

print(
    "---------------------------------------5. 长距离--------------------------------------------------------------------------------------")

# SHOE_LIST = ["特步 160X 3.0 PRO", "乔丹 强风SE 秋冬版", "乔丹 飞影Plaid 1.5", "鸿星尔克 芷境2", "必迈 远征者5.0", "必迈 惊碳Fly", "特步 160X 5.0",
#              "adidas adizero Boston 12"]
print(
    df.loc[
        (df["shoe"].isin(SHOE_LIST)) & (df.index >= "2020-09-01") & (df["distance"] >= 17), ["distance", "rq", "rq_inc",
                                                                                             "pace", "bpm", "PFM",
                                                                                             "shoe"]].tail(30)
)

EMTIR = "T"
print(
    f"---------------------------------------6. 某个EMTIR({EMTIR})现役shoe详细数据(最近10条数据)--------------------------------------------------------------------------------------")
df_6 = pd.DataFrame()
for shoe in SHOE_LIST:
    result = df.loc[(df["EMTIR"].isin([EMTIR])) & (df["shoe"].isin([shoe])) & (df.index >= "2020-09-01") & (
            df["distance"] >= 1), ["shoe", "distance", "rq", "rq_inc", "pace", "bpm", "PFM"]].tail(5).reset_index()
    if not result.empty:
        df_6 = pd.concat([df_6, result], axis=0)

print(df_6.set_index("date").sort_values("date")[["distance", "rq_inc", "rq", "pace", "bpm", "PFM", "shoe"]])
