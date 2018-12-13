"""Сохранение и обновление локальных данных о котировках в режиме  T+2"""
import functools

import numpy as np
import pandas as pd
from pandas.tseries import offsets

import local
from local import dividends
from local import moex
from utils import aggregation
from utils import data_manager
from web import moex
from web.labels import CLOSE_PRICE
from web.labels import DATE
from web.labels import TICKER
from web.labels import VOLUME

QUOTES_CATEGORY = 'quotes_t2'

# Количество дней между отсечкой и эксдивидендной датой
T2 = 1


class QuotesT2DataManager(data_manager.AbstractDataManager):
    """Реализует особенность загрузки и хранения истории котировок в режиме T+2"""
    def __init__(self, ticker):
        super().__init__(QUOTES_CATEGORY, ticker)

    def download_all(self):
        """Загружает историю котировок в режиме T+2, склеенную из всех тикеров аналогов

        Если на одну дату приходится несколько результатов торгов, то выбирается с максимальным оборотом
        """
        df = pd.concat(self._yield_aliases_quotes_history()).reset_index()
        df = df.loc[df.groupby(DATE)[VOLUME].idxmax()]
        return df.set_index(DATE)

    def _yield_aliases_quotes_history(self):
        """Генерирует истории котировок для все тикеров аналогов заданного тикера"""
        ticker = self.data_name
        aliases_tickers = local.moex.aliases(ticker)
        for ticker in aliases_tickers:
            yield moex.quotes_t2(ticker)

    def download_update(self):
        """Загружает историю котировок в режиме T+2 начиная с последней имеющейся даты"""
        ticker = self.data_name
        last_date = self.value.index[-1]
        return moex.quotes_t2(ticker, last_date)


@functools.lru_cache(maxsize=None)
def quotes_t2(ticker: str):
    """Возвращает данные по котировкам в режиме T+2 из локальной версии данных, при необходимости обновляя их

    Parameters
    ----------
    ticker
        Тикер для которого необходимо получить данные

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов
        В столбцах [CLOSE, VOLUME] цена закрытия и оборот в штуках
    """
    data = QuotesT2DataManager(ticker)
    return data.value


@functools.lru_cache(maxsize=1)
def prices_t2(tickers: tuple):
    """Возвращает историю цен закрытия в режиме T+2 по набору тикеров из локальных данных, при необходимости обновляя их

    Parameters
    ----------
    tickers: tuple of str
        Список тикеров

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов
    """
    df = pd.concat([quotes_t2(ticker)[CLOSE_PRICE] for ticker in tickers], axis=1)
    df.columns = tickers
    df.columns.name = TICKER
    return df


@functools.lru_cache(maxsize=1)
def volumes_t2(tickers: tuple):
    """Возвращает историю объемов торгов в режиме T+2 для тикеров из локальных данных, при необходимости обновляя их

    Parameters
    ----------
    tickers: tuple of str
        Список тикеров

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов
    """
    df = pd.concat([quotes_t2(ticker)[VOLUME] for ticker in tickers], axis=1)
    df.columns = tickers
    return df


def t2_shift(date, index):
    """Рассчитывает эксдивидендную дату для режима T-2 на основании даты закрытия реестра

    Если дата не содержится индексе цен, то необходимо найти предыдущую из индекса цен. После этого взять
    сдвинутую на 1 назад дату. Если дата находится в будущем за пределом истории котировок, то достаточно
    сдвинуть на 1 бизнес дня назад - упрощенный подход, который может не корректно работать из-за праздников
    """
    if date <= index[-1]:
        position = index.get_loc(date, 'ffill')
        return index[position - T2]
    # Выходной гарантированно заменяем бизнес днем
    next_b_day = date + offsets.BDay()
    return next_b_day - (T2 + 1) * offsets.BDay()


def log_returns_with_div(tickers: tuple, last_date: pd.Timestamp):
    """Ряды логарифмов месячных доходностей с учетом дивидендов для набора тикеров до указанной даты

    Parameters
    ----------
    tickers
        Кортеж тикеров
    last_date
        Последняя дата

    Returns
    -------
    pd.DataFrame
        Столбцы - тикеры
        Строки - логарифмы месячных доходностей с учетом дивидендов
    """
    prices = prices_t2(tickers).fillna(method='ffill', axis='index')
    monthly_prices = prices.groupby(by=aggregation.monthly_aggregation_func(last_date)).last()
    monthly_prices = monthly_prices.loc[:last_date]
    div = dividends.dividends(tickers).loc[monthly_prices.index[0]:, :]
    div.index = div.index.map(functools.partial(t2_shift, index=prices.index))
    monthly_dividends = div.groupby(by=aggregation.monthly_aggregation_func(last_date)).sum()
    # В некоторые месяцы не платятся дивиденды - без этого буду NaN при расчете доходностей
    monthly_dividends = monthly_dividends.reindex(index=monthly_prices.index, fill_value=0)
    returns = (monthly_prices + monthly_dividends) / monthly_prices.shift(1)
    return returns.apply(np.log)


if __name__ == '__main__':
    print(prices_t2(("KRSBP",)))
