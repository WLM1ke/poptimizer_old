"""Load and update local securities info data.

    1. Load and update local securities info data:

        get_security_info(tickers)

    2. Load and update local last prices data:

        get_last_prices(tickers)

    3. Load aliases for tickers and update local securities info data.

        get_aliases_tickers(tickers)
"""

import pandas as pd

import optimizer.getter.storage
from optimizer import download
from optimizer.settings import LAST_PRICE, LOT_SIZE, COMPANY_NAME, REG_NUMBER, TICKER, TICKER_ALIASES

DATA_PATH = optimizer.getter.storage.make_data_path('securities_info', 'securities_info.csv')


def load_securities_info():
    """загружает локальную версию данных - sep гарантирует загрузку данных с добавленными PyCharm пробелами."""
    converters = {LOT_SIZE: pd.to_numeric, LAST_PRICE: pd.to_numeric}
    df = pd.read_csv(DATA_PATH, converters=converters, header=0, engine='python', sep='\s*,')
    return df.set_index(TICKER)


def download_securities_info(tickers):
    """Загружает информацию о тикерах из интернета и добавляет колонку пустую колонку ALIASES."""
    df = download.securities_info(tickers)
    columns = [TICKER_ALIASES, COMPANY_NAME, REG_NUMBER, LOT_SIZE, LAST_PRICE]
    return df.reindex(columns=columns)


def save_security_info(df: pd.DataFrame):
    """Сохраняет фрейм с данными в директорию с данными."""
    df.sort_index().to_csv(DATA_PATH)


def validate(df, df_update):
    """Проверяет совпадение данных для общих тикеров.

    Проверка осуществляется для колонок с кратким наименованием, регистрационным номером и размером лота."""
    common_tickers = list(set(df.index) & set(df_update.index))
    columns_for_validation = [REG_NUMBER, LOT_SIZE]
    df = df.loc[common_tickers, columns_for_validation]
    df_update = df_update.loc[common_tickers, columns_for_validation]
    if not df.equals(df_update):
        raise ValueError(f'Загруженные данные {common_tickers} не стыкуются с локальными. \n' +
                         f'{df} \n' +
                         f'{df_update}')


def fill_aliases_column(df):
    """Заполняет пустые ячейки в колонке с тикерами аналогами."""
    for ticker in df.index:
        if pd.isna(df.loc[ticker, TICKER_ALIASES]):
            tickers = download.reg_number_tickers(reg_number=df.loc[ticker, REG_NUMBER])
            df.loc[ticker, TICKER_ALIASES] = tickers


def update_local_securities_info(tickers):
    """Обновляет существующую локальную версию данных и проверяет соответствие новых данных старым."""
    df = load_securities_info()
    df_update = download_securities_info(tickers)
    validate(df, df_update)
    not_updated_tickers = list(set(df.index) - set(df_update.index))
    df = pd.concat([df.loc[not_updated_tickers], df_update])
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


def get_aliases_tickers(tickers: list):
    """
    Возвращает список тикеров аналогов для заданного набора тикеров.

    Parameters
    ----------
    tickers
        Тикеры.

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


def get_last_prices(tickers: list):
    """
    Возвращает последние цены для тикеров из списка и обновляет локальные данные.

    Parameters
    ----------
    tickers
        Список тикеров.

    Returns
    -------
    pandas.Series
        В строках тикеры и последние цены для них.
    """
    # Цены обновляются постоянно - поэтому можно вызывать функцию, требующую обновления данных
    df = get_security_info(tickers)
    return df.loc[tickers, LAST_PRICE]


if __name__ == '__main__':
    df_get = get_security_info(['SNGSP', 'SBERP'])
    print(df_get)
