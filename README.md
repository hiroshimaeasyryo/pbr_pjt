# PBR分析プロジェクト

東証プライム上場企業のPBR（株価純資産倍率）分析を行うプロジェクトです。

## 機能

- 東証プライム上場企業の証券コードを動的に取得
- 日経新聞サイトからの株価情報スクレイピング
- PBR、PER、配当利回り等の財務指標分析
- 結果の可視化とレポート生成

## セットアップ

### 1. 環境構築

```bash
# 仮想環境の作成
python3 -m venv venv

# 仮想環境の有効化
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt
```

### 2. 環境変数の設定

```bash
# 環境変数ファイルのコピー
cp env.example .env

# .envファイルを編集してAPIキーを設定
```

`.env`ファイルの例：
```env
# API Keys
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here
QUANDL_API_KEY=your_quandl_api_key_here
YAHOO_FINANCE_API_KEY=your_yahoo_finance_api_key_here

# Scraping Configuration
SCRAPING_DELAY=1
MAX_RETRIES=3
TIMEOUT=30
```

### 3. 必要なAPIキーの取得

#### Alpha Vantage API
1. [Alpha Vantage](https://www.alphavantage.co/support/#api-key)にアクセス
2. 無料アカウントを作成
3. APIキーを取得

#### Quandl API
1. [Quandl](https://www.quandl.com/)にアクセス
2. アカウントを作成
3. APIキーを取得

## 使用方法

### 動的銘柄コード取得

```bash
# セキュアな銘柄コード取得
python src/stock_code_fetcher_secure.py

# 基本的な銘柄コード取得
python src/stock_code_fetcher_working.py
```

### スクレイピング実行

```bash
# 動的銘柄コード取得を使用したスクレイピング
python src/scraper_dynamic.py

# 従来の静的ファイルを使用したスクレイピング
python src/scraper.py
```

## プロジェクト構造

```
pbr_pjt/
├── data/                   # データファイル
│   ├── codes.csv          # 銘柄コード（静的）
│   ├── output.csv         # スクレイピング結果
│   └── backup/            # バックアップファイル
├── src/                   # ソースコード
│   ├── config.py          # 設定管理
│   ├── stock_code_fetcher_secure.py  # セキュアな銘柄コード取得
│   ├── stock_code_fetcher_working.py # 基本的な銘柄コード取得
│   ├── scraper_dynamic.py # 動的スクレイピング
│   └── scraper.py         # 従来のスクレイピング
├── docs/                  # ドキュメント・HTML出力
├── logs/                  # ログファイル
├── venv/                  # 仮想環境
├── .env                   # 環境変数（gitignore対象）
├── env.example            # 環境変数テンプレート
├── requirements.txt       # 依存関係
└── README.md             # このファイル
```

## セキュリティ考慮事項

- APIキーは`.env`ファイルで管理し、Gitにコミットしない
- ログファイルには機密情報を含めない
- 外部APIへのリクエストには適切なタイムアウトを設定
- エラーハンドリングを適切に実装

## 開発環境

### ブランチ戦略

```bash
# 新機能開発時
git checkout -b feature/your-feature-name

# 開発完了後
git add .
git commit -m "Add your feature description"
git push origin feature/your-feature-name
```

### テスト実行

```bash
# 仮想環境が有効化されていることを確認
source venv/bin/activate

# 基本的な動作確認
python src/stock_code_fetcher_secure.py
```

## トラブルシューティング

### よくある問題

1. **APIキーが設定されていない**
   - `.env`ファイルが正しく設定されているか確認
   - APIキーが有効か確認

2. **スクレイピングが失敗する**
   - ネットワーク接続を確認
   - 対象サイトの構造変更を確認

3. **依存関係のエラー**
   - 仮想環境が有効化されているか確認
   - `pip install -r requirements.txt`を再実行

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 貢献

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成 