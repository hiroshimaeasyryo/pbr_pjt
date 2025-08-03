import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import logging
from src.data_manager import DataManager
from pathlib import Path

class TimeSeriesVisualizer:
    """
    時系列データ可視化クラス
    """
    
    def __init__(self):
        self.data_manager = DataManager()
        self.logger = logging.getLogger(__name__)
    
    def create_pbr_trend_chart(self, start_date=None, end_date=None, top_n=20):
        """
        PBRトレンドチャートを作成
        
        Args:
            start_date (str): 開始日
            end_date (str): 終了日
            top_n (int): 表示する上位銘柄数
        
        Returns:
            plotly.graph_objects.Figure: チャート
        """
        # 時系列データを取得
        data = self.data_manager.get_time_series_data(
            start_date=start_date, 
            end_date=end_date,
            columns=['code', 'stock_name', 'actual_pbr', 'last_price']
        )
        
        if data.empty:
            self.logger.warning("時系列データがありません")
            return None
        
        # 最新日のデータで上位銘柄を特定
        latest_date = data['date'].max()
        latest_data = data[data['date'] == latest_date]
        
        # PBRが有効なデータのみフィルタリング
        latest_data = latest_data[latest_data['actual_pbr'].notna()]
        latest_data = latest_data[latest_data['actual_pbr'] > 0]
        
        if latest_data.empty:
            self.logger.warning("有効なPBRデータがありません")
            return None
        
        # 上位銘柄を選択
        top_stocks = latest_data.nsmallest(top_n, 'actual_pbr')
        top_codes = top_stocks['code'].tolist()
        
        # 選択された銘柄の時系列データをフィルタリング
        filtered_data = data[data['code'].isin(top_codes)]
        
        # チャートを作成
        fig = go.Figure()
        
        for code in top_codes:
            stock_data = filtered_data[filtered_data['code'] == code]
            stock_name = stock_data['stock_name'].iloc[0] if not stock_data.empty else code
            
            fig.add_trace(go.Scatter(
                x=stock_data['date'],
                y=stock_data['actual_pbr'],
                mode='lines+markers',
                name=f"{code}: {stock_name}",
                hovertemplate='<b>%{fullData.name}</b><br>' +
                            '日付: %{x}<br>' +
                            'PBR: %{y:.2f}<br>' +
                            '<extra></extra>'
            ))
        
        fig.update_layout(
            title=f"PBRトレンド（上位{top_n}銘柄）",
            xaxis_title="日付",
            yaxis_title="PBR",
            hovermode='x unified',
            height=600
        )
        
        return fig
    
    def create_price_trend_chart(self, codes, start_date=None, end_date=None):
        """
        株価トレンドチャートを作成
        
        Args:
            codes (list): 銘柄コードのリスト
            start_date (str): 開始日
            end_date (str): 終了日
        
        Returns:
            plotly.graph_objects.Figure: チャート
        """
        # 時系列データを取得
        data = self.data_manager.get_time_series_data(
            start_date=start_date, 
            end_date=end_date,
            columns=['code', 'stock_name', 'last_price']
        )
        
        if data.empty:
            self.logger.warning("時系列データがありません")
            return None
        
        # 指定された銘柄のデータをフィルタリング
        filtered_data = data[data['code'].isin(codes)]
        
        if filtered_data.empty:
            self.logger.warning("指定された銘柄のデータがありません")
            return None
        
        # チャートを作成
        fig = go.Figure()
        
        for code in codes:
            stock_data = filtered_data[filtered_data['code'] == code]
            if not stock_data.empty:
                stock_name = stock_data['stock_name'].iloc[0]
                
                fig.add_trace(go.Scatter(
                    x=stock_data['date'],
                    y=stock_data['last_price'],
                    mode='lines+markers',
                    name=f"{code}: {stock_name}",
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                '日付: %{x}<br>' +
                                '株価: %{y:,.0f}円<br>' +
                                '<extra></extra>'
                ))
        
        fig.update_layout(
            title="株価トレンド",
            xaxis_title="日付",
            yaxis_title="株価（円）",
            hovermode='x unified',
            height=600
        )
        
        return fig
    
    def create_market_overview_chart(self, start_date=None, end_date=None):
        """
        市場全体の概況チャートを作成
        
        Args:
            start_date (str): 開始日
            end_date (str): 終了日
        
        Returns:
            plotly.graph_objects.Figure: チャート
        """
        # 時系列データを取得
        data = self.data_manager.get_time_series_data(
            start_date=start_date, 
            end_date=end_date,
            columns=['code', 'actual_pbr', 'expected_per', 'expected_dividend_yield', 'last_price']
        )
        
        if data.empty:
            self.logger.warning("時系列データがありません")
            return None
        
        # 日次統計を計算
        daily_stats = data.groupby('date').agg({
            'actual_pbr': ['mean', 'median', 'std'],
            'expected_per': ['mean', 'median'],
            'expected_dividend_yield': ['mean', 'median'],
            'last_price': ['mean', 'median']
        }).reset_index()
        
        # マルチサブプロットを作成
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('PBR分布', 'PER分布', '配当利回り分布', '株価分布'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # PBR分布
        fig.add_trace(
            go.Scatter(
                x=daily_stats['date'],
                y=daily_stats[('actual_pbr', 'mean')],
                mode='lines+markers',
                name='平均PBR',
                line=dict(color='blue')
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=daily_stats['date'],
                y=daily_stats[('actual_pbr', 'median')],
                mode='lines+markers',
                name='中央値PBR',
                line=dict(color='red')
            ),
            row=1, col=1
        )
        
        # PER分布
        fig.add_trace(
            go.Scatter(
                x=daily_stats['date'],
                y=daily_stats[('expected_per', 'mean')],
                mode='lines+markers',
                name='平均PER',
                line=dict(color='green')
            ),
            row=1, col=2
        )
        
        # 配当利回り分布
        fig.add_trace(
            go.Scatter(
                x=daily_stats['date'],
                y=daily_stats[('expected_dividend_yield', 'mean')],
                mode='lines+markers',
                name='平均配当利回り',
                line=dict(color='orange')
            ),
            row=2, col=1
        )
        
        # 株価分布
        fig.add_trace(
            go.Scatter(
                x=daily_stats['date'],
                y=daily_stats[('last_price', 'mean')],
                mode='lines+markers',
                name='平均株価',
                line=dict(color='purple')
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            title="市場全体の概況",
            height=800,
            showlegend=True
        )
        
        # 軸ラベルを設定
        fig.update_xaxes(title_text="日付", row=1, col=1)
        fig.update_xaxes(title_text="日付", row=1, col=2)
        fig.update_xaxes(title_text="日付", row=2, col=1)
        fig.update_xaxes(title_text="日付", row=2, col=2)
        
        fig.update_yaxes(title_text="PBR", row=1, col=1)
        fig.update_yaxes(title_text="PER", row=1, col=2)
        fig.update_yaxes(title_text="配当利回り（%）", row=2, col=1)
        fig.update_yaxes(title_text="株価（円）", row=2, col=2)
        
        return fig
    
    def save_chart_to_html(self, fig, filename):
        """
        チャートをHTMLファイルに保存
        
        Args:
            fig (plotly.graph_objects.Figure): チャート
            filename (str): ファイル名
        """
        if fig is not None:
            output_dir = Path("docs/charts")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = output_dir / filename
            fig.write_html(str(filepath))
            self.logger.info(f"チャートを保存しました: {filepath}")

def main():
    """
    メイン実行関数
    """
    visualizer = TimeSeriesVisualizer()
    
    # データ統計を表示
    stats = visualizer.data_manager.get_statistics()
    print("データ統計情報:")
    print(f"  総ファイル数: {stats['total_files']}")
    print(f"  総データポイント: {stats['total_data_points']}")
    
    if stats['total_files'] > 0:
        # PBRトレンドチャートを作成
        pbr_chart = visualizer.create_pbr_trend_chart(top_n=10)
        if pbr_chart:
            visualizer.save_chart_to_html(pbr_chart, "pbr_trend.html")
        
        # 市場概況チャートを作成
        overview_chart = visualizer.create_market_overview_chart()
        if overview_chart:
            visualizer.save_chart_to_html(overview_chart, "market_overview.html")
        
        print("チャートの生成が完了しました")
    else:
        print("時系列データがありません。まずデータを収集してください。")

if __name__ == "__main__":
    main() 