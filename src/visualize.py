import numpy as np
from data_processing import process_data
import plotly.graph_objects as go


# 処理済データの受け取り
data = process_data()

# 初期のfigオブジェクトを作成
fig = go.Figure()

# ドロップダウンメニューのボタンを格納するリスト
buttons = []

# グラフの表示
for index, (genre, group_df) in enumerate(data.items()):
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
    scatter = go.Scatter(
        x=group_df['expected_per'],
        y=group_df['expected_roe'],
        mode='markers',
        marker=dict(
            color=group_df['expected_dividend_yield'],
            colorscale='Viridis',
            size=group_df['price'] / 50,
            colorbar=dict(title="Dividend Yield")
        ),
        customdata=group_df[['code', 'name', 'price', 'expected_roe', 'expected_per', 'actual_pbr', 'expected_dividend_yield']].values,
        hovertemplate=hovertemplate,
        visible=(index == 0)  # 最初のジャンルのグラフのみを表示
    )
    fig.add_trace(scatter)

    # pbr指標の追加
    x_values = np.linspace(2, max(group_df['expected_per']) * 1.1, 2000)
    y_values = 100 / x_values
    pbr_line = go.Scatter(x=x_values, y=y_values, mode='lines', name='PBR *1 line', visible=(index == 0))
    fig.add_trace(pbr_line)

    # ドロップダウンメニューのボタンを追加
    visible_list = [False] * len(data) * 2  # すべてのトレースを非表示に設定
    visible_list[index * 2] = True  # 選択されたジャンルのscatter plotを表示
    visible_list[index * 2 + 1] = True  # 選択されたジャンルのpbr lineを表示
    buttons.append(dict(label=genre, method="update", args=[{"visible": visible_list}]))

# ドロップダウンメニューを作成
fig.update_layout(
    updatemenus=[dict(type="dropdown", direction="down", buttons=buttons, showactive=True)]
)

# フィギュアを表示
fig.write_html('web/all_graphs.html', config={'responsive': True})
