"""Загружает котировки индекса полной доходности с учетом российских налогов с http://iss.moex.com"""

import pandas as pd

from web.labels import CLOSE_PRICE, DATE
from web.moex.iss_quotes import Quotes


class Index(Quotes):
    """Представление ответа сервера по индексу полной доходности MOEX в виде итератора

    При большом запросе сервер ISS возвращает данные блоками обычно по 100 значений, поэтому класс является итератором
    Если начальная дата не указана, то загружается вся доступная история котировок
    """
    _base_url = 'http://iss.moex.com/iss/history/engines/stock/markets/index/boards/RTSI/securities/'
    _ticker = 'MCFTRR'

    def __init__(self, start_date):
        super().__init__(self._ticker, start_date)

    def get_df(self, block_position):
        """Выбирает из сырого DataFrame только с необходимые колонки - даты и цены закрытия"""
        json_data = self.get_json_data(block_position)
        df = pd.DataFrame(**json_data)
        df[DATE] = pd.to_datetime(df['TRADEDATE'])
        df[CLOSE_PRICE] = pd.to_numeric(df['CLOSE'])
        return df[[DATE, CLOSE_PRICE]].set_index(DATE)


def index(start=None):
    """
    Возвращает котировки индекса полной доходности с учетом российских налогов
    начиная с даты start_date

    Если дата None, то загружается вся доступная история котировок

    Parameters
    ----------
    start : datetime.date or None
        Начальная дата котировок

    Returns
    -------
    pandas.Series
        В строках даты торгов
        В столбцах цена закрытия индекса полной доходности
    """
    return pd.concat(Index(start))[CLOSE_PRICE]


if __name__ == '__main__':
    z = index(start=pd.to_datetime('2017-10-02'))
    print(z.head())
    print(z.tail())
