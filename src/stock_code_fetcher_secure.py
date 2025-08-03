import requests
import pandas as pd
import re
from bs4 import BeautifulSoup
import time
from datetime import datetime
import logging
from src.config import config
from src.jquants_client import JQuantsClient

class SecureStockCodeFetcher:
    """
    セキュリティを考慮した東証プライム上場企業の証券コード取得クラス
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 設定の検証
        self._validate_config()
        
        # ロガーの設定
        self.logger = logging.getLogger(__name__)
        
        # j-Quantsクライアントの初期化
        self.jquants_client = None
        try:
            self.jquants_client = JQuantsClient()
        except Exception as e:
            self.logger.warning(f"j-Quantsクライアントの初期化に失敗: {e}")
    
    def _validate_config(self):
        """
        設定の妥当性を検証
        """
        if not config.validate_api_keys():
            self.logger.warning("一部のAPIキーが設定されていません。一部の機能が制限される可能性があります。")
    
    def fetch_from_jquants(self):
        """
        j-Quants APIから東証プライム銘柄を取得
        """
        if not self.jquants_client:
            self.logger.warning("j-Quantsクライアントが利用できません")
            return None
        
        try:
            # 認証を実行
            if not self.jquants_client.authenticate():
                self.logger.error("j-Quants API認証に失敗しました")
                return None
            
            # 東証プライム銘柄コードを取得
            prime_codes = self.jquants_client.get_prime_stock_codes()
            
            if prime_codes:
                self.logger.info(f"j-Quantsから{len(prime_codes)}件の東証プライム銘柄コードを取得しました")
                return prime_codes
            else:
                self.logger.warning("j-Quantsから有効な東証プライム銘柄コードを取得できませんでした")
                return None
                
        except Exception as e:
            self.logger.error(f"j-Quants APIからの取得に失敗: {e}")
            return None
    
    def fetch_from_alpha_vantage(self):
        """
        Alpha Vantage APIから東証プライム銘柄を取得
        """
        api_key = config.get_api_key('alpha_vantage')
        if not api_key:
            self.logger.warning("Alpha Vantage APIキーが設定されていません")
            return None
        
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'LISTING_STATUS',
                'apikey': api_key
            }
            
            response = self.session.get(url, params=params, timeout=config.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # 日本株の東証プライム銘柄をフィルタリング
            prime_codes = []
            if 'data' in data:
                for item in data['data']:
                    if (item.get('exchange') == 'TSE' and 
                        item.get('market') == 'PRIME'):
                        prime_codes.append(item.get('symbol'))
            
            if prime_codes:
                self.logger.info(f"Alpha Vantageから{len(prime_codes)}件の銘柄コードを取得しました")
                return prime_codes
            else:
                self.logger.warning("Alpha Vantageから有効な銘柄コードを取得できませんでした")
                return None
            
        except Exception as e:
            self.logger.error(f"Alpha Vantage APIからの取得に失敗: {e}")
            return None
    
    def fetch_from_quandl(self):
        """
        Quandl APIから日本株データを取得
        """
        api_key = config.get_api_key('quandl')
        if not api_key:
            self.logger.warning("Quandl APIキーが設定されていません")
            return None
        
        try:
            url = f"https://www.quandl.com/api/v3/datasets/WIKI/PRICES.json"
            params = {
                'api_key': api_key,
                'limit': 1000
            }
            
            response = self.session.get(url, params=params, timeout=config.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # 日本株の銘柄コードを抽出
            codes = []
            if 'datasets' in data:
                for dataset in data['datasets']:
                    code = dataset.get('dataset_code')
                    if code and code.isdigit() and len(code) == 4:
                        codes.append(code)
            
            if codes:
                self.logger.info(f"Quandlから{len(codes)}件の銘柄コードを取得しました")
                return codes
            else:
                self.logger.warning("Quandlから有効な銘柄コードを取得できませんでした")
                return None
            
        except Exception as e:
            self.logger.error(f"Quandl APIからの取得に失敗: {e}")
            return None
    
    def fetch_from_jpx_official(self):
        """
        JPX公式サイトから上場企業情報を取得
        """
        try:
            url = "https://www.jpx.co.jp/listing/stocks/new/index.html"
            
            response = self.session.get(url, timeout=config.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 東証プライム銘柄を抽出（実際のHTML構造に基づいて実装）
            codes = []
            # ここでHTMLから銘柄コードを抽出する処理を実装
            
            if codes:
                self.logger.info(f"JPX公式サイトから{len(codes)}件の銘柄コードを取得しました")
                return codes
            else:
                self.logger.warning("JPX公式サイトから有効な銘柄コードを取得できませんでした")
                return None
            
        except Exception as e:
            self.logger.error(f"JPX公式サイトからの取得に失敗: {e}")
            return None
    
    def fetch_from_local_backup(self):
        """
        ローカルバックアップファイルから取得（フォールバック用）
        """
        try:
            df = pd.read_csv(config.codes_file, header=None)
            codes = df[0].tolist()
            
            if codes:
                self.logger.info(f"ローカルバックアップから{len(codes)}件の銘柄コードを読み込みました")
                return codes
            else:
                self.logger.warning("ローカルバックアップファイルが空です")
                return None
                
        except Exception as e:
            self.logger.error(f"ローカルバックアップからの取得に失敗: {e}")
            return None
    
    def get_prime_stock_codes(self, method='auto'):
        """
        東証プライム上場企業の証券コードを取得
        
        Args:
            method (str): 取得方法 ('auto', 'jquants', 'alpha_vantage', 'quandl', 'jpx', 'local')
        
        Returns:
            list: 証券コードのリスト
        """
        if method == 'auto':
            methods = ['jquants', 'alpha_vantage', 'quandl', 'jpx', 'local']
        else:
            methods = [method]
        
        for method_name in methods:
            self.logger.info(f"{method_name}から銘柄コードを取得中...")
            
            if method_name == 'jquants':
                codes = self.fetch_from_jquants()
            elif method_name == 'alpha_vantage':
                codes = self.fetch_from_alpha_vantage()
            elif method_name == 'quandl':
                codes = self.fetch_from_quandl()
            elif method_name == 'jpx':
                codes = self.fetch_from_jpx_official()
            elif method_name == 'local':
                codes = self.fetch_from_local_backup()
            else:
                continue
            
            if codes and len(codes) > 0:
                self.logger.info(f"{method_name}から{len(codes)}件の銘柄コードを取得しました")
                return codes
        
        self.logger.error("すべての方法で銘柄コードの取得に失敗しました")
        return []
    
    def save_codes_to_file(self, codes, filename=None):
        """
        取得した銘柄コードをファイルに保存
        
        Args:
            codes (list): 証券コードのリスト
            filename (str): 保存先ファイル名（Noneの場合は設定ファイルの値を使用）
        """
        if filename is None:
            filename = config.output_file
        
        try:
            df = pd.DataFrame(codes, columns=['code'])
            df.to_csv(filename, index=False, header=False)
            self.logger.info(f"{len(codes)}件の銘柄コードを{filename}に保存しました")
            
            # バックアップも作成
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"codes_backup_{timestamp}.csv"
            backup_path = config.get_backup_path(backup_filename)
            df.to_csv(backup_path, index=False, header=False)
            self.logger.info(f"バックアップを{backup_path}に保存しました")
            
        except Exception as e:
            self.logger.error(f"ファイル保存に失敗: {e}")
    
    def validate_codes(self, codes):
        """
        取得した銘柄コードの妥当性を検証
        
        Args:
            codes (list): 証券コードのリスト
        
        Returns:
            list: 検証済みの証券コードのリスト
        """
        validated_codes = []
        
        for code in codes:
            code_str = str(code)
            
            # 基本的な検証（4桁または5桁の数字）
            if (code_str.isdigit() and
                (len(code_str) == 4 or len(code_str) == 5) and
                1000 <= int(code) <= 99999):
                validated_codes.append(code)
        
        self.logger.info(f"検証前: {len(codes)}件, 検証後: {len(validated_codes)}件")
        return validated_codes

def main():
    """
    メイン実行関数
    """
    fetcher = SecureStockCodeFetcher()
    
    # 銘柄コードを取得
    codes = fetcher.get_prime_stock_codes(method='auto')
    
    if codes:
        # コードの妥当性を検証
        validated_codes = fetcher.validate_codes(codes)
        
        if validated_codes:
            # 取得したコードを保存
            fetcher.save_codes_to_file(validated_codes)
            print(f"取得した銘柄コード数: {len(validated_codes)}")
            print(f"最初の10件: {validated_codes[:10]}")
        else:
            print("有効な銘柄コードが見つかりませんでした")
    else:
        print("銘柄コードの取得に失敗しました")

if __name__ == "__main__":
    main() 