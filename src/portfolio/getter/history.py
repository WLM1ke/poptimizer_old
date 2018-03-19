"""Load and update local data for daily quotes history and returns pandas DataFrames.



   1. Load and update local data for single ticker and all its aliases daily prices and volumes:

        get_quotes_history(ticker)

   2. Load and update local data for list of tickers daily prices or volumes:

        get_prices_history(tickers)
        get_volumes_history(tickers)
"""

from datetime import date
from os import path
from pathlib import Path
from typing import Generator

import arrow
import pandas as pd

from portfolio import download
from portfolio import settings
from portfolio.getter import security_info

MARKET_TIME_ZONE = 'Europe/Moscow'
# Реально торги заканчиваются в 19.00, но данные транслируются с задержкой в 15 минут
END_OF_CURRENT_TRADING_DAY = arrow.get().to(MARKET_TIME_ZONE).replace(hour=19,
                                                                      minute=15,
                                                                      second=0,
                                                                      microsecond=0)


def end_of_last_trading_day() -> arrow:
    """Возвращает дату последнего завершившегося торгового дня."""
    if arrow.get().to(MARKET_TIME_ZONE) > END_OF_CURRENT_TRADING_DAY:
        return END_OF_CURRENT_TRADING_DAY
    return END_OF_CURRENT_TRADING_DAY.shift(days=-1)


class Quotes:
    """Реализует хранение, обновление и хранение локальных данных по котировкам тикеров."""
    _data_folder = 'quotes'
    _columns_for_validation = ['CLOSE', 'VOLUME']

    def __init__(self, ticker: str):
        self.ticker = ticker
        if self.quotes_path.exists():
            self._df = self.update_quotes_history()
        else:
            self._df = self.create_quotes_history()

    def __call__(self) -> pd.DataFrame:
        return self._df

    @property
    def quotes_path(self) -> Path:
        """Возвращает и при необходимости создает путь к файлу с котировками."""
        return settings.make_data_path(self._data_folder, f'{self.ticker}.csv')

    def load_quotes_history(self) -> pd.DataFrame:
        """Загружает историю котировок из локальных данных."""
        converters = dict(TRADEDATE=pd.to_datetime, CLOSE=pd.to_numeric, VOLUME=pd.to_numeric)
        # Значение sep гарантирует загрузку данных с добавленными PyCharm пробелами
        df = pd.read_csv(self.quotes_path, converters=converters, header=0, engine='python', sep='\s*,')
        self._df = df.set_index('TRADEDATE')
        return self._df

    def need_update(self) -> bool:
        """Проверяет по дате изменения файла и времени окончания торгов, нужно ли обновлять локальные данные."""
        file_date = arrow.get(path.getmtime(self.quotes_path)).to(MARKET_TIME_ZONE)
        # Если файл обновлялся после завершения последнего торгового дня, то он не должен обновляться
        if file_date > end_of_last_trading_day():
            return False
        return True

    @property
    def df_last_date(self) -> date:
        """Возвращает последнюю дату в DataFrame."""
        return self._df.index[-1]

    def _validate_last_date(self, df_new: pd.DataFrame) -> None:
        """Проверяет совпадение данных на стыке, то есть для последней даты старого DataFrame."""
        last_date = self.df_last_date
        df_old_last = self._df.loc[last_date]
        df_new_last = df_new.loc[last_date]
        if any([df_old_last[column] != df_new_last[column] for column in self._columns_for_validation]):
            raise ValueError(f'Загруженные данные {self.ticker} не стыкуются с локальными. \n' +
                             f'{df_old_last} \n' +
                             f'{df_new_last}')

    def _save_quotes_history(self) -> None:
        """Сохраняет локальную версию данных в csv-файл с именем тикера."""
        self._df.to_csv(self.quotes_path)

    def update_quotes_history(self) -> pd.DataFrame:
        """Обновляет локальные данные данными из интернета и возвращает полную историю котировок и объемов."""
        df = self.load_quotes_history()
        if self.need_update():
            df_update = download.quotes_history(self.ticker, self.df_last_date)
            self._validate_last_date(df_update)
            self._df = pd.concat([df, df_update.iloc[1:]])
            self._save_quotes_history()
        return self._df

    def _yield_aliases_quotes_history(self) -> Generator[pd.DataFrame, None, None]:
        """Генерирует истории котировок для все тикеров аналогов заданного тикера."""
        aliases_series = security_info.get_aliases_tickers([self.ticker])
        aliases = aliases_series.loc[self.ticker].split(sep=' ')
        for ticker in aliases:
            yield download.quotes_history(ticker)

    def create_quotes_history(self) -> pd.DataFrame:
        """Формирует, сохраняет локальную версию и возвращает склеенную из всех тикеров аналогов историю котировок."""
        aliases = self._yield_aliases_quotes_history()
        df = pd.concat(aliases)
        # Для каждой даты выбирается тикер с максимальным оборотом
        df = df.loc[df.groupby('TRADEDATE')['VOLUME'].idxmax()]
        self._df = df.sort_index()
        self._save_quotes_history()
        return self._df


class Index(Quotes):
    """Реализует хранение, обновление и хранение локальных данных по индексу MCFTRR."""
    _data_folder = None
    _columns_for_validation = ['CLOSE']

    def __init__(self) -> None:
        super(Index, self).__init__('MCFTRR')

    def update_quotes_history(self) -> pd.DataFrame:
        """Обновляет локальные данные данными из интернета и возвращает полную историю котировок индекса."""
        df = self.load_quotes_history()
        if self.need_update():
            df_update = download.index_history(self.df_last_date)
            self._validate_last_date(df_update)
            self._df = pd.concat([df, df_update.iloc[1:]])
            self._save_quotes_history()
        return self._df

    def create_quotes_history(self) -> pd.DataFrame:
        """Формирует, сохраняет локальную версию историю котировок индекса."""
        self._df = download.index_history()
        self._save_quotes_history()
        return self._df


def get_quotes_history(ticker: str):
    """
    Возвращает данные по котровкам из локальной версии данных, при необходимости обновляя их.

    При первоночальном формировании данных используются все алиасы тикера для его регистрационного номера, чтобы
    выгрузить максимально длинную историю котировок. При последующих обновлениях используется только текущий тикер.

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
    df = Quotes(ticker)
    return df()


def get_prices_history(tickers: list) -> pd.DataFrame:
    """
    Возвращает историю цен закрытия по набору тикеров из локальных данных, при необходимости обновляя их.

    Parameters
    ----------
    tickers: list of str
        Список тикеров.

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов.
        В столбцах цены закрытия для тикеров.
    """
    df = pd.concat([get_quotes_history(ticker)['CLOSE'] for ticker in tickers], axis=1)
    df.columns = tickers
    return df


def get_volumes_history(tickers: list) -> pd.DataFrame:
    """
    Возвращает историю объемов торгов по набору тикеров из локальных данных, при необходимости обновляя их.

    Parameters
    ----------
    tickers: list of str
        Список тикеров.

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов.
        В столбцах объемы торгов для тикеров.
    """
    df = pd.concat([get_quotes_history(ticker)['VOLUME'] for ticker in tickers], axis=1)
    df.columns = tickers
    return df


def get_index_history() -> pd.DataFrame:
    """
    Возвращает историю индекса полной доходности с учетом российских налогов из локальных данных.

    При необходимости локальные данные обновляются для ускорения последующих загрузок.

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов.
        В столбце цена закрытия индекса.
    """
    df = Index()
    return df()


if __name__ == '__main__':
    print(get_index_history())
