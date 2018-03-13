"""Load and update local data of daily quotes history and returns pandas DataFrames."""

from os import path

import arrow
import pandas as pd

from portfolio import download
from portfolio import settings

QUOTES_PATH = 'quotes'
MARKET_TIME_ZONE = 'Europe/Moscow'
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
    else:
        return END_OF_CURRENT_TRADING_DAY.shift(days=-1)


def load_quotes_history(ticker: str) -> pd.DataFrame:
    converters = dict(TRADEDATE=pd.to_datetime, CLOSE=pd.to_numeric, VOLUME=pd.to_numeric)
    df = pd.read_csv(quotes_path(ticker), converters=converters, header=0, engine='python', sep='\s*,')
    return df.set_index('TRADEDATE')


def need_update(ticker):
    file_date = arrow.get(path.getmtime(quotes_path(ticker))).to(MARKET_TIME_ZONE)
    # Если файл обновлялся после завершения последнего торгового дня, то он не должен обновляться
    if file_date > end_of_last_trading_day():
        return False
    else:
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


def update_quotes_history(ticker: str):
    df = load_quotes_history(ticker)
    if need_update(ticker):
        df_update = download.quotes_history(ticker, df_last_date(df))
        validate_last_date(ticker, df, df_update)
        df = pd.concat([df, df_update.iloc[1:]])
        save_quotes_history(ticker, df)
    return df


def save_quotes_history(ticker: str, df: pd.DataFrame):
    df.to_csv(quotes_path(ticker))


def get_quotes_history(ticker: str):
    """
    Возвращает данные по котровкам из локальной версии данных при необходимости обновляя их.

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
        df = download.quotes_history_from_start(ticker)
        save_quotes_history(ticker, df)
    return df


def get_prices_history(tickers):
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


def get_volumes_history(tickers):
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
    print(get_prices_history(['KBTK', 'RTKMP']))
