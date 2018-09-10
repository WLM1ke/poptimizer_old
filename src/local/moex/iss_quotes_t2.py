"""Сохранение и обновление локальных данных о котировках в режиме  T+2"""
import functools

import pandas as pd

import local
from utils import data_manager
from web import moex
from web.labels import VOLUME, CLOSE_PRICE, DATE

QUOTES_CATEGORY = 'quotes_t2'


class QuotesT2DataManager(data_manager.AbstractDataManager):
    """Реализует особенность загрузки и хранения истории котировок в режиме T+2"""
    def __init__(self, ticker):
        super().__init__(QUOTES_CATEGORY, ticker)

    def download_all(self):
        """Загружает историю котировок в режиме T+2, склеенную из всех тикеров аналогов

        Если на одну дату приходится несколько результатов торгов, то выбирается с максимальным оборотом
        """
        df = pd.concat(self._yield_aliases_quotes_history())
        return df.loc[df.groupby(DATE)[VOLUME].idxmax()]

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
        return moex.quotes(ticker, last_date)


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


if __name__ == '__main__':
    print(quotes_t2('UPRO'))
