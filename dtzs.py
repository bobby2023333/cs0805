from flask import Blueprint, render_template, session
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from scipy.stats import pearsonr
from  extensions import db

txzs = Blueprint('txzs', __name__)

@txzs.route('/')
def txzs_view():
    data = session.get('df', None)
    if data is None:
        return "No data found in session. Please make sure to select files for analysis in txfx.html."

    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])

    # Create plot for trend analysis
    fig_trend = px.line(df, x='date', y=['shouru', 'zhichu', 'yue'], facet_col='name', title='趋势分析')
    plot_div_trend = fig_trend.to_html(full_html=False)

    # Create plot for comparison analysis
    fig_compare = go.Figure()
    names = df['name'].unique()
    for name in names:
        temp_df = df[df['name'] == name]
        fig_compare.add_trace(go.Scatter(x=temp_df['date'], y=temp_df['shouru'], mode='lines', name=f'{name} - shouru'))
        fig_compare.add_trace(go.Scatter(x=temp_df['date'], y=temp_df['zhichu'], mode='lines', name=f'{name} - zhichu'))
        fig_compare.add_trace(go.Scatter(x=temp_df['date'], y=temp_df['yue'], mode='lines', name=f'{name} - yue'))
    fig_compare.update_layout(title_text='比较分析')
    plot_div_compare = fig_compare.to_html(full_html=False)

    # Create plot for correlation analysis
    corr, _ = pearsonr(df['shouru'], df['yue'])
    fig_corr = px.scatter(df, x='shouru', y='yue', trendline='ols', title=f'相关性分析: shouru and yue (Correlation: {corr:.2f})')
    plot_div_corr = fig_corr.to_html(full_html=False)

    # 非0收入和支出的交易
    df_nonzero = df[(df['shouru'] != 0) | (df['zhichu'] != 0)]

    # 计算每个账户的收入/支出总额和交易次数
    df_grouped_shouru = df_nonzero.groupby('name')['shouru'].agg(['sum', 'count'])
    df_grouped_zhichu = df_nonzero.groupby('name')['zhichu'].agg(['sum', 'count'])

    # 创建收入柱状图
    fig_shouru = go.Figure(data=[
        go.Bar(
            x=df_grouped_shouru.index,
            y=df_grouped_shouru['sum'],
            text=df_grouped_shouru['count'],
            name='收入',
            marker_color='blue'
        )
    ])
    fig_shouru.update_layout(title='收入前5账户', xaxis_title='账户', yaxis_title='总额',
                             yaxis=dict(title='总额', titlefont_size=16, tickfont_size=14),
                             legend=dict(x=0, y=1.0, bgcolor='rgba(255, 255, 255, 0)', bordercolor='rgba(255, 255, 255, 0)'),
                             barmode='group', bargap=0.15, bargroupgap=0.1)
    plot_div_shouru = fig_shouru.to_html(full_html=False)

    # 创建支出柱状图
    fig_zhichu = go.Figure(data=[
        go.Bar(
            x=df_grouped_zhichu.index,
            y=df_grouped_zhichu['sum'],
            text=df_grouped_zhichu['count'],
            name='支出',
            marker_color='red'
        )
    ])
    fig_zhichu.update_layout(title='支出前5账户', xaxis_title='账户', yaxis_title='总额',
                             yaxis=dict(title='总额', titlefont_size=16, tickfont_size=14),
                             legend=dict(x=0, y=1.0, bgcolor='rgba(255, 255, 255, 0)', bordercolor='rgba(255, 255, 255, 0)'),
                             barmode='group', bargap=0.15, bargroupgap=0.1)
    plot_div_zhichu = fig_zhichu.to_html(full_html=False)

    return render_template('txzs.html', plot_div_trend=plot_div_trend, plot_div_compare=plot_div_compare,
                           plot_div_corr=plot_div_corr, plot_div_shouru=plot_div_shouru, plot_div_zhichu=plot_div_zhichu)


