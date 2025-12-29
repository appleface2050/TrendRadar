"""
宏观交易策略 - Streamlit监控仪表盘

实时监控宏观状态、择时信号、风险指数等

功能：
1. 宏观状态概率监控
2. Nowcasting预测路径
3. 复合风险指数
4. 择时信号
5. 行业权重建议
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 页面配置
st.set_page_config(
    page_title="宏观交易策略监控",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-title {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .positive {
        color: #00cc00;
        font-weight: bold;
    }
    .negative {
        color: #ff4d4d;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """
    加载数据（缓存）

    Returns:
    --------
    dict
        包含各类数据
    """
    data = {}

    try:
        # 加载宏观得分
        data['macro_scores'] = pd.read_csv(
            'data/derived/indicators/macro_scores.csv',
            parse_dates=['date'],
            index_col='date'
        )
    except:
        data['macro_scores'] = None

    try:
        # 加载风险指数
        data['risk_index'] = pd.read_csv(
            'data/derived/indicators/composite_risk_index.csv',
            parse_dates=['date'],
            index_col='date'
        )
    except:
        data['risk_index'] = None

    try:
        # 加载区制概率
        data['regime_probs'] = pd.read_csv(
            'data/derived/indicators/regime_probabilities.csv',
            parse_dates=['date'],
            index_col='date'
        )
    except:
        data['regime_probs'] = None

    try:
        # 加载价格数据
        data['prices'] = pd.read_csv(
            'data/processed/china/hs300.csv',
            parse_dates=['date'],
            index_col='date'
        )
    except:
        data['prices'] = None

    return data


def render_header():
    """渲染页面标题"""
    st.markdown('<h1 class="main-title">📈 宏观交易策略监控仪表盘</h1>', unsafe_allow_html=True)
    st.markdown("---")


def render_sidebar(data):
    """渲染侧边栏"""
    st.sidebar.header("⚙️ 设置")

    # 日期范围
    st.sidebar.subheader("数据范围")
    if data['prices'] is not None:
        min_date = data['prices'].index.min()
        max_date = data['prices'].index.max()

        date_range = st.sidebar.slider(
            "选择日期范围",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="YYYY-MM-DD"
        )

        start_date, end_date = date_range
    else:
        start_date = datetime.now() - timedelta(days=365)
        end_date = datetime.now()
        st.sidebar.warning("未加载价格数据")

    # 策略参数
    st.sidebar.subheader("策略参数")
    macro_weight = st.sidebar.slider("宏观状态权重", 0.0, 1.0, 0.30, 0.05)
    liquidity_weight = st.sidebar.slider("流动性权重", 0.0, 1.0, 0.25, 0.05)
    valuation_weight = st.sidebar.slider("估值权重", 0.0, 1.0, 0.25, 0.05)
    sentiment_weight = st.sidebar.slider("情绪权重", 0.0, 1.0, 0.20, 0.05)

    # 风险管理
    st.sidebar.subheader("风险管理")
    risk_adjustment = st.sidebar.checkbox("启用风险调整", True)
    risk_threshold = st.sidebar.slider("高风险阈值", 0, 100, 70, 5)

    return {
        'start_date': start_date,
        'end_date': end_date,
        'macro_weight': macro_weight,
        'liquidity_weight': liquidity_weight,
        'valuation_weight': valuation_weight,
        'sentiment_weight': sentiment_weight,
        'risk_adjustment': risk_adjustment,
        'risk_threshold': risk_threshold
    }


def render_overview(data, params):
    """渲染概览页面"""
    st.header("📊 策略概览")

    # 创建3列布局
    col1, col2, col3, col4 = st.columns(4)

    # 当前宏观得分
    if data['macro_scores'] is not None:
        latest_macro = data['macro_scores'].iloc[-1]

        with col1:
            st.metric(
                label="宏观状态得分",
                value=f"{latest_macro.get('macro_score', 0):.1f}",
                delta=None
            )

        with col2:
            st.metric(
                label="流动性得分",
                value=f"{latest_macro.get('liquidity_score', 0):.1f}",
                delta=None
            )

        with col3:
            st.metric(
                label="估值得分",
                value=f"{latest_macro.get('valuation_score', 0):.1f}",
                delta=None
            )

        with col4:
            st.metric(
                label="情绪得分",
                value=f"{latest_macro.get('sentiment_score', 0):.1f}",
                delta=None
            )

    # 综合得分趋势图
    st.subheader("综合得分趋势")

    if data['macro_scores'] is not None:
        df = data['macro_scores'].loc[params['start_date']:params['end_date']]

        fig = go.Figure()

        # 添加综合得分线
        if 'composite_score' in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['composite_score'],
                mode='lines',
                name='综合得分',
                line=dict(color='#1f77b4', width=2)
            ))

        # 添加阈值线
        fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="高风险")
        fig.add_hline(y=35, line_dash="dash", line_color="green", annotation_text="低风险")

        fig.update_layout(
            title="宏观综合得分趋势",
            xaxis_title="日期",
            yaxis_title="得分",
            hovermode='x unified',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)


def render_regime(data, params):
    """渲染区制监控页面"""
    st.header("🎯 宏观状态识别")

    if data['regime_probs'] is None:
        st.warning("未加载区制概率数据")
        return

    df = data['regime_probs'].loc[params['start_date']:params['end_date']]

    # 当前区制
    latest = df.iloc[-1]

    regime_names = {
        'Regime_1': '正常增长',
        'Regime_2': '过热',
        'Regime_3': '衰退',
        'Regime_4': '滞胀'
    }

    # 找出最大概率的区制
    max_regime = max(
        [col for col in df.columns if col.startswith('Regime_')],
        key=lambda x: latest[x]
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="当前宏观状态",
            value=regime_names.get(max_regime, max_regime),
            delta=f"置信度: {latest[max_regime]:.1%}"
        )

    with col2:
        # 区制概率分布
        probs = {regime_names.get(k, k): latest[k] for k in df.columns if k.startswith('Regime_')}

        fig = go.Figure(go.Bar(
            x=list(probs.values()),
            y=list(probs.keys()),
            orientation='h',
            marker_color=['#00cc00' if v == max(probs.values()) else '#1f77b4' for v in probs.values()]
        ))

        fig.update_layout(
            title="区制概率分布",
            xaxis_title="概率",
            yaxis_title="",
            height=300
        )

        st.plotly_chart(fig, use_container_width=True)

    # 区制概率时序图
    st.subheader("区制概率演变")

    fig = go.Figure()

    colors = {
        'Regime_1': '#00cc00',
        'Regime_2': '#ffaa00',
        'Regime_3': '#ff4d4d',
        'Regime_4': '#9900cc'
    }

    for col in df.columns:
        if col.startswith('Regime_'):
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df[col],
                mode='lines',
                name=regime_names.get(col, col),
                line=dict(color=colors.get(col, '#1f77b4'))
            ))

    fig.update_layout(
        title="宏观状态概率演变",
        xaxis_title="日期",
        yaxis_title="概率",
        hovermode='x unified',
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def render_risk(data, params):
    """渲染风险监控页面"""
    st.header("⚠️ 风险监控")

    if data['risk_index'] is None:
        st.warning("未加载风险指数数据")
        return

    df = data['risk_index'].loc[params['start_date']:params['end_date']]

    # 当前风险水平
    latest = df.iloc[-1]
    current_risk = latest.get('risk_index', 50)

    # 风险等级判断
    if current_risk >= 70:
        risk_level = "高风险"
        risk_color = "🔴"
    elif current_risk >= 40:
        risk_level = "中等风险"
        risk_color = "🟠"
    else:
        risk_level = "低风险"
        risk_color = "🟢"

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="当前风险指数",
            value=f"{current_risk:.1f}",
            delta=None
        )

    with col2:
        st.metric(
            label="风险等级",
            value=risk_level,
            delta=None
        )

    with col3:
        # 风险趋势
        if len(df) > 5:
            recent_trend = df['risk_index'].iloc[-5:].mean()
            trend = current_risk - recent_trend
            st.metric(
                label="风险趋势",
                value="上升" if trend > 0 else "下降",
                delta=f"{trend:.1f}"
            )

    # 风险指数时序图
    st.subheader("风险指数趋势")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['risk_index'],
        mode='lines',
        name='风险指数',
        line=dict(color='#ff4d4d', width=2),
        fill='tozeroy',
        fillcolor='rgba(255, 77, 77, 0.1)'
    ))

    # 添加风险阈值线
    fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="高风险阈值")
    fig.add_hline(y=40, line_dash="dash", line_color="orange", annotation_text="中等风险阈值")

    fig.update_layout(
        title="复合风险指数",
        xaxis_title="日期",
        yaxis_title="风险指数 (0-100)",
        hovermode='x unified',
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def render_signals(data, params):
    """渲染择时信号页面"""
    st.header("📈 择时信号")

    # 生成信号（模拟）
    if data['macro_scores'] is not None:
        df = data['macro_scores'].loc[params['start_date']:params['end_date']]

        # 计算目标仓位
        df['position'] = df['composite_score'].apply(lambda x: min(max(x / 100, 0), 1))

        # 风险调整
        if data['risk_index'] is not None and params['risk_adjustment']:
            risk_df = data['risk_index'].loc[df.index]
            df['risk_adjusted_position'] = df['position'].copy()

            high_risk = risk_df['risk_index'] >= params['risk_threshold']
            df.loc[high_risk, 'risk_adjusted_position'] *= 0.5

            medium_risk = (
                (risk_df['risk_index'] >= 40) &
                (risk_df['risk_index'] < params['risk_threshold'])
            )
            df.loc[medium_risk, 'risk_adjusted_position'] *= 0.75

        # 当前仓位
        latest = df.iloc[-1]
        current_position = latest.get('risk_adjusted_position', latest.get('position', 0)) * 100

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label="建议仓位",
                value=f"{current_position:.0f}%",
                delta="看涨" if current_position > 50 else "看跌" if current_position < 30 else "中性"
            )

        with col2:
            # 信号判断
            if current_position >= 80:
                signal = "强烈买入"
                signal_emoji = "🚀"
            elif current_position >= 60:
                signal = "买入"
                signal_emoji = "📈"
            elif current_position >= 40:
                signal = "持有"
                signal_emoji = "➡️"
            elif current_position >= 20:
                signal = "卖出"
                signal_emoji = "📉"
            else:
                signal = "强烈卖出"
                signal_emoji = "⚠️"

            st.metric(
                label="交易信号",
                value=f"{signal_emoji} {signal}",
                delta=None
            )

        with col3:
            # 综合得分
            st.metric(
                label="综合得分",
                value=f"{latest['composite_score']:.1f}",
                delta=None
            )

        # 仓位和得分时序图
        st.subheader("仓位和得分趋势")

        fig = go.Figure()

        # 添加得分
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['composite_score'],
            mode='lines',
            name='综合得分',
            yaxis='y',
            line=dict(color='#1f77b4', width=2)
        ))

        # 添加仓位
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['risk_adjusted_position'] * 100,
            mode='lines',
            name='风险调整后仓位(%)',
            yaxis='y2',
            line=dict(color='#ff7f0e', width=2)
        ))

        fig.update_layout(
            title="择时信号",
            xaxis_title="日期",
            yaxis=dict(title="得分", side="left"),
            yaxis2=dict(title="仓位(%)", side="right", overlaying="y"),
            hovermode='x unified',
            height=400,
            legend=dict(x=0.01, y=0.99)
        )

        st.plotly_chart(fig, use_container_width=True)

    else:
        st.warning("无法生成信号：缺少宏观得分数据")


def render_industry_allocation(data, params):
    """渲染行业配置页面"""
    st.header("🏭 行业配置建议")

    st.info("行业轮动功能需要额外的行业数据和宏观-行业映射数据库")

    # 模拟行业配置示例
    st.subheader("示例：当前宏观状态下的行业配置")

    # 创建示例配置
    example_allocation = {
        '行业': ['金融', '科技', '消费', '工业', '能源'],
        '权重': [0.30, 0.25, 0.20, 0.15, 0.10],
        '理由': [
            '受益于流动性宽松',
            '增长动力强劲',
            '防御性配置',
            '受益于基建投资',
            '通胀对冲'
        ]
    }

    df = pd.DataFrame(example_allocation)

    # 显示配置表
    st.dataframe(
        df,
        column_config={
            '权重': st.column_config.ProgressColumn(
                '权重',
                help='行业配置权重',
                format='%.2f',
                min_value=0,
                max_value=1
            )
        },
        hide_index=True
    )

    # 可视化饼图
    fig = go.Figure(go.Pie(
        labels=df['行业'],
        values=df['权重'],
        hole=0.3,
        textinfo='percent+label'
    ))

    fig.update_layout(
        title="建议行业配置",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def main():
    """主函数"""
    # 加载数据
    data = load_data()

    # 渲染标题
    render_header()

    # 渲染侧边栏
    params = render_sidebar(data)

    # 创建标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 概览",
        "🎯 宏观状态",
        "⚠️ 风险监控",
        "📈 择时信号",
        "🏭 行业配置"
    ])

    with tab1:
        render_overview(data, params)

    with tab2:
        render_regime(data, params)

    with tab3:
        render_risk(data, params)

    with tab4:
        render_signals(data, params)

    with tab5:
        render_industry_allocation(data, params)

    # 页脚
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
        <p>宏观交易策略监控系统 | 基于 Nowcasting 与动态因子模型</p>
        <p>数据更新时间: {}</p>
        </div>
        """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
