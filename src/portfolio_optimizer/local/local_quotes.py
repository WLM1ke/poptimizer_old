"""Сохраняет, обновляет и загружает локальную версию данных по индексу котировкам"""

import functools

import pandas as pd

from portfolio_optimizer import web, local
from portfolio_optimizer.local.data_manager import DataManager
from portfolio_optimizer.settings import DATE, CLOSE_PRICE, VOLUME, REG_NUMBER

QUOTES_CATEGORY = 'quotes'


class QuotesManager(DataManager):
    """Реализует особенность загрузки 'длинной' истории котировок"""

    def __init__(self, ticker: str):
        web_quotes_function = functools.partial(web.quotes, ticker=ticker)
        super().__init__(QUOTES_CATEGORY, ticker, None, web_quotes_function)

    def create(self):
        """Создает локальную версию истории котировок, склеенную из всех тикеров аналогов"""
        df = pd.concat(self._yield_aliases_quotes_history())
        # Для каждой даты выбирается тикер с максимальным оборотом
        df = df.loc[df.groupby(DATE)[VOLUME].idxmax()]
        df = df.sort_index()
        self.file.dump(df)

    def _yield_aliases_quotes_history(self):
        """Генерирует истории котировок для все тикеров аналогов заданного тикера"""
        ticker = self.frame_name
        reg_number = local.security_info([ticker]).loc[ticker, REG_NUMBER]
        aliases_tickers = web.reg_number_tickers(reg_number)
        for ticker in aliases_tickers:
            yield web.quotes(ticker)


def quotes(ticker: str):
    """
    Возвращает данные по котировкам из локальной версии данных, при необходимости обновляя их

    При первоначальном формировании данных используются все алиасы тикера для его регистрационного номера, чтобы
    выгрузить максимально длинную историю котировок. При последующих обновлениях используется только текущий тикер

    Parameters
    ----------
    ticker
        Тикер для которого необходимо получить данные

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов.
        В столбцах [CLOSE, VOLUME] цена закрытия и оборот в штуках.
    """
    data = QuotesManager(ticker)
    return data.get()


def prices(tickers: tuple):
    """
    Возвращает историю цен закрытия по набору тикеров из локальных данных, при необходимости обновляя их

    Parameters
    ----------
    tickers: tuple of str
        Список тикеров

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов
    """
    df = pd.concat([quotes(ticker)[CLOSE_PRICE] for ticker in tickers], axis=1)
    df.columns = tickers
    return df


def volumes(tickers: tuple):
    """
    Возвращает историю объемов торгов по набору тикеров из локальных данных, при необходимости обновляя их.

    Parameters
    ----------
    tickers: tuple of str
        Список тикеров

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов
    """
    df = pd.concat([quotes(ticker)[VOLUME] for ticker in tickers], axis=1)
    df.columns = tickers
    return df


if __name__ == '__main__':
    print(quotes('SBER'))
