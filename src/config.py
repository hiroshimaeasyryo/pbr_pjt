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
        
        # j-Quants API Configuration
        self.jquants_refresh_token = os.getenv('JQUANTS_REFRESH_TOKEN')
        
        # Database Configuration
        self.database_url = os.getenv('DATABASE_URL')
        
        # Logging Configuration
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        self.log_file = os.getenv('LOG_FILE', 'logs/app.log')
        
        # Scraping Configuration
        self.scraping_delay = float(os.getenv('SCRAPING_DELAY', '1'))
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
        if not self.jquants_refresh_token:
            logging.warning("JQUANTS_REFRESH_TOKENが設定されていません")
            return False
        
        return True
    
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