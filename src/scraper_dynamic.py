import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import sys
import os
from datetime import datetime
import argparse

# 動的銘柄コード取得モジュールをインポート
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.stock_code_fetcher_working import WorkingStockCodeFetcher
from src.data_manager import DataManager

class DynamicStockScraper:
    """
    動的に銘柄コードを取得してスクレイピングを行うクラス
    """
    
    def __init__(self, use_dynamic_codes=True, codes_file='data/codes.csv'):
        self.use_dynamic_codes = use_dynamic_codes
        self.codes_file = codes_file
        self.fetcher = WorkingStockCodeFetcher() if use_dynamic_codes else None
        self.data_manager = DataManager()
        
        # Chrome設定
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--remote-debugging-port=9222")
        
        # WebDriver設定
        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), 
            options=self.chrome_options
        )
        
        self.base_url = 'https://www.nikkei.com/nkd/company/?scode='
        
        # データ格納用リスト
        self.current_urls = []
        self.stock_names = []
        self.last_prices = []
        self.expected_pers = []
        self.expected_dividend_yields = []
        self.expected_roes = []
        self.actual_pbrs = []
        self.last_news_texts = []
        self.last_news_urls = []
        self.last_disclosures = []
        self.last_disclosure_urls = []
    
    def get_stock_codes(self):
        """
        銘柄コードを取得（動的または静的）
        """
        if self.use_dynamic_codes:
            print("動的に銘柄コードを取得中...")
            codes = self.fetcher.get_prime_stock_codes(method='auto')

            if codes:
                # 正規化（4桁ゼロ埋め・数値4桁のみ）
                normalized = self.normalize_codes(codes)
                # 動的に取得したコードを保存（ログ用途）
                self.fetcher.save_codes_to_file(normalized, 'data/codes_dynamic.csv')
                return normalized
            else:
                print("動的取得に失敗したため、静的ファイルを使用します")
                return self._load_static_codes()
        else:
            return self._load_static_codes()
    
    def _load_static_codes(self):
        """
        静的ファイルから銘柄コードを読み込み
        """
        try:
            c = pd.read_csv(self.codes_file, header=None)
            codes = [cv[0] for cv in c.values]
            normalized = self.normalize_codes(codes)
            print(f"静的ファイルから{len(normalized)}件の銘柄コードを読み込みました")
            return normalized
        except Exception as e:
            print(f"静的ファイルの読み込みに失敗: {e}")
            return []
    
    def ext_by_cn(self, class_name, int, replace_text, type_to_change):
        """
        クラス名を指定して要素を抽出する
        """
        lst = WebDriverWait(self.driver, 30).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, class_name))
        )
        spcfd = lst[int].text.replace(replace_text, '')
        if ',' in spcfd:
            var = type_to_change(spcfd.replace(',', ''))
        else:
            var = type_to_change(spcfd)
        return var
    
    def scrape_stock_data(self, codes):
        """
        銘柄データをスクレイピング
        """
        print(f"{len(codes)}件の銘柄をスクレイピング開始...")
        
        counter = 0
        
        for code in codes:
            try:
                current_url = self.base_url + str(code)
                self.current_urls.append(current_url)
                
                # URLにアクセス
                self.driver.get(current_url)
                time.sleep(1)
                
                # 初回だけ「株価指標ボタン」を押下
                if counter == 0:
                    btn = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CLASS_NAME, 'm-stockInfo_btn_open'))
                    )
                    self.driver.execute_script("arguments[0].click();", btn)
                
                # 銘柄名
                stock_name = self.driver.title[1:].split('】')[0]
                self.stock_names.append(stock_name)
                
                # 直近時価
                try:
                    last_price = self.ext_by_cn('m-stockPriceElm_value', 0, ' 円', float)
                    self.last_prices.append(last_price)
                except:
                    self.last_prices.append(None)
                
                # 予想PER
                try:
                    expected_per = self.ext_by_cn('m-stockInfo_detail_value', 4, ' 倍', float)
                    self.expected_pers.append(expected_per)
                except:
                    self.expected_pers.append(None)
                
                # 予想配当利回り
                try:
                    expected_dividend_yield = self.ext_by_cn('m-stockInfo_detail_value', 5, ' ％', float)
                    self.expected_dividend_yields.append(expected_dividend_yield)
                except:
                    self.expected_dividend_yields.append(None)
                
                # PBR実績値
                try:
                    actual_pbr = self.ext_by_cn('m-stockInfo_detail_value', 6, ' 倍', float)
                    self.actual_pbrs.append(actual_pbr)
                except:
                    self.actual_pbrs.append(None)
                
                # 予想ROE
                try:
                    expected_roe = self.ext_by_cn('m-stockInfo_detail_value', 7, ' ％', float)
                    self.expected_roes.append(expected_roe)
                except:
                    self.expected_roes.append(None)
                
                # 最新ニュース
                try:
                    news_elements = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.CLASS_NAME, 'm-articleList_item'))
                    )
                    if news_elements:
                        last_news_text = news_elements[0].text
                        last_news_url = news_elements[0].find_element(By.TAG_NAME, 'a').get_attribute('href')
                        self.last_news_texts.append(last_news_text)
                        self.last_news_urls.append(last_news_url)
                    else:
                        self.last_news_texts.append(None)
                        self.last_news_urls.append(None)
                except:
                    self.last_news_texts.append(None)
                    self.last_news_urls.append(None)
                
                # 最新開示
                try:
                    disclosure_elements = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_all_elements_located((By.CLASS_NAME, 'm-disclosureList_item'))
                    )
                    if disclosure_elements:
                        last_disclosure = disclosure_elements[0].text
                        last_disclosure_url = disclosure_elements[0].find_element(By.TAG_NAME, 'a').get_attribute('href')
                        self.last_disclosures.append(last_disclosure)
                        self.last_disclosure_urls.append(last_disclosure_url)
                    else:
                        self.last_disclosures.append(None)
                        self.last_disclosure_urls.append(None)
                except:
                    self.last_disclosures.append(None)
                    self.last_disclosure_urls.append(None)
                
                counter += 1
                print(f"進捗: {counter}/{len(codes)} - {stock_name} ({code})")
                
            except Exception as e:
                print(f"銘柄コード {code} のスクレイピングに失敗: {e}")
                # エラー時はNoneを追加
                self.stock_names.append(None)
                self.last_prices.append(None)
                self.expected_pers.append(None)
                self.expected_dividend_yields.append(None)
                self.actual_pbrs.append(None)
                self.expected_roes.append(None)
                self.last_news_texts.append(None)
                self.last_news_urls.append(None)
                self.last_disclosures.append(None)
                self.last_disclosure_urls.append(None)
    
    def save_results(self, filename='data/output.csv'):
        """
        スクレイピング結果を保存
        """
        try:
            # コードを4桁ゼロ埋めの文字列に正規化
            normalized_codes = [str(code).strip().zfill(4) for code in self.codes]

            # 可視化・処理系と時系列系の両方に互換のある列名で保存
            results_df = pd.DataFrame({
                # 共通
                'code': normalized_codes,
                'name': self.stock_names,
                'price': self.last_prices,
                'expected_per': self.expected_pers,
                'expected_dividend_yield': self.expected_dividend_yields,
                'expected_roe': self.expected_roes,
                'actual_pbr': self.actual_pbrs,
                # 追加（時系列可視化の互換）
                'stock_name': self.stock_names,
                'last_price': self.last_prices,
                # ニュース/開示
                'last_news_text': self.last_news_texts,
                'last_news_url': self.last_news_urls,
                'last_disclosure': self.last_disclosures,
                'last_disclosure_url': self.last_disclosure_urls
            })

            # 必須列の最終検証
            required_cols = ['code', 'name', 'price', 'expected_roe', 'expected_per', 'expected_dividend_yield', 'actual_pbr']
            missing = [c for c in required_cols if c not in results_df.columns]
            if missing:
                raise ValueError(f"出力に必須列が不足しています: {missing}")
            
            # 既存ファイルがあればマージ（codeキーで上書き追加）
            if os.path.exists(filename):
                try:
                    existing = pd.read_csv(filename)
                    if 'code' in existing.columns:
                        existing['code'] = existing['code'].astype(str).str.strip().str.replace('.0', '', regex=False)
                        existing['code'] = existing['code'].apply(lambda x: str(int(x)).zfill(4) if x.isdigit() else x)
                    merged = existing.set_index('code')
                    merged.update(results_df.set_index('code'))
                    new_only = results_df[~results_df['code'].isin(merged.index)].set_index('code')
                    merged = pd.concat([merged, new_only])
                    merged.reset_index().to_csv(filename, index=False, encoding='utf-8-sig')
                except Exception:
                    results_df.to_csv(filename, index=False, encoding='utf-8-sig')
            else:
                results_df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"結果を{filename}に保存しました（マージ済み）")
            
            # 時系列データとしても保存
            self.data_manager.save_daily_data(results_df)
            print("時系列データとして保存しました")
            
        except Exception as e:
            print(f"結果の保存に失敗: {e}")
    
    def run(self, start_index=None, start_code=None, limit=None, resume=False):
        """
        メイン実行関数
        """
        try:
            # 銘柄コードを取得（正規化済み）
            self.codes = self.get_stock_codes()
            
            if not self.codes:
                print("銘柄コードの取得に失敗しました")
                return
            
            # 再開・開始位置・件数の制御
            codes_to_scrape = list(self.codes)
            if resume and os.path.exists('data/output.csv'):
                try:
                    existing = pd.read_csv('data/output.csv')
                    if 'code' in existing.columns:
                        existing_codes = set(existing['code'].astype(str).str.strip().apply(lambda x: str(int(x)).zfill(4) if x.isdigit() else x))
                        codes_to_scrape = [c for c in codes_to_scrape if c not in existing_codes]
                        print(f"再開モード: 既存{len(existing_codes)}件スキップ、対象{len(codes_to_scrape)}件")
                except Exception as e:
                    print(f"既存output.csv読み込み失敗: {e}")

            if start_code is not None:
                start_code = str(start_code).strip().zfill(4)
                if start_code in codes_to_scrape:
                    start_index = codes_to_scrape.index(start_code)
                else:
                    print(f"start_code {start_code} は一覧にありません。start_indexを使用します。")

            if isinstance(start_index, int) and start_index > 0:
                codes_to_scrape = codes_to_scrape[start_index:]
                print(f"開始インデックス {start_index} から再開（残り {len(codes_to_scrape)} 件）")

            if isinstance(limit, int) and limit > 0:
                codes_to_scrape = codes_to_scrape[:limit]
                print(f"最大 {limit} 件のみ処理")

            if not codes_to_scrape:
                print("処理対象がありません。終了します。")
                return

            # スクレイピング実行
            self.scrape_stock_data(codes_to_scrape)
            
            # 結果を保存（統一出力: data/output.csv）
            self.save_results('data/output.csv')
            
            print("スクレイピング完了")
            
        except Exception as e:
            print(f"スクレイピング実行中にエラーが発生: {e}")
        
        finally:
            # WebDriverを閉じる
            if hasattr(self, 'driver'):
                self.driver.quit()

    def normalize_codes(self, codes):
        """
        取得した銘柄コードを4桁の文字列に正規化し重複を除去
        """
        normalized = []
        seen = set()
        for code in codes:
            s = str(code).strip()
            # 末尾の不要な"0"付与・5桁化などの異常を防ぐため、数値のみを取り出して4桁に揃える
            if s.isdigit():
                s = str(int(s)).zfill(4)
            else:
                # 非数字はスキップ
                continue
            if len(s) == 4 and s.isdigit() and s not in seen:
                normalized.append(s)
                seen.add(s)
        return normalized

def main():
    """
    メイン実行関数
    """
    parser = argparse.ArgumentParser(description='Dynamic stock scraper with resume options')
    parser.add_argument('--start-index', type=int, default=None, help='先頭からのスキップ件数')
    parser.add_argument('--start-code', type=str, default=None, help='このコードから開始（4桁）')
    parser.add_argument('--limit', type=int, default=None, help='最大処理件数')
    parser.add_argument('--resume', action='store_true', help='既存data/output.csvを基にスキップして再開')
    args = parser.parse_args()

    # 動的取得を使用する場合
    scraper = DynamicStockScraper(use_dynamic_codes=True)
    scraper.run(start_index=args.start_index, start_code=args.start_code, limit=args.limit, resume=args.resume)
    
    # 静的ファイルを使用する場合
    # scraper = DynamicStockScraper(use_dynamic_codes=False)
    # scraper.run()

if __name__ == "__main__":
    main() 