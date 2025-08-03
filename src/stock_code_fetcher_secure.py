import requests
import pandas as pd
import re
from bs4 import BeautifulSoup
import time
from datetime import datetime
import logging
from src.config import config
from src.jquants_client import JQuantsClient
import os

class SecureStockCodeFetcher:
    """
    セキュリティを考慮した東証プライム上場企業の証券コード取得クラス
    """
    
    def __init__(self):
        # ロガーの設定（最初に初期化）
        self.logger = logging.getLogger(__name__)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # 設定の検証
        self._validate_config()
        
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
        if not config.jquants_refresh_token:
            self.logger.warning("JQUANTS_REFRESH_TOKENが設定されていません。j-Quants APIが利用できません。")
    
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
    
    def fetch_from_jpx_official(self):
        """
        日本取引所グループ公式サイトから東証プライム銘柄を取得
        """
        try:
            url = "https://www.jpx.co.jp/listing/stocks/new/index.html"
            response = self.session.get(url, timeout=config.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 東証プライム銘柄のテーブルを探す
            tables = soup.find_all('table')
            prime_codes = []
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        # 証券コードを抽出
                        code_cell = cells[0].get_text(strip=True)
                        if code_cell.isdigit() and len(code_cell) == 4:
                            prime_codes.append(code_cell)
            
            if prime_codes:
                self.logger.info(f"日本取引所グループ公式サイトから{len(prime_codes)}件の銘柄コードを取得しました")
                return prime_codes
            else:
                self.logger.warning("日本取引所グループ公式サイトから有効な銘柄コードを取得できませんでした")
                return None
                
        except Exception as e:
            self.logger.error(f"日本取引所グループ公式サイトからの取得に失敗: {e}")
            return None
    
    def fetch_from_local_backup(self):
        """
        ローカルバックアップファイルから銘柄コードを取得
        """
        try:
            backup_file = config.get_backup_path('prime_stock_codes.csv')
            if os.path.exists(backup_file):
                df = pd.read_csv(backup_file)
                codes = df['code'].astype(str).tolist()
                self.logger.info(f"ローカルバックアップから{len(codes)}件の銘柄コードを取得しました")
                return codes
            else:
                self.logger.warning("ローカルバックアップファイルが見つかりません")
                return None
        except Exception as e:
            self.logger.error(f"ローカルバックアップからの取得に失敗: {e}")
            return None
    
    def get_prime_stock_codes(self, method='auto'):
        """
        東証プライム銘柄コードを取得
        
        Args:
            method (str): 取得方法 ('auto', 'jquants', 'jpx', 'backup')
        
        Returns:
            list: 銘柄コードのリスト
        """
        if method == 'auto':
            # 優先順位: j-Quants > 日本取引所グループ公式 > ローカルバックアップ
            methods = ['jquants', 'jpx', 'backup']
        else:
            methods = [method]
        
        for method_name in methods:
            self.logger.info(f"{method_name}から銘柄コードを取得中...")
            
            if method_name == 'jquants':
                codes = self.fetch_from_jquants()
            elif method_name == 'jpx':
                codes = self.fetch_from_jpx_official()
            elif method_name == 'backup':
                codes = self.fetch_from_local_backup()
            else:
                self.logger.warning(f"未知の取得方法: {method_name}")
                continue
            
            if codes:
                # 取得したコードを検証
                validated_codes = self.validate_codes(codes)
                if validated_codes:
                    self.logger.info(f"有効な銘柄コード{len(validated_codes)}件を取得しました")
                    return validated_codes
                else:
                    self.logger.warning(f"{method_name}から取得したコードが無効でした")
            else:
                self.logger.warning(f"{method_name}から銘柄コードを取得できませんでした")
        
        self.logger.error("すべての取得方法で失敗しました")
        return []
    
    def save_codes_to_file(self, codes, filename=None):
        """
        銘柄コードをファイルに保存
        
        Args:
            codes (list): 銘柄コードのリスト
            filename (str): 保存先ファイル名（省略時はデフォルト）
        """
        if not filename:
            filename = config.codes_file
        
        try:
            df = pd.DataFrame({'code': codes})
            df.to_csv(filename, index=False, header=False)
            self.logger.info(f"銘柄コード{len(codes)}件を{filename}に保存しました")
            
            # バックアップも作成
            backup_filename = f"prime_stock_codes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            backup_path = config.get_backup_path(backup_filename)
            df.to_csv(backup_path, index=False)
            self.logger.info(f"バックアップを{backup_path}に保存しました")
            
        except Exception as e:
            self.logger.error(f"ファイル保存に失敗: {e}")
    
    def validate_codes(self, codes):
        """
        銘柄コードの妥当性を検証
        
        Args:
            codes (list): 銘柄コードのリスト
        
        Returns:
            list: 有効な銘柄コードのリスト
        """
        valid_codes = []
        
        for code in codes:
            code_str = str(code).strip()
            
            # 4桁の数字かチェック
            if re.match(r'^\d{4}$', code_str):
                valid_codes.append(code_str)
            else:
                self.logger.debug(f"無効な銘柄コードをスキップ: {code}")
        
        return valid_codes

def main():
    """
    メイン実行関数
    """
    fetcher = SecureStockCodeFetcher()
    
    # 銘柄コードを取得
    codes = fetcher.get_prime_stock_codes()
    
    if codes:
        # ファイルに保存
        fetcher.save_codes_to_file(codes)
        print(f"東証プライム銘柄コード{len(codes)}件を取得・保存しました")
    else:
        print("銘柄コードの取得に失敗しました")

if __name__ == "__main__":
    main() 