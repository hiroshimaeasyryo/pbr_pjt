import numpy as np
from data_processing import process_data
import plotly.graph_objects as go


# 処理済データの受け取り
data = process_data()

# 10個ずつデータをとる(ここは本番環境では不要)
# sample10 = dict(list(data.items())[15:])

# グラフの表示
for genre, group_df in data.items():
# for genre, group_df in zip(sample10.keys(), sample10.values()):
    fig = go.Figure()

    # hovertemplateの設定
    hovertemplate = (
        "<b>code:</b> %{customdata[0]}<br>"
        "<b>name:</b> %{customdata[1]}<br>"
        "<b>price:</b> %{customdata[2]}<br>"
        "<b>expected ROE:</b> %{customdata[3]}<br>"
        "<b>expected PER:</b> %{customdata[4]}<br>"
        "<b>actual PBR:</b> %{customdata[5]}<br>"
        "<b>expected dividend yield:</b> %{customdata[6]}"
        "<extra></extra>"  # 余分な情報を表示しないための設定
    )

    # scatter plotの追加
    fig.add_trace(go.Scatter(
        x=group_df['expected_per'],
        y=group_df['expected_roe'],
        mode='markers',
        marker=dict(
            color=group_df['expected_dividend_yield'],
            colorscale='Viridis',
            size=group_df['price']/50,
            colorbar=dict(title="Dividend Yield")
        ),
        customdata=group_df[['code', 'name', 'price', 'expected_roe', 'expected_per', 'actual_pbr', 'expected_dividend_yield']].values,
        hovertemplate=hovertemplate
    ))

    # pbr指標の追加
    x_values = np.linspace(2, max(group_df['expected_per'])*1.1, 2000)
    y_values = 100 / x_values
    fig.add_trace(go.Scatter(x=x_values, y=y_values, mode='lines', name='PBR *1 line'))

    fig.update_layout(title=f"Scatter plot for {genre}", xaxis_title="Expected PER(倍)", yaxis_title="Expected ROE(%)")
    fig.show()
