import numpy as np
import pandas as pd
from data_processing import process_data
import plotly.graph_objects as go
from datetime import datetime
import os


# 処理済データの受け取り
data = process_data()

# データが空の場合のフェイルセーフ
if not data:
    raise RuntimeError("処理データが空です。まず'src/scraper_dynamic.py'で'data/output.csv'を生成してください。")

# スクレイピング日時を取得（ファイルの作成日時を使用）
output_file_path = 'data/output.csv'
if os.path.exists(output_file_path):
    file_timestamp = os.path.getmtime(output_file_path)
    scraping_datetime = datetime.fromtimestamp(file_timestamp).strftime('%Y年%m月%d日 %H:%M')
else:
    scraping_datetime = datetime.now().strftime('%Y年%m月%d日 %H:%M')

# 日経のベースURL
nikkei_base_url = 'https://www.nikkei.com/nkd/company/?scode='

# 初期のfigオブジェクトを作成
fig = go.Figure()

# ドロップダウンメニューのボタンを格納するリスト
buttons = []

# グラフの表示
for index, (genre, group_df) in enumerate(data.items()):
    # 数値のフォーマット関数
    def format_price(price):
        if pd.isna(price):
            return "N/A"
        return f"{price:,.0f}円"
    
    def format_percentage(value):
        if pd.isna(value):
            return "N/A"
        return f"{value:.1f}%"
    
    def format_pbr(value):
        if pd.isna(value):
            return "N/A"
        return f"{value:.2f}倍"
    
    # hovertemplateの設定（日本語化と単位付与、リンクは削除）
    hovertemplate = (
        "<b>銘柄コード:</b> %{customdata[0]}<br>"
        "<b>銘柄名:</b> %{customdata[1]}<br>"
        "<b>直近終値:</b> %{customdata[2]}<br>"
        "<b>期待ROE:</b> %{customdata[3]}<br>"
        "<b>期待PER:</b> %{customdata[4]}<br>"
        "<b>PBR実績値:</b> %{customdata[5]}<br>"
        "<b>期待配当率:</b> %{customdata[6]}<br>"
        "<b>情報取得日時:</b> " + scraping_datetime + "<br>"
        "<b>操作:</b> クリックで詳細パネルを表示"
        "<extra></extra>"  # 余分な情報を表示しないための設定
    )

    # カスタムデータの準備
    custom_data = []
    for _, row in group_df.iterrows():
        # 数値のフォーマット
        formatted_price = format_price(row['price'])
        formatted_roe = format_percentage(row['expected_roe'])
        formatted_per = format_percentage(row['expected_per'])
        formatted_pbr = format_pbr(row['actual_pbr'])
        formatted_dividend = format_percentage(row['expected_dividend_yield'])
        
        # 日経のURLを生成
        nikkei_url = nikkei_base_url + str(row['code'])
        
        custom_data.append([
            row['code'],
            row['name'],
            formatted_price,
            formatted_roe,
            formatted_per,
            formatted_pbr,
            formatted_dividend,
            nikkei_url
        ])

    # scatter plotの追加
    scatter = go.Scatter(
        x=group_df['expected_per'],
        y=group_df['expected_roe'],
        mode='markers',
        marker=dict(
            color=group_df['expected_dividend_yield'],
            colorscale='Viridis',
            size=group_df['price'] / 50,
            colorbar=dict(title="配当利回り (%)")
        ),
        customdata=custom_data,
        hovertemplate=hovertemplate,
        visible=(index == 0),  # 最初のジャンルのグラフのみを表示
        hoverinfo='all'
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

# カスタムJavaScriptを含むHTMLを生成
html_content = fig.to_html(
    include_plotlyjs=True,
    config={'responsive': True},
    full_html=True
)

# カスタムCSSとJavaScriptを追加
custom_css_js = """
<style>
#detail-panel {
    position: fixed;
    top: 50%;
    right: 20px;
    transform: translateY(-50%);
    width: 300px;
    background: white;
    border: 2px solid #007bff;
    border-radius: 10px;
    padding: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    z-index: 1000;
    display: none;
    max-height: 80vh;
    overflow-y: auto;
}

#detail-panel h3 {
    margin-top: 0;
    color: #007bff;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
}

#detail-panel .detail-item {
    margin: 10px 0;
    padding: 5px 0;
    border-bottom: 1px solid #f0f0f0;
}

#detail-panel .detail-label {
    font-weight: bold;
    color: #333;
}

#detail-panel .detail-value {
    color: #666;
    margin-left: 10px;
}

#detail-panel .nikkei-link {
    display: inline-block;
    background: #007bff;
    color: white;
    padding: 10px 20px;
    text-decoration: none;
    border-radius: 5px;
    margin-top: 15px;
    text-align: center;
    width: 100%;
    box-sizing: border-box;
}

#detail-panel .nikkei-link:hover {
    background: #0056b3;
    color: white;
    text-decoration: none;
}

#detail-panel .close-btn {
    position: absolute;
    top: 10px;
    right: 15px;
    background: none;
    border: none;
    font-size: 20px;
    cursor: pointer;
    color: #666;
}

#detail-panel .close-btn:hover {
    color: #333;
}
</style>

<div id="detail-panel">
    <button class="close-btn" onclick="closeDetailPanel()">&times;</button>
    <h3>銘柄詳細情報</h3>
    <div id="detail-content"></div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    // グラフのクリックイベントを監視
    var plotDiv = document.querySelector('.plotly-graph-div');
    if (plotDiv) {
        plotDiv.on('plotly_click', function(data) {
            var point = data.points[0];
            if (point && point.customdata && point.customdata.length >= 8) {
                showDetailPanel(point.customdata);
            }
        });
    }
});

function showDetailPanel(customData) {
    var panel = document.getElementById('detail-panel');
    var content = document.getElementById('detail-content');
    
    var html = `
        <div class="detail-item">
            <span class="detail-label">銘柄コード:</span>
            <span class="detail-value">${customData[0]}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">銘柄名:</span>
            <span class="detail-value">${customData[1]}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">直近終値:</span>
            <span class="detail-value">${customData[2]}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">期待ROE:</span>
            <span class="detail-value">${customData[3]}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">期待PER:</span>
            <span class="detail-value">${customData[4]}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">PBR実績値:</span>
            <span class="detail-value">${customData[5]}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">期待配当率:</span>
            <span class="detail-value">${customData[6]}</span>
        </div>
        <div class="detail-item">
            <span class="detail-label">情報取得日時:</span>
            <span class="detail-value">""" + scraping_datetime + """</span>
        </div>
        <a href="${customData[7]}" target="_blank" class="nikkei-link">
            日経新聞で詳細を見る
        </a>
    `;
    
    content.innerHTML = html;
    panel.style.display = 'block';
}

function closeDetailPanel() {
    document.getElementById('detail-panel').style.display = 'none';
}

// ESCキーでパネルを閉じる
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeDetailPanel();
    }
});
</script>
"""

# JavaScriptをHTMLに挿入
html_content = html_content.replace('</head>', custom_css_js + '</head>')

# HTMLファイルに保存
with open('docs/all_graphs.html', 'w', encoding='utf-8') as f:
    f.write(html_content)
