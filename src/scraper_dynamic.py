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

# 動的銘柄コード取得モジュールをインポート
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from src.stock_code_fetcher_working import WorkingStockCodeFetcher

class DynamicStockScraper:
    """
    動的に銘柄コードを取得してスクレイピングを行うクラス
    """
    
    def __init__(self, use_dynamic_codes=True, codes_file='data/codes.csv'):
        self.use_dynamic_codes = use_dynamic_codes
        self.codes_file = codes_file
        self.fetcher = WorkingStockCodeFetcher() if use_dynamic_codes else None
        
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
                # 動的に取得したコードを保存
                self.fetcher.save_codes_to_file(codes, 'data/codes_dynamic.csv')
                return codes
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
            codes = []
            for cv in c.values:
                codes.append(cv[0])
            print(f"静的ファイルから{len(codes)}件の銘柄コードを読み込みました")
            return codes
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
    
    def save_results(self, filename='data/output_dynamic.csv'):
        """
        スクレイピング結果を保存
        """
        try:
            results_df = pd.DataFrame({
                'code': [str(code) for code in self.codes],
                'stock_name': self.stock_names,
                'last_price': self.last_prices,
                'expected_per': self.expected_pers,
                'expected_dividend_yield': self.expected_dividend_yields,
                'actual_pbr': self.actual_pbrs,
                'expected_roe': self.expected_roes,
                'last_news_text': self.last_news_texts,
                'last_news_url': self.last_news_urls,
                'last_disclosure': self.last_disclosures,
                'last_disclosure_url': self.last_disclosure_urls
            })
            
            results_df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"結果を{filename}に保存しました")
            
        except Exception as e:
            print(f"結果の保存に失敗: {e}")
    
    def run(self):
        """
        メイン実行関数
        """
        try:
            # 銘柄コードを取得
            self.codes = self.get_stock_codes()
            
            if not self.codes:
                print("銘柄コードの取得に失敗しました")
                return
            
            # スクレイピング実行
            self.scrape_stock_data(self.codes)
            
            # 結果を保存
            self.save_results()
            
            print("スクレイピング完了")
            
        except Exception as e:
            print(f"スクレイピング実行中にエラーが発生: {e}")
        
        finally:
            # WebDriverを閉じる
            if hasattr(self, 'driver'):
                self.driver.quit()

def main():
    """
    メイン実行関数
    """
    # 動的取得を使用する場合
    scraper = DynamicStockScraper(use_dynamic_codes=True)
    scraper.run()
    
    # 静的ファイルを使用する場合
    # scraper = DynamicStockScraper(use_dynamic_codes=False)
    # scraper.run()

if __name__ == "__main__":
    main() 