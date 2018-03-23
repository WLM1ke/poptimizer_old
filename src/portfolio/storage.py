"""Local file storage for pandas dataframes"""

from pathlib import Path
import time

import pandas as pd


DATA_PATH = Path(__file__).parents[2] / 'data'


def make_path(filename: str, subfolder: str = '') -> str:
    """Returns path to file"""
    folder = DATA_PATH / subfolder
    if not folder.exists():
        folder.mkdir(parents=True)
    return str(folder / filename)

class LocalFile:    
    allowed_subfolders = ['dividend']
    
    def __init__(self, filename: str, subfolder: str = ''):
        if subfolder and subfolder not in self.allowed_subfolders:
            raise ValueError(f'{subfolder} not supported')
        self.path = make_path(filename, subfolder)
    
    # FIXME: must change from physical to logical check of updates    
    def _time_updated(self):
        # https://docs.python.org/3/library/os.html#os.stat_result.st_mtime
        return Path(self.path).stat().st_mtime

    def _updated_days_ago(self):
        lag_sec = time.time() -  self._time_updated()
        return lag_sec / (60 * 60 * 24)
    
    def is_updated(self):
        """Обновление нужно, если прошло менее 1 дня с момента обновления файла."""
        return self._updated_days_ago() < 1
    # end FIXME
        
    def save_dataframe(self, df):
        df.to_csv(self.path, index=True, header=True)
        
    #TODO: manage colunmn converters
    def read_dataframe(self):    
        df = pd.read_csv(self.path,
                     converters={'DATE': pd.to_datetime},
                     header=0,
                     engine='python',
                     sep='\s*,')
        df = df.set_index('DATE')
        return df    
    
FILE_CPI = LocalFile('CPI.csv')    
