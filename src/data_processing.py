import pandas as pd
import os
import pickle
from datetime import datetime, timedelta

def get_cache_path():
    """キャッシュファイルのパスを取得"""
    return 'data/processed_data_cache.pkl'

def is_cache_valid():
    """キャッシュが有効かどうかをチェック（24時間以内）"""
    cache_path = get_cache_path()
    if not os.path.exists(cache_path):
        return False
    
    # キャッシュファイルの更新時刻をチェック
    cache_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
    return datetime.now() - cache_time < timedelta(hours=24)

def save_cache(data):
    """データをキャッシュに保存"""
    cache_path = get_cache_path()
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, 'wb') as f:
        pickle.dump(data, f)

def load_cache():
    """キャッシュからデータを読み込み"""
    cache_path = get_cache_path()
    with open(cache_path, 'rb') as f:
        return pickle.load(f)

def process_data():
    """
    データの処理（キャッシュ機能付き）
    """
    # キャッシュが有効な場合はキャッシュを使用
    if is_cache_valid():
        print("有効なキャッシュを使用します")
        return load_cache()
    
    print("データを処理中...")
    
    # データの読み込みとマージ
    scraping_df = pd.read_csv('data/output.csv')

    # 列名の正規化（想定列がそろっているか最終チェック）
    expected_columns = ['code', 'name', 'price', 'expected_roe', 'expected_per', 'expected_dividend_yield', 'actual_pbr']
    missing_columns = [c for c in expected_columns if c not in scraping_df.columns]
    if missing_columns:
        raise ValueError(f"data/output.csv に必須列がありません: {missing_columns}")

    # 証券コードを4桁文字列に正規化
    scraping_df['code'] = scraping_df['code'].astype(str).str.strip().str.replace(".0", "", regex=False)
    scraping_df['code'] = scraping_df['code'].apply(lambda x: str(int(x)).zfill(4) if x.isdigit() else x)
    
    type_data = pd.read_excel('data/data_j.xls')
    # 業種データのコード列も文字列に統一
    type_data['コード'] = type_data['コード'].astype(str).str.strip().str.replace(".0", "", regex=False)
    type_data['コード'] = type_data['コード'].apply(lambda x: str(int(x)).zfill(4) if x.isdigit() else x)
    
    merged_df = pd.merge(scraping_df, type_data[['コード', '33業種区分']], left_on='code', right_on='コード', how='left')
    merged_df.drop('コード', axis=1, inplace=True)

    # 欠損値処理
    merged_df.dropna(subset=['expected_roe', 'expected_per', 'price', 'expected_dividend_yield'], inplace=True)

    # PBR指標の追加
    merged_df['pbr_indicator'] = merged_df['expected_roe'] * merged_df['expected_per'] / 100

    # データの分割
    grouped_data = {}
    for genre, group_df in merged_df.groupby('33業種区分'):
        grouped_data[genre] = group_df

    # 結果をキャッシュに保存
    save_cache(grouped_data)
    print("データ処理完了、キャッシュに保存しました")
    
    return grouped_data