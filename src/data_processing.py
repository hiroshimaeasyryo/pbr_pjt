import pandas as pd


def process_data():
    # データの読み込みとマージ
    scraping_df = pd.read_csv('data/output.csv')
    type_data = pd.read_excel('data/data_j.xls')
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

    return grouped_data