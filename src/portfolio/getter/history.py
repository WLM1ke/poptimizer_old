"""Load and update local data for daily quotes history and returns pandas DataFrames.



   1. Load and update local data for single ticker and all its aliases daily price and volumes:

        get_quotes_history(ticker)

   2. Load and update local data for list of tickers daily price or volumes:

        get_prices_history(tickers)
        get_volumes_history(tickers)
"""

from os import path

import arrow
import pandas as pd

from portfolio import download
from portfolio import settings
from portfolio.getter import security_info

QUOTES_PATH = 'quotes'
MARKET_TIME_ZONE = 'Europe/Moscow'
# Реально торги заканчиваются в 19.00, но данные транслируются с задержкой в 15 минут
END_OF_CURRENT_TRADING_DAY = arrow.get().to(MARKET_TIME_ZONE).replace(hour=19,
                                                                      minute=15,
                                                                      second=0,
                                                                      microsecond=0)


def quotes_path(ticker: str):
    """Возвращает и при необходимости создает путь к файлу с котировками."""
    return settings.make_data_path(QUOTES_PATH, f'{ticker}.csv')


def end_of_last_trading_day():
    """Возвращает дату последнего завершившегося торгового дня."""
    if arrow.get().to(MARKET_TIME_ZONE) > END_OF_CURRENT_TRADING_DAY:
        return END_OF_CURRENT_TRADING_DAY
    return END_OF_CURRENT_TRADING_DAY.shift(days=-1)


def load_quotes_history(ticker: str) -> pd.DataFrame:
    converters = dict(TRADEDATE=pd.to_datetime, CLOSE=pd.to_numeric, VOLUME=pd.to_numeric)
    # Значение sep гарантирует загрузку данных с добавленными PyCharm пробелами
    df = pd.read_csv(quotes_path(ticker), converters=converters, header=0, engine='python', sep='\s*,')
    return df.set_index('TRADEDATE')


def need_update(ticker):
    file_date = arrow.get(path.getmtime(quotes_path(ticker))).to(MARKET_TIME_ZONE)
    # Если файл обновлялся после завершения последнего торгового дня, то он не должен обновляться
    if file_date > end_of_last_trading_day():
        return False
    return True


def df_last_date(df):
    return df.index[-1]


def validate_last_date(ticker, df_old: pd.DataFrame, df_new: pd.DataFrame):
    last_date = df_last_date(df_old)
    df_old_last = df_old.loc[last_date]
    df_new_last = df_new.loc[last_date]
    if any([df_old_last['CLOSE'] != df_new_last['CLOSE'], df_old_last['VOLUME'] != df_new_last['VOLUME']]):
        raise ValueError(f'Загруженные данные {ticker} не стыкуются с локальными. \n' +
                         f'{df_old_last} \n' +
                         f'{df_new_last}')


def save_quotes_history(ticker: str, df: pd.DataFrame):
    df.to_csv(quotes_path(ticker))


def update_quotes_history(ticker: str):
    df = load_quotes_history(ticker)
    if need_update(ticker):
        df_update = download.quotes_history(ticker, df_last_date(df))
        validate_last_date(ticker, df, df_update)
        df = pd.concat([df, df_update.iloc[1:]])
        save_quotes_history(ticker, df)
    return df


def yield_aliases_quotes_history(ticker: str):
    aliases_series = security_info.get_aliases_tickers([ticker])
    aliases = aliases_series.loc[ticker].split(sep=' ')
    for ticker in aliases:
        yield download.quotes_history(ticker)


def create_quotes_history(ticker: str):
    aliases = yield_aliases_quotes_history(ticker)
    df = pd.concat(aliases)
    # Для каждой даты выбирается тикер с максимальным оборотом
    df = df.loc[df.groupby('TRADEDATE')['VOLUME'].idxmax()]
    df.sort_index(inplace=True)
    save_quotes_history(ticker, df)
    return df


def get_quotes_history(ticker: str):
    """
    Возвращает данные по котровкам из локальной версии данных при необходимости обновляя их.

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
    if quotes_path(ticker).exists():
        df = update_quotes_history(ticker)
    else:
        df = create_quotes_history(ticker)
    return df


def get_prices_history(tickers: list) -> pd.DataFrame:
    """
    Возвращает историю цен по набору тикеров.

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
    Возвращает историю объеиов торгов по набору тикеров.

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


if __name__ == '__main__':
    print(get_quotes_history('MTSS'))
