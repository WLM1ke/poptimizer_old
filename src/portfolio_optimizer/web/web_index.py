"""Загружает котировки индекса полной доходности с учетом российских налогов с http://iss.moex.com"""

import datetime

import pandas as pd

from portfolio_optimizer.settings import DATE, CLOSE_PRICE
from portfolio_optimizer.web.web_quotes import Quotes


class Index(Quotes):
    """Представление ответа сервера - данные по индексу полной доходности MOEX"""
    base = 'http://iss.moex.com/iss/history/engines/stock/markets/index/boards/RTSI/securities'
    ticker = 'MCFTRR'

    def __init__(self, start_date):
        super().__init__(self.ticker, start_date)

    @property
    def dataframe(self):
        """Выбирает из сырого DataFrame только с необходимые колонки - даты и цены закрытия"""
        df = self.df
        df[DATE] = pd.to_datetime(df['TRADEDATE'])
        df[CLOSE_PRICE] = pd.to_numeric(df['CLOSE'])
        return df[[DATE, CLOSE_PRICE]].set_index(DATE)


def index(start_date=None):
    """
    Возвращает котировки индекса полной доходности с учетом российских налогов
    начиная с даты start_date

    Если дата None, то загружается вся доступная история котировок

    Parameters
    ----------
    start_date : datetime.date or None
        Начальная дата котировок

    Returns
    -------
    pandas.Series
        В строках даты торгов
        В столбцах цена закрытия индекса полной доходности
    """
    return pd.concat(Index(start_date))[CLOSE_PRICE]


if __name__ == '__main__':
    z = index(start_date=datetime.date(2017, 10, 2))
    print(z.head())
    print(z.tail())
