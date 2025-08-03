import os
from dotenv import load_dotenv
import logging
from pathlib import Path

class Config:
    """
    セキュアな設定管理クラス
    """
    
    def __init__(self, env_file='.env'):
        # 環境変数ファイルを読み込み
        load_dotenv(env_file)
        
        # API Keys
        self.alpha_vantage_api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.quandl_api_key = os.getenv('QUANDL_API_KEY')
        self.yahoo_finance_api_key = os.getenv('YAHOO_FINANCE_API_KEY')
        
        # j-Quants API Configuration
        self.jquants_refresh_token = os.getenv('JQUANTS_REFRESH_TOKEN')
        
        # Database Configuration
        self.database_url = os.getenv('DATABASE_URL')
        
        # Logging Configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('LOG_FILE', 'logs/app.log')
        
        # Scraping Configuration
        self.scraping_delay = int(os.getenv('SCRAPING_DELAY', '1'))
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        self.timeout = int(os.getenv('TIMEOUT', '30'))
        
        # File Paths
        self.codes_file = os.getenv('CODES_FILE', 'data/codes.csv')
        self.output_file = os.getenv('OUTPUT_FILE', 'data/output.csv')
        self.backup_dir = os.getenv('BACKUP_DIR', 'data/backup/')
        
        # ログディレクトリの作成
        self._setup_logging()
    
    def _setup_logging(self):
        """
        ログ設定の初期化
        """
        log_dir = Path(self.log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, self.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
    
    def validate_api_keys(self):
        """
        APIキーの存在確認
        """
        missing_keys = []
        
        if not self.alpha_vantage_api_key:
            missing_keys.append('ALPHA_VANTAGE_API_KEY')
        if not self.quandl_api_key:
            missing_keys.append('QUANDL_API_KEY')
        if not self.yahoo_finance_api_key:
            missing_keys.append('YAHOO_FINANCE_API_KEY')
        if not self.jquants_refresh_token:
            missing_keys.append('JQUANTS_REFRESH_TOKEN')
        
        if missing_keys:
            logging.warning(f"以下のAPIキーが設定されていません: {', '.join(missing_keys)}")
            return False
        
        return True
    
    def get_api_key(self, service_name):
        """
        指定されたサービスのAPIキーを取得
        
        Args:
            service_name (str): サービス名 ('alpha_vantage', 'quandl', 'yahoo_finance', 'jquants')
        
        Returns:
            str: APIキー（設定されていない場合はNone）
        """
        key_mapping = {
            'alpha_vantage': self.alpha_vantage_api_key,
            'quandl': self.quandl_api_key,
            'yahoo_finance': self.yahoo_finance_api_key,
            'jquants': self.jquants_refresh_token  # j-Quantsはrefresh_tokenを使用
        }
        
        return key_mapping.get(service_name)
    
    def get_jquants_config(self):
        """
        j-Quants APIの設定を取得
        
        Returns:
            dict: j-Quants設定辞書
        """
        return {
            'refresh_token': self.jquants_refresh_token
        }
    
    def is_development(self):
        """
        開発環境かどうかを判定
        """
        return os.getenv('ENVIRONMENT', 'development') == 'development'
    
    def get_backup_path(self, filename):
        """
        バックアップファイルのパスを生成
        
        Args:
            filename (str): ファイル名
        
        Returns:
            str: バックアップファイルの完全パス
        """
        backup_dir = Path(self.backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        return str(backup_dir / filename)

# グローバル設定インスタンス
config = Config() 