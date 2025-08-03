import pandas as pd
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import logging
from src.config import config

class DataManager:
    """
    時系列データ管理クラス
    """
    
    def __init__(self):
        self.history_dir = Path("data/history")
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # 履歴メタデータファイル
        self.metadata_file = self.history_dir / "metadata.json"
        self._load_metadata()
    
    def _load_metadata(self):
        """
        メタデータを読み込み
        """
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {
                'last_update': None,
                'total_files': 0,
                'data_points': 0,
                'file_list': []
            }
    
    def _save_metadata(self):
        """
        メタデータを保存
        """
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def save_daily_data(self, data, date=None):
        """
        日次データを保存
        
        Args:
            data (pd.DataFrame): 保存するデータ
            date (str): 日付（YYYY-MM-DD形式、Noneの場合は今日）
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # ファイル名を生成
        filename = f"daily_{date}.csv"
        filepath = self.history_dir / filename
        
        try:
            # データを保存
            data.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            # メタデータを更新
            file_info = {
                'date': date,
                'filename': filename,
                'rows': len(data),
                'columns': len(data.columns),
                'file_size': filepath.stat().st_size,
                'created_at': datetime.now().isoformat()
            }
            
            # 既存のエントリを更新または新規追加
            existing_index = None
            for i, item in enumerate(self.metadata['file_list']):
                if item['date'] == date:
                    existing_index = i
                    break
            
            if existing_index is not None:
                self.metadata['file_list'][existing_index] = file_info
            else:
                self.metadata['file_list'].append(file_info)
            
            self.metadata['last_update'] = datetime.now().isoformat()
            self.metadata['total_files'] = len(self.metadata['file_list'])
            self.metadata['data_points'] = sum(item['rows'] for item in self.metadata['file_list'])
            
            self._save_metadata()
            
            self.logger.info(f"日次データを保存しました: {filename} ({len(data)}行)")
            
        except Exception as e:
            self.logger.error(f"データ保存に失敗: {e}")
            raise
    
    def load_daily_data(self, date):
        """
        指定日のデータを読み込み
        
        Args:
            date (str): 日付（YYYY-MM-DD形式）
        
        Returns:
            pd.DataFrame: データ（存在しない場合はNone）
        """
        filename = f"daily_{date}.csv"
        filepath = self.history_dir / filename
        
        if filepath.exists():
            try:
                data = pd.read_csv(filepath, encoding='utf-8-sig')
                self.logger.info(f"日次データを読み込みました: {filename} ({len(data)}行)")
                return data
            except Exception as e:
                self.logger.error(f"データ読み込みに失敗: {e}")
                return None
        else:
            self.logger.warning(f"データファイルが存在しません: {filename}")
            return None
    
    def get_available_dates(self):
        """
        利用可能な日付のリストを取得
        
        Returns:
            list: 日付のリスト（降順）
        """
        dates = []
        for item in self.metadata['file_list']:
            dates.append(item['date'])
        
        return sorted(dates, reverse=True)
    
    def get_time_series_data(self, start_date=None, end_date=None, columns=None):
        """
        時系列データを取得
        
        Args:
            start_date (str): 開始日（YYYY-MM-DD形式）
            end_date (str): 終了日（YYYY-MM-DD形式）
            columns (list): 取得する列名のリスト
        
        Returns:
            pd.DataFrame: 時系列データ
        """
        available_dates = self.get_available_dates()
        
        if not available_dates:
            return pd.DataFrame()
        
        # 日付範囲を設定
        if start_date is None:
            start_date = available_dates[-1]
        if end_date is None:
            end_date = available_dates[0]
        
        # 日付範囲内のデータを取得
        data_list = []
        for date in available_dates:
            if start_date <= date <= end_date:
                data = self.load_daily_data(date)
                if data is not None:
                    # 日付列を追加
                    data['date'] = date
                    data_list.append(data)
        
        if not data_list:
            return pd.DataFrame()
        
        # データを結合
        combined_data = pd.concat(data_list, ignore_index=True)
        
        # 列を指定した場合はフィルタリング
        if columns:
            available_columns = [col for col in columns if col in combined_data.columns]
            if available_columns:
                combined_data = combined_data[available_columns + ['date']]
        
        self.logger.info(f"時系列データを取得しました: {len(combined_data)}行 ({start_date} ～ {end_date})")
        return combined_data
    
    def cleanup_old_files(self, keep_days=365):
        """
        古いファイルを削除
        
        Args:
            keep_days (int): 保持する日数
        """
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        cutoff_date_str = cutoff_date.strftime('%Y-%m-%d')
        
        files_to_remove = []
        for item in self.metadata['file_list']:
            if item['date'] < cutoff_date_str:
                files_to_remove.append(item)
        
        for item in files_to_remove:
            filepath = self.history_dir / item['filename']
            if filepath.exists():
                filepath.unlink()
                self.logger.info(f"古いファイルを削除しました: {item['filename']}")
        
        # メタデータから削除
        self.metadata['file_list'] = [
            item for item in self.metadata['file_list'] 
            if item['date'] >= cutoff_date_str
        ]
        
        self.metadata['total_files'] = len(self.metadata['file_list'])
        self.metadata['data_points'] = sum(item['rows'] for item in self.metadata['file_list'])
        
        self._save_metadata()
        
        self.logger.info(f"古いファイルのクリーンアップ完了: {len(files_to_remove)}件削除")
    
    def get_statistics(self):
        """
        データ統計情報を取得
        
        Returns:
            dict: 統計情報
        """
        if not self.metadata['file_list']:
            return {
                'total_files': 0,
                'total_data_points': 0,
                'date_range': None,
                'average_daily_records': 0
            }
        
        dates = [item['date'] for item in self.metadata['file_list']]
        total_records = sum(item['rows'] for item in self.metadata['file_list'])
        
        return {
            'total_files': len(self.metadata['file_list']),
            'total_data_points': total_records,
            'date_range': {
                'start': min(dates),
                'end': max(dates)
            },
            'average_daily_records': total_records / len(self.metadata['file_list']) if self.metadata['file_list'] else 0
        }

def main():
    """
    テスト用メイン関数
    """
    manager = DataManager()
    
    # 統計情報を表示
    stats = manager.get_statistics()
    print("データ統計情報:")
    print(f"  総ファイル数: {stats['total_files']}")
    print(f"  総データポイント: {stats['total_data_points']}")
    print(f"  日次平均レコード数: {stats['average_daily_records']:.1f}")
    
    if stats['date_range']:
        print(f"  データ期間: {stats['date_range']['start']} ～ {stats['date_range']['end']}")
    
    # 利用可能な日付を表示
    dates = manager.get_available_dates()
    print(f"\n利用可能な日付: {len(dates)}件")
    if dates:
        print(f"  最新: {dates[0]}")
        print(f"  最古: {dates[-1]}")

if __name__ == "__main__":
    main() 