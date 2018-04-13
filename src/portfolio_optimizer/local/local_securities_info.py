"""Load and update local securities info data.

    1. Load and update local securities info data:

        get_security_info(tickers)

    2. Load and update local last prices data:

        last_price(tickers)

    3. Load aliases for tickers and update local securities info data.

        aliases(tickers)
"""

import numpy as np
import pandas as pd

from portfolio_optimizer import web
from portfolio_optimizer.local import storage_old
from portfolio_optimizer.settings import LAST_PRICE, LOT_SIZE, COMPANY_NAME, REG_NUMBER, TICKER, TICKER_ALIASES

DATA_PATH = storage_old.make_data_path('securities_info', 'securities_info.csv')


def load_securities_info():
    """загружает локальную версию данных - sep гарантирует загрузку данных с добавленными PyCharm пробелами."""
    converters = {LOT_SIZE: pd.to_numeric, LAST_PRICE: pd.to_numeric}
    df = pd.read_csv(DATA_PATH, converters=converters, header=0, engine='python', sep='\s*,')
    return df.set_index(TICKER)


def download_securities_info(tickers):
    """Загружает информацию о тикерах из интернета и добавляет колонку пустую колонку ALIASES."""
    df = web.securities_info(tickers)
    columns = [TICKER_ALIASES, COMPANY_NAME, REG_NUMBER, LOT_SIZE, LAST_PRICE]
    return df.reindex(columns=columns)


def save_security_info(df: pd.DataFrame):
    """Сохраняет фрейм с данными в директорию с данными."""
    df.sort_index().to_csv(DATA_PATH)


def validate(df, df_update):
    """Проверяет совпадение данных для общих тикеров.

    Проверка осуществляется для колонок с кратким наименованием, регистрационным номером и размером лота."""
    common_tickers = list(set(df.index) & set(df_update.index))
    if common_tickers:
        columns_for_validation = [REG_NUMBER, LOT_SIZE]
        df = df.loc[common_tickers]
        df_update = df_update.loc[common_tickers]
        equal = df[REG_NUMBER].equals(df_update[REG_NUMBER]) and np.allclose(df[LOT_SIZE], df_update[LOT_SIZE])
        if not equal:
            raise ValueError(f'Загруженные данные {common_tickers} не стыкуются с локальными. \n' +
                             f'{df[columns_for_validation]} \n' +
                             f'{df_update[columns_for_validation]}')


def fill_aliases_column(df):
    """Заполняет пустые ячейки в колонке с тикерами аналогами."""
    for ticker in df.index:
        if pd.isna(df.loc[ticker, TICKER_ALIASES]):
            tickers = web.reg_number_tickers(reg_number=df.loc[ticker, REG_NUMBER])
            df.loc[ticker, TICKER_ALIASES] = ' '.join(tickers)


def update_local_securities_info(tickers):
    """Обновляет существующую локальную версию данных и проверяет соответствие новых данных старым."""
    df = load_securities_info()
    df_update = download_securities_info(tickers)
    validate(df, df_update)
    all_tickers = list(set(df_update.index) | set(df.index))
    df = df.reindex(index=all_tickers)
    df.loc[tickers, df_update.columns] = df_update
    fill_aliases_column(df)
    save_security_info(df)
    return df.loc[tickers]


def create_local_security_info(tickers):
    """Создает с нуля локальную версию данных, загружая их из интернета."""
    df = download_securities_info(tickers)
    fill_aliases_column(df)
    save_security_info(df)
    return df


def get_security_info(tickers: list):
    """
    Возвращает данные по тикерам из списка и при необходимости обновляет локальные данные

    Parameters
    ----------
    tickers
        Список тикеров.

    Returns
    -------
    pandas.DataFrame
        В строках тикеры.
        В столбцах данные по размеру лота, регистрационному номеру, краткому наименованию, последней цене и тикерам,
        которые соответствуют такому же регистрационному номеру (обычно устаревшие ранее использовавшиеся тикеры).
    """
    # Общий запрос содержит последние цены, которые регулярно обновляются, поэтому требует обновления
    if DATA_PATH.exists():
        df = update_local_securities_info(tickers)
    else:
        df = create_local_security_info(tickers)
    return df


def aliases(tickers: tuple):
    """
    Возвращает список тикеров аналогов для заданного набора тикеров

    Parameters
    ----------
    tickers
        Тикеры

    Returns
    -------
    pd.Series
        В строках тикеры и тикеры аналоги для них.
    """
    if DATA_PATH.exists():
        df = load_securities_info()
        # Если тикеры в локальной версии, то обновлять данные нет необходимости
        if not set(df.index).issuperset(tickers):
            df = update_local_securities_info(tickers)
    else:
        df = create_local_security_info(tickers)
    return df.loc[tickers, TICKER_ALIASES]


def last_price(tickers: tuple):
    """
    Возвращает последние цены для тикеров из кортежа напрямую из интернета

    Parameters
    ----------
    tickers
        Кортеж тикеров

    Returns
    -------
    pandas.Series
        В строках тикеры
    """
    df = web.securities_info(tickers)
    return df.loc[tickers, LAST_PRICE]


if __name__ == '__main__':
    df_get = last_price(('SNGSP', 'SBERP'))
    print(df_get)
