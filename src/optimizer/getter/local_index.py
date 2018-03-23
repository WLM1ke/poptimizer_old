"""Load and update local daily data for MOEX Russia Net Total Return (Resident).

    get_index_history()
"""
import pandas as pd

from optimizer import download
from optimizer.getter.local_quotes import LocalQuotes
from optimizer.settings import DATE, CLOSE_PRICE

INDEX_FOLDER = 'index'
INDEX_TICKER = 'MCFTRR'


class LocalIndex(LocalQuotes):
    """Реализует хранение, обновление и хранение локальных данных по индексу MCFTRR."""
    _data_folder = INDEX_FOLDER
    _load_converter = {DATE: pd.to_datetime, CLOSE_PRICE: pd.to_numeric}
    _data_columns = CLOSE_PRICE

    def __init__(self):
        super().__init__(INDEX_TICKER)

    def _validate_new_data(self, df_new):
        """Проверяет совпадение данных на стыке, то есть для последней даты старого DataFrame."""
        last_date = self.df_last_date
        df_old_last = self.df.loc[last_date]
        df_new_last = df_new.loc[last_date]
        if df_old_last != df_new_last:
            raise ValueError(f'Загруженные данные {self.ticker} не стыкуются с локальными. \n' +
                             f'{df_old_last} \n' +
                             f'{df_new_last}')

    def update_local_history(self):
        """Обновляет локальные данные данными из интернета и возвращает полную историю котировок индекса."""
        self.df = self.load_local_history()
        if self.need_update():
            df_update = download.index_history(self.df_last_date)
            self._validate_new_data(df_update)
            self.df = pd.concat([self.df, df_update.iloc[1:]])
            self._save_history()

    def create_local_history(self):
        """Формирует, сохраняет и возвращает локальную версию историю котировок индекса."""
        self.df = download.index_history()
        self._save_history()


def get_index_history():
    """
    Возвращает историю индекса полной доходности с учетом российских налогов из локальных данных.

    При необходимости локальные данные обновляются для ускорения последующих загрузок.

    Returns
    -------
    pandas.Series
        В строках даты торгов.
        В столбце цена закрытия индекса.
    """
    return LocalIndex().df


if __name__ == '__main__':
    print(get_index_history())
