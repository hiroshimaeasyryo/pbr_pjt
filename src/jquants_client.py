import requests
import json
import time
from datetime import datetime, timedelta
import logging
from src.config import config

class JQuantsClient:
    """
    j-Quants APIクライアントクラス
    """
    
    def __init__(self):
        self.base_url = "https://api.jquants.com/v1"
        self.session = requests.Session()
        self.id_token = None
        self.token_expires_at = None
        
        # ロガーの設定
        self.logger = logging.getLogger(__name__)
        
        # 設定の取得
        self.jquants_config = config.get_jquants_config()
        
        if not self.jquants_config['refresh_token']:
            self.logger.error("j-Quants API設定が不完全です")
            raise ValueError("j-Quants API設定が不完全です")
    
    def authenticate(self):
        """
        j-Quants APIの認証を実行
        リフレッシュトークンを使用してIDトークンを取得
        """
        try:
            # リフレッシュトークンを使用してIDトークンを取得
            # API仕様: https://jpx.gitbook.io/j-quants-ja/api-reference/idtoken
            url = f"{self.base_url}/token/auth_refresh"
            params = {
                'refreshtoken': self.jquants_config["refresh_token"]
            }
            
            response = self.session.post(url, params=params, timeout=config.timeout)
            response.raise_for_status()
            
            data = response.json()
            self.id_token = data.get('idToken')
            
            if not self.id_token:
                raise ValueError("IDトークンの取得に失敗しました")
            
            # トークンの有効期限を設定（24時間）
            self.token_expires_at = datetime.now() + timedelta(hours=24)
            
            self.logger.info("j-Quants API認証が成功しました")
            return True
            
        except Exception as e:
            self.logger.error(f"j-Quants API認証に失敗: {e}")
            return False
    
    def _ensure_authenticated(self):
        """
        認証状態を確認し、必要に応じて再認証を実行
        """
        if (not self.id_token or 
            (self.token_expires_at and datetime.now() >= self.token_expires_at)):
            return self.authenticate()
        return True
    
    def get_listed_info(self):
        """
        上場企業情報を取得
        
        Returns:
            list: 上場企業情報のリスト
        """
        if not self._ensure_authenticated():
            return None
        
        try:
            url = f"{self.base_url}/listed/info"
            headers = {
                'Authorization': f'Bearer {self.id_token}'
            }
            
            response = self.session.get(url, headers=headers, timeout=config.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if 'info' in data:
                self.logger.info(f"j-Quantsから{len(data['info'])}件の上場企業情報を取得しました")
                return data['info']
            else:
                self.logger.warning("j-Quantsから有効な上場企業情報を取得できませんでした")
                return None
                
        except Exception as e:
            self.logger.error(f"上場企業情報の取得に失敗: {e}")
            return None
    
    def get_prime_stock_codes(self):
        """
        東証プライム銘柄の証券コードを取得
        
        Returns:
            list: 証券コードのリスト
        """
        listed_info = self.get_listed_info()
        
        if not listed_info:
            return []
        
        prime_codes = []
        
        # デバッグ情報を追加
        self.logger.info(f"取得した企業数: {len(listed_info)}")
        
        # 最初の数件のデータ構造を確認
        if listed_info:
            sample_companies = listed_info[:3]
            self.logger.info(f"サンプル企業データ: {sample_companies}")
        
        for company in listed_info:
            # データ構造を確認して適切なフィールドを使用
            market_name = company.get('MarketCodeName') or company.get('market_code_name')
            code = company.get('Code') or company.get('code')
            
            # 東証プライム銘柄の条件をチェック
            if (market_name == 'プライム' and 
                code and 
                str(code).isdigit()):
                prime_codes.append(str(code))
        
        self.logger.info(f"東証プライム銘柄: {len(prime_codes)}件")
        if prime_codes:
            self.logger.info(f"最初の10件: {prime_codes[:10]}")
        
        return prime_codes
    
    def get_stock_prices(self, codes, date=None):
        """
        株価情報を取得
        
        Args:
            codes (list): 証券コードのリスト
            date (str): 日付（YYYY-MM-DD形式、Noneの場合は最新）
        
        Returns:
            list: 株価情報のリスト
        """
        if not self._ensure_authenticated():
            return None
        
        if not codes:
            return []
        
        try:
            # 日付の設定（最新の営業日を取得するか、過去の日付を使用）
            if not date:
                # 最新の営業日を取得するか、過去の日付を使用
                # 例: 2024年12月31日（年末の営業日）
                date = '2024-12-30'
            
            url = f"{self.base_url}/prices/daily_quotes"
            headers = {
                'Authorization': f'Bearer {self.id_token}'
            }
            
            # 一度に取得する銘柄数を制限（API制限を考慮）
            batch_size = 10
            all_prices = []
            
            for i in range(0, len(codes), batch_size):
                batch_codes = codes[i:i + batch_size]
                
                params = {
                    'date': date,
                    'code': ','.join(map(str, batch_codes))
                }
                
                self.logger.info(f"株価情報取得中: {len(batch_codes)}件 (バッチ {i//batch_size + 1})")
                
                response = self.session.get(url, headers=headers, params=params, timeout=config.timeout)
                response.raise_for_status()
                
                data = response.json()
                
                if 'daily_quotes' in data and data['daily_quotes']:
                    all_prices.extend(data['daily_quotes'])
                    self.logger.info(f"バッチ {i//batch_size + 1} で{len(data['daily_quotes'])}件の株価情報を取得")
                else:
                    self.logger.warning(f"バッチ {i//batch_size + 1} で株価情報を取得できませんでした")
                
                # API制限を考慮して少し待機
                time.sleep(0.1)
            
            if all_prices:
                self.logger.info(f"j-Quantsから合計{len(all_prices)}件の株価情報を取得しました")
                return all_prices
            else:
                self.logger.warning("j-Quantsから有効な株価情報を取得できませんでした")
                return None
                
        except Exception as e:
            self.logger.error(f"株価情報の取得に失敗: {e}")
            return None
    
    def get_financial_statements(self, codes):
        """
        財務諸表情報を取得
        
        Args:
            codes (list): 証券コードのリスト
        
        Returns:
            list: 財務諸表情報のリスト
        """
        if not self._ensure_authenticated():
            return None
        
        if not codes:
            return []
        
        try:
            url = f"{self.base_url}/fins/statements"
            headers = {
                'Authorization': f'Bearer {self.id_token}'
            }
            
            params = {
                'code': ','.join(map(str, codes))
            }
            
            response = self.session.get(url, headers=headers, params=params, timeout=config.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if 'statements' in data:
                self.logger.info(f"j-Quantsから{len(data['statements'])}件の財務諸表情報を取得しました")
                return data['statements']
            else:
                self.logger.warning("j-Quantsから有効な財務諸表情報を取得できませんでした")
                return None
                
        except Exception as e:
            self.logger.error(f"財務諸表情報の取得に失敗: {e}")
            return None

def main():
    """
    メイン実行関数（テスト用）
    """
    try:
        client = JQuantsClient()
        
        # 認証テスト
        if client.authenticate():
            print("認証成功")
            
            # 東証プライム銘柄コードを取得
            prime_codes = client.get_prime_stock_codes()
            print(f"東証プライム銘柄数: {len(prime_codes)}")
            
            if prime_codes:
                print(f"最初の10件: {prime_codes[:10]}")
                
                # 最初の5件の株価情報を取得
                sample_codes = prime_codes[:5]
                prices = client.get_stock_prices(sample_codes)
                
                if prices:
                    print(f"株価情報取得数: {len(prices)}")
        else:
            print("認証失敗")
            
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    main() 