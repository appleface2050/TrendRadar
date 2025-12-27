"""
RunningV2 Web Dashboard - Flask API 服务
单文件 Flask 应用，提供数据查询和 Prophet 预测 API
"""
import sys
sys.path.insert(0, '/home/shang/git')
sys.path.insert(0, '/home/shang/git/Indeptrader')

from flask import Flask, render_template, jsonify
import pandas as pd
from prophet import Prophet
from Running.running_models import engine_running

app = Flask(__name__)


@app.route('/')
def index():
    """Dashboard 主页"""
    return render_template('index.html')


@app.route('/api/rq/history')
def get_rq_history():
    """
    获取历史 RQ 数据
    返回：JSON 格式的历史数据 [{date, rq}, ...]
    """
    try:
        # 从 MySQL 读取数据
        query = 'SELECT date, rq FROM running_rq_record ORDER BY date'
        df = pd.read_sql(query, con=engine_running)

        # 转换为 JSON 格式
        data = df.to_dict('records')

        return jsonify({
            'success': True,
            'data': data,
            'count': len(data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/rq/forecast')
def get_rq_forecast():
    """
    获取 RQ 预测数据
    返回：JSON 格式的历史数据和预测数据
    """
    try:
        # 1. 从 MySQL 读取历史 RQ 数据
        query = 'SELECT date, rq FROM running_rq_record ORDER BY date'
        df = pd.read_sql(query, con=engine_running)

        # 2. 使用 Prophet 预测
        # 重命名列为 Prophet 要求的格式
        df_prophet = df.rename(columns={"date": "ds", "rq": "y"})

        # 创建并拟合模型
        m = Prophet(daily_seasonality=False)
        m.fit(df_prophet)

        # 生成未来 30 天的日期
        future = m.make_future_dataframe(periods=30)
        forecast = m.predict(future)

        # 3. 准备返回数据
        # 历史数据
        history_data = df.to_dict('records')

        # 预测数据（只返回需要的字段）
        forecast_data = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].to_dict('records')

        return jsonify({
            'success': True,
            'history': history_data,
            'forecast': forecast_data,
            'history_count': len(history_data),
            'forecast_count': len(forecast_data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/rq/stats')
def get_rq_stats():
    """
    获取 RQ 统计信息
    返回：当前值、最大值、最小值、平均值等
    """
    try:
        # 从 MySQL 读取数据
        query = 'SELECT rq FROM running_rq_record WHERE rq != "" AND rq != "0"'
        df = pd.read_sql(query, con=engine_running)

        # 转换为数值类型
        df['rq'] = pd.to_numeric(df['rq'], errors='coerce')
        df = df.dropna()

        if len(df) == 0:
            return jsonify({
                'success': False,
                'error': '没有有效数据'
            }), 404

        # 计算统计数据
        current_rq = float(df.iloc[-1]['rq'])
        max_rq = float(df['rq'].max())
        min_rq = float(df['rq'].min())
        avg_rq = float(df['rq'].mean())
        count = len(df)

        return jsonify({
            'success': True,
            'current': current_rq,
            'max': max_rq,
            'min': min_rq,
            'avg': avg_rq,
            'count': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("RunningV2 Dashboard 启动中...")
    print("访问地址: http://localhost:5000")
    print("API 端点:")
    print("  - GET  /                 : Dashboard 主页")
    print("  - GET  /api/rq/history   : 历史数据")
    print("  - GET  /api/rq/forecast  : 预测数据")
    print("  - GET  /api/rq/stats     : 统计信息")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)
