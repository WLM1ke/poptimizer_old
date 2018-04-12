"""Load and update local daily data for MOEX Russia Net Total Return (Resident).

    index()
"""
import pandas as pd

from portfolio_optimizer import web
from portfolio_optimizer.local.local_quotes import LocalQuotes
from portfolio_optimizer.settings import DATE, CLOSE_PRICE

INDEX_FOLDER = 'index'
INDEX_TICKER = 'MCFTRR'


class LocalIndex(LocalQuotes):
    """Реализует хранение, обновление и хранение локальных данных по индексу MCFTRR."""
    _data_folder = INDEX_FOLDER
    _load_converter = {DATE: pd.to_datetime, CLOSE_PRICE: pd.to_numeric}
    _data_columns = CLOSE_PRICE

    def __init__(self):
        super().__init__(INDEX_TICKER)

    def update_local_history(self):
        """Обновляет локальные данные данными из интернета и возвращает полную историю котировок индекса."""
        self.df = self.load_local_history()
        if self.need_update():
            df_update = web.index(self.df_last_date)
            self._validate_new_data(df_update)
            self.df = pd.concat([self.df, df_update.iloc[1:]])
            self._save_history()

    def create_local_history(self):
        """Формирует, сохраняет и возвращает локальную версию историю котировок индекса."""
        self.df = web.index()
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
