"""Load and update local data for daily quotes history and returns pandas DataFrames.

    1. Load and update local data for single ticker and all its aliases daily prices and volumes:

        get_quotes_history(ticker)

    2. Load and update local data for list of tickers daily prices or volumes:

        get_prices_history(tickers)
        get_volumes_history(tickers)

    3. Load and update local daily data for MOEX Russia Net Total Return (Resident):

        get_index_history()
"""

from os import path

import arrow
import pandas as pd

from optimizer import download
from optimizer.getter import local_securities_info
from optimizer.getter.local_dividends import LocalDividends
from optimizer.settings import DATE, CLOSE_PRICE, VOLUME

MARKET_TIME_ZONE = 'Europe/Moscow'
# Реально торги заканчиваются в 19.00, но данные транслируются с задержкой в 15 минут
END_OF_CURRENT_TRADING_DAY = arrow.get().to(MARKET_TIME_ZONE).replace(hour=19,
                                                                      minute=15,
                                                                      second=0,
                                                                      microsecond=0)
QUOTES_FOLDER = 'quotes'


def end_of_last_trading_day():
    """Возвращает дату последнего завершившегося торгового дня."""
    if arrow.get().to(MARKET_TIME_ZONE) > END_OF_CURRENT_TRADING_DAY:
        return END_OF_CURRENT_TRADING_DAY
    return END_OF_CURRENT_TRADING_DAY.shift(days=-1)


class LocalQuotes(LocalDividends):
    """Реализует хранение, обновление и хранение локальных данных по котировкам тикеров."""
    _data_folder = QUOTES_FOLDER
    _load_converter = {DATE: pd.to_datetime, CLOSE_PRICE: pd.to_numeric, VOLUME: pd.to_numeric}
    _data_columns = [CLOSE_PRICE, VOLUME]

    def need_update(self):
        """Проверяет по дате изменения файла и времени окончания торгов, нужно ли обновлять локальные данные."""
        file_date = arrow.get(path.getmtime(self.local_data_path)).to(MARKET_TIME_ZONE)
        # Если файл обновлялся после завершения последнего торгового дня, то он не должен обновляться
        if file_date > end_of_last_trading_day():
            return False
        return True

    @property
    def df_last_date(self):
        """Возвращает последнюю дату в DataFrame."""
        return self.df.index[-1]

    def _validate_new_data(self, df_new):
        """Проверяет совпадение данных на стыке, то есть для последней даты старого DataFrame."""
        last_date = self.df_last_date
        df_old_last = self.df.loc[last_date]
        df_new_last = df_new.loc[last_date]
        columns_for_validation = [CLOSE_PRICE, VOLUME]
        if any([df_old_last[column] != df_new_last[column] for column in columns_for_validation]):
            raise ValueError(f'Загруженные данные {self.ticker} не стыкуются с локальными. \n' +
                             f'{df_old_last} \n' +
                             f'{df_new_last}')

    def update_local_history(self):
        """Обновляет локальные данные данными из интернета и возвращает полную историю котировок и объемов."""
        self.df = self.load_local_history()
        if self.need_update():
            df_update = download.quotes_history(self.ticker, self.df_last_date)
            self._validate_new_data(df_update)
            self.df = pd.concat([self.df, df_update.iloc[1:]])
            self._save_history()

    def _yield_aliases_quotes_history(self):
        """Генерирует истории котировок для все тикеров аналогов заданного тикера."""
        aliases_series = local_securities_info.get_aliases_tickers([self.ticker])
        aliases = aliases_series.loc[self.ticker].split(sep=' ')
        for ticker in aliases:
            yield download.quotes_history(ticker)

    def create_local_history(self):
        """Формирует, сохраняет локальную версию и возвращает склеенную из всех тикеров аналогов историю котировок."""
        aliases = self._yield_aliases_quotes_history()
        df = pd.concat(aliases)
        # Для каждой даты выбирается тикер с максимальным оборотом
        df = df.loc[df.groupby(DATE)[VOLUME].idxmax()]
        self.df = df.sort_index()
        self._save_history()


def get_quotes_history(ticker: str):
    """
    Возвращает данные по котировкам из локальной версии данных, при необходимости обновляя их.

    При первоначальном формировании данных используются все алиасы тикера для его регистрационного номера, чтобы
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
    return LocalQuotes(ticker).df


def get_prices_history(tickers: list):
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
    df = pd.concat([get_quotes_history(ticker)[CLOSE_PRICE] for ticker in tickers], axis=1)
    df.columns = tickers
    return df


def get_volumes_history(tickers: list):
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
    df = pd.concat([get_quotes_history(ticker)[VOLUME] for ticker in tickers], axis=1)
    df.columns = tickers
    return df


if __name__ == '__main__':
    print(get_prices_history(['MVID', 'PHOR']))
