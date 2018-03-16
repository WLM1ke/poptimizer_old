"""Load and update local securities info data.

    1. Load and update local securities info data:

        get_security_info(tickers)

    2. Load and update local lots size data:

        get_lots_size(tickers)

    3. Load and update local last prices data:

        get_last_prices(tickers)

    4. Load aliases for ticker and update local securities info data.

        get_tickers(ticker)

"""

import pandas as pd

from portfolio import download
from portfolio import settings

DATA_FILE = 'securities_info.csv'


def securities_info_path():
    return settings.make_data_path(None, DATA_FILE)


def load_securities_info() -> pd.DataFrame:
    converters = dict(LOTSIZE=pd.to_numeric, LAST=pd.to_numeric)
    # Значение sep гарантирует загрузку данных с добавленными PyCharm пробелами
    df = pd.read_csv(securities_info_path(), converters=converters, header=0, engine='python', sep='\s*,')
    return df.set_index('SECID')


def download_securities_info(tickers) -> pd.DataFrame:
    df = download.securities_info(tickers)
    # add ALIASES empty column
    columns = ['SHORTNAME', 'REGNUMBER', 'TICKERS', 'LOTSIZE', 'LAST']
    return df.reindex(columns=columns)


def save_security_info(df: pd.DataFrame):
    df.sort_index().to_csv(securities_info_path())


def validate(df, df_update):
    common_tickers = list(set(df.index) & set(df_update.index))
    df = df.loc[common_tickers, ['SHORTNAME', 'REGNUMBER', 'LOTSIZE']]
    df_update = df_update.loc[common_tickers, ['SHORTNAME', 'REGNUMBER', 'LOTSIZE']]
    if not df.equals(df_update):
        raise ValueError(f'Загруженные данные {common_tickers} не стыкуются с локальными. \n' +
                         f'{df} \n' +
                         f'{df_update}')


def fill_tickers_column(df):
    for ticker in df.index:
        if pd.isna(df.loc[ticker, 'TICKERS']):
            tickers = download.tickers(reg_number=df.loc[ticker, 'REGNUMBER'])
            df.loc[ticker, 'TICKERS'] = tickers


def update_local_securities_info(tickers) -> pd.DataFrame:
    df = load_securities_info()
    df_update = download_securities_info(tickers)
    validate(df, df_update)
    not_updated_tickers = list(set(df.index) - set(df_update.index))
    df = pd.concat([df.loc[not_updated_tickers], df_update])
    fill_tickers_column(df)
    save_security_info(df)
    return df.loc[tickers]


def create_local_security_info(tickers):
    df = download_securities_info(tickers)
    fill_tickers_column(df)
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
        которые соответсвуют такому же регистрационному номеру (обычно устаревшие ранеиспользовавшиеся тикеры).
    """
    # Общий запрос содержит последние цены, которые регулярно обновляются, поэтому требует обновления
    if securities_info_path().exists():
        df = update_local_securities_info(tickers)
    else:
        df = create_local_security_info(tickers)
    return df


def get_lots_size(tickers: list):
    """
    Возвращает размеры лотов для тикеров из списка и при необходимости обновляет локальные данные

    Parameters
    ----------
    tickers
        Список тикеров.

    Returns
    -------
    pandas.DataFrame
        В столбцах тикеры.
        В строке размеры лотов.
    """
    if securities_info_path().exists():
        df = load_securities_info()
        # Если все тикеры в локальной версии, то обновлять данные нет необходимости
        if not set(df.index).issuperset(tickers):
            df = update_local_securities_info(tickers)
    else:
        df = create_local_security_info(tickers)
    return df.loc[tickers, 'LOTSIZE']


def get_last_prices(tickers: list):
    """
    Возвращает последние цены для тикеров из списка и обновляет локальные данные.

    Parameters
    ----------
    tickers
        Список тикеров.

    Returns
    -------
    pandas.DataFrame
        В столбцах тикеры.
        В строке последние цены.
    """
    # Цены обновляются пстоянно
    df = get_security_info(tickers)
    return df.loc[tickers, 'LAST']


def get_tickers(ticker: str) -> list:
    """
    Возвращает список тикеров аналогов для заданного тикера.

    Parameters
    ----------
    ticker
        Тикер.

    Returns
    -------
    list
        Список тикеров аналогов заданного тикера, включая его самого.
    """
    if securities_info_path().exists():
        df = load_securities_info()
        # Если тикер в локальной версии, то обновлять данные нет необходимости
        if ticker not in df.index:
            df = update_local_securities_info([ticker])
    else:
        df = create_local_security_info([ticker])
    return df.loc[ticker, 'TICKERS'].split(sep=' ')


if __name__ == '__main__':
    print(get_security_info(['KBTK', 'MOEX', 'MTSS', 'SNGSP', 'GAZP', 'PHOR']))
    print(get_tickers('UPRO'))
    print(get_lots_size(['KBTK', 'MOEX', 'MTSS', 'SNGSP', 'GAZP', 'PHOR']))
