import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
import concurrent.futures
import threading
from queue import Queue
import logging
from src.config import config

class ParallelScraper:
    """
    並列処理に対応したスクレイパー
    """
    
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)
        self.results_queue = Queue()
        self.lock = threading.Lock()
        
        # 結果を格納するリスト
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
    
    def create_driver(self):
        """
        新しいWebDriverインスタンスを作成
        """
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")
        
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    def wait_with_retry(self, driver, timeout, condition, max_retries=1):
        """
        リトライ機能付きのWebDriverWait
        """
        for attempt in range(max_retries + 1):
            try:
                return WebDriverWait(driver, timeout).until(condition)
            except TimeoutException:
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                else:
                    raise TimeoutException(f"最大リトライ回数({max_retries})に達しました")
    
    def ext_by_cn(self, driver, class_name, index, replace_text, type_to_change):
        """
        クラス名を指定して要素を抽出する
        """
        lst = self.wait_with_retry(driver, 15, 
                                 EC.presence_of_all_elements_located((By.CLASS_NAME, class_name)))
        spcfd = lst[index].text.replace(replace_text, '')
        if ',' in spcfd:
            var = type_to_change(spcfd.replace(',', ''))
        else:
            var = type_to_change(spcfd)
        return var
    
    def scrape_single_stock(self, code):
        """
        単一の銘柄をスクレイピング
        """
        driver = None
        try:
            driver = self.create_driver()
            base_url = 'https://www.nikkei.com/nkd/company/?scode='
            current_url = base_url + str(code)
            
            driver.get(current_url)
            time.sleep(0.5)  # 短縮
            
            # 銘柄名
            stock_name = driver.title[1:].split('】')[0]
            
            # 直近時価
            try:
                last_price = self.ext_by_cn(driver, 'm-stockPriceElm_value', 0, ' 円', float)
            except:
                last_price = None
            
            # 予想PER
            try:
                expected_per = self.ext_by_cn(driver, 'm-stockInfo_detail_value', 4, ' 倍', float)
            except:
                expected_per = None
            
            # 予想配当利回り
            try:
                expected_dividend_yield = self.ext_by_cn(driver, 'm-stockInfo_detail_value', 5, ' ％', float)
            except:
                expected_dividend_yield = None
                
            # PBR実績値
            try:
                actual_pbr = self.ext_by_cn(driver, 'm-stockInfo_detail_value', 6, ' 倍', float)
            except:
                actual_pbr = None
                
            # 予想ROE
            try:
                expected_roe = self.ext_by_cn(driver, 'm-stockInfo_detail_value', 7, ' ％', float)
            except:
                expected_roe = None
                
            # ニュースがあるか
            try:
                news_id = self.wait_with_retry(driver, 10, 
                                             EC.presence_of_all_elements_located((By.ID, 'JSID_cwCompanyNews')))
                if len(news_id) > 0:
                    last_news_text = news_id[0].find_elements(By.CLASS_NAME, 'm-listItem_text_text')[0].text
                    a = news_id[0].find_elements(By.CLASS_NAME, 'm-listItem_text_text')[0]
                    last_news_url = a.find_element(By.TAG_NAME, 'a').get_attribute('href')
                else:
                    last_news_text = None
                    last_news_url = None
            except TimeoutException:
                last_news_text = None
                last_news_url = None
                
            # 適時開示
            try:
                dscl_id = self.wait_with_retry(driver, 30, 
                                             EC.presence_of_all_elements_located((By.ID, 'JSID_cwCompanyInfo')))
                last_disclosure_text = dscl_id[0].find_elements(By.CLASS_NAME, 'm-listItem_text_text')[0].text
                a = dscl_id[0].find_elements(By.CLASS_NAME, 'm-listItem_text_text')[0]
                last_disclosure_url = a.find_element(By.TAG_NAME, 'a').get_attribute('href')
            except TimeoutException:
                last_disclosure_text = None
                last_disclosure_url = None
            
            # 結果を返す
            return {
                'code': code,
                'current_url': current_url,
                'name': stock_name,
                'price': last_price,
                'expected_per': expected_per,
                'expected_dividend_yield': expected_dividend_yield,
                'expected_roe': expected_roe,
                'actual_pbr': actual_pbr,
                'last_news_text': last_news_text,
                'last_news_url': last_news_url,
                'last_disclosure_text': last_disclosure_text,
                'last_disclosure_url': last_disclosure_url
            }
            
        except Exception as e:
            self.logger.error(f"銘柄コード {code} の処理中にエラーが発生しました: {e}")
            return {
                'code': code,
                'current_url': base_url + str(code),
                'name': f"銘柄コード{code}",
                'price': None,
                'expected_per': None,
                'expected_dividend_yield': None,
                'expected_roe': None,
                'actual_pbr': None,
                'last_news_text': None,
                'last_news_url': None,
                'last_disclosure_text': None,
                'last_disclosure_url': None
            }
        finally:
            if driver:
                driver.quit()
    
    def scrape_all_stocks(self, codes):
        """
        すべての銘柄を並列でスクレイピング
        """
        self.logger.info(f"{len(codes)}件の銘柄を並列処理でスクレイピング開始")
        
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 並列実行
            future_to_code = {executor.submit(self.scrape_single_stock, code): code for code in codes}
            
            # 結果を収集
            for future in concurrent.futures.as_completed(future_to_code):
                code = future_to_code[future]
                try:
                    result = future.result()
                    results.append(result)
                    self.logger.info(f"銘柄コード {code} の処理完了")
                except Exception as e:
                    self.logger.error(f"銘柄コード {code} の処理で例外が発生: {e}")
                    # エラーが発生した場合のデフォルト値
                    results.append({
                        'code': code,
                        'current_url': f"https://www.nikkei.com/nkd/company/?scode={code}",
                        'name': f"銘柄コード{code}",
                        'price': None,
                        'expected_per': None,
                        'expected_dividend_yield': None,
                        'expected_roe': None,
                        'actual_pbr': None,
                        'last_news_text': None,
                        'last_news_url': None,
                        'last_disclosure_text': None,
                        'last_disclosure_url': None
                    })
        
        return results

def main():
    """
    メイン実行関数
    """
    # CSVの読み込み
    c = pd.read_csv('data/codes.csv', header=None)
    codes = []
    for cv in c.values:
        codes.append(cv[0])
    
    # 並列スクレイパーの初期化
    scraper = ParallelScraper(max_workers=4)
    
    # スクレイピング実行
    results = scraper.scrape_all_stocks(codes)
    
    # DataFrameの生成
    df = pd.DataFrame(results)
    
    # 必要な列のみを選択
    df_final = df[['code', 'current_url', 'name', 'price', 'expected_per', 
                   'expected_dividend_yield', 'expected_roe', 'actual_pbr']]
    
    # ファイルに保存
    df_final.to_csv("data/output.csv", index=False, encoding="UTF-8")
    print(f"スクレイピング完了: {len(results)}件の銘柄を処理しました")

if __name__ == "__main__":
    main() 