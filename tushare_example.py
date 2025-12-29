import tushare as ts
# 找到 ts.pro_api 所在行
pro = ts.pro_api()
# ⬇️ 在 ts.pro_api之后 添加以下两行
pro._DataApi__token 	= '4952632215960276804'   # ⬅️你拿到token以后，必须替换进此行
pro._DataApi__http_url 	= 'http://1w1a.xiximiao.com/dataapi'
# ⬆️ 添加两行代码 /结束 ===kwp===

# ==⬇️你原有的调用代码不用变
# ========= daily 日线接口 ============
df = pro.daily(trade_date='20180810',limit=20)
print(df)
# =========  交易日历 =========
df_cal = pro.trade_cal(exchange='', start_date='20250101', end_date='20251231' ,limit=5, offset=0)
print(df_cal)
# ========= 5000积分验证 ======
# dfkpl_concept_cons = pro.kpl_concept_cons(trade_date='20241014')
# print(dfkpl_concept_cons)
# ========= 10000积分验证 =======
dflimit_list_ths = pro.limit_list_ths(trade_date='20241125', limit_type='涨停池', fields='ts_code,trade_date,tag,status,lu_desc')
print(dflimit_list_ths)