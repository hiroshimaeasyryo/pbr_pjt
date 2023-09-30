import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time 


# csvの読み込み
c = pd.read_csv('data/codes.csv', header=None)
codes = []
for cv in c.values:
    codes.append(cv[0])

# WebDriverの設定
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

base_url = 'https://www.nikkei.com/nkd/company/?scode='

# クラス名を指定して要素を抽出する
def ext_by_cn(class_name, int, replace_text, type_to_change):
    lst = WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, class_name))
    )
    spcfd = lst[int].text.replace(replace_text, '')
    if ',' in spcfd:
        var = type_to_change(spcfd.replace(',', ''))
    else:
        var = type_to_change(spcfd)
    return var 

current_urls = []
stock_names = []
last_prices = []
expected_pers = []
expected_dividend_yields = []
expected_roes = []
actual_pbrs = []
last_news_texts = []
last_news_urls = []
last_disclosures = []
last_disclosure_urls = []

counter = 0

# ループ
for code in codes:
    
    current_url = base_url + str(code)
    driver.get(current_url)
    
    # カレントURLを取得する
    current_url = base_url + str(code)
    current_urls.append(current_url)
    
    # カレントURLにアクセスする
    driver.get(current_url)
    
    # 待機処理
    time.sleep(1)
    
    # 初回だけ「株価指標ボタン」を押下する
    if counter == 0:
        btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'm-stockInfo_btn_open')))
        driver.execute_script("arguments[0].click();", btn)
    else:
        pass

    # 邪魔なのでウィンドウサイズを最小化
    driver.minimize_window()

    # 銘柄名
    stock_name = driver.title[1:].split('】')[0]
    stock_names.append(stock_name)
    
    # 直近時価
    try:
        last_price = ext_by_cn('m-stockPriceElm_value', 0, ' 円', float)
        last_prices.append(last_price)
    except:
        last_prices.append(None)
    
    # 予想PER
    try:
        expected_per = ext_by_cn('m-stockInfo_detail_value', 4, ' 倍', float)
        expected_pers.append(expected_per)
    except:
        expected_pers.append(None)
    
    # 予想配当利回り
    try:
        expected_dividend_yield = ext_by_cn('m-stockInfo_detail_value', 5, ' ％', float)
        expected_dividend_yields.append(expected_dividend_yield)
    except:
        expected_dividend_yields.append(None)
        
    # PBR実績値
    try:
        actual_pbr = ext_by_cn('m-stockInfo_detail_value', 6, ' 倍', float)
        actual_pbrs.append(actual_pbr)
    except:
        actual_pbrs.append(None)
        
    # 予想ROE
    try:
        expected_roe = ext_by_cn('m-stockInfo_detail_value', 7, ' ％', float)
        expected_roes.append(expected_roe)
    except:
        expected_roes.append(None)
        
    # ニュースがあるか
    try:
        news_id = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.ID, 'JSID_cwCompanyNews')))
    except:
        news_id =[]
    
    # ニュースがあったら
    if len(news_id) > 0:
        last_news_text = news_id[0].find_elements(By.CLASS_NAME, 'm-listItem_text_text')[0].text
        last_news_texts.append(last_news_text)
        
        a = news_id[0].find_elements(By.CLASS_NAME, 'm-listItem_text_text')[0]
        last_news_url = a.find_element(By.TAG_NAME, 'a').get_attribute('href')
        last_news_urls.append(last_news_url)
    
    else:
        last_news_texts.append(None)
        last_news_urls.append(last_news_url)
        
    # 適時開示
    dscl_id = WebDriverWait(driver, 30).until(
        EC.presence_of_all_elements_located((By.ID, 'JSID_cwCompanyInfo')))        
    last_disclosure_text = dscl_id[0].find_elements(By.CLASS_NAME, 'm-listItem_text_text')[0].text
    last_disclosures.append(last_disclosure_text)

    a = dscl_id[0].find_elements(By.CLASS_NAME, 'm-listItem_text_text')[0]
    last_disclosure_url = a.find_element(By.TAG_NAME, 'a').get_attribute('href')
    last_disclosure_urls.append(last_disclosure_url)
        
    counter +=1
    
# dataframeの生成
df = pd.DataFrame({
    'code': codes[:len(stock_names)],
    'current_url': current_urls,
    'name': stock_names,
    'price': last_prices,
    'expected_per': expected_pers,
    'expected_dividend_yield': expected_dividend_yields,
    'expected_roe': expected_roes,
    'actual_pbr': actual_pbrs})

# dfの保存
df.to_csv("data/output.csv", index=False, encoding="UTF-8")

driver.close()