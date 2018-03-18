"""Load and update local securities info data.

    1. Load and update local securities info data:

        get_security_info(tickers)

    2. Load and update local last prices data:

        get_last_prices(tickers)

    3. Load aliases for tickers and update local securities info data.

        get_aliases_tickers(tickers)

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
    # Add ALIASES empty column
    columns = ['ALIASES', 'SHORTNAME', 'REGNUMBER', 'LOTSIZE', 'LAST']
    return df.reindex(columns=columns)


def save_security_info(df: pd.DataFrame):
    df.sort_index().to_csv(securities_info_path())


def validate(df, df_update):
    common_tickers = list(set(df.index) & set(df_update.index))
    columns_for_validation = ['SHORTNAME', 'REGNUMBER', 'LOTSIZE']
    df = df.loc[common_tickers, columns_for_validation]
    df_update = df_update.loc[common_tickers, columns_for_validation]
    if not df.equals(df_update):
        raise ValueError(f'Загруженные данные {common_tickers} не стыкуются с локальными. \n' +
                         f'{df} \n' +
                         f'{df_update}')


def fill_aliases_column(df):
    for ticker in df.index:
        if pd.isna(df.loc[ticker, 'ALIASES']):
            tickers = download.reg_number_tickers(reg_number=df.loc[ticker, 'REGNUMBER'])
            df.loc[ticker, 'ALIASES'] = tickers


def update_local_securities_info(tickers) -> pd.DataFrame:
    df = load_securities_info()
    df_update = download_securities_info(tickers)
    validate(df, df_update)
    not_updated_tickers = list(set(df.index) - set(df_update.index))
    df = pd.concat([df.loc[not_updated_tickers], df_update])
    fill_aliases_column(df)
    save_security_info(df)
    return df.loc[tickers]


def create_local_security_info(tickers):
    df = download_securities_info(tickers)
    fill_aliases_column(df)
    save_security_info(df)
    return df


def get_security_info(tickers: list) -> pd.DataFrame:
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
        которые соответсвуют такому же регистрационному номеру (обычно устаревшие ранее использовавшиеся тикеры).
    """
    # Общий запрос содержит последние цены, которые регулярно обновляются, поэтому требует обновления
    if securities_info_path().exists():
        df = update_local_securities_info(tickers)
    else:
        df = create_local_security_info(tickers)
    return df


def get_aliases_tickers(tickers: list) -> pd.Series:
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
    if securities_info_path().exists():
        df = load_securities_info()
        # Если тикеры в локальной версии, то обновлять данные нет необходимости
        if not set(df.index).issuperset(tickers):
            df = update_local_securities_info(tickers)
    else:
        df = create_local_security_info(tickers)
    return df.loc[tickers, 'ALIASES']


def get_last_prices(tickers: list) -> pd.Series:
    """
    Возвращает последние цены для тикеров из списка и обновляет локальные данные.

    Parameters
    ----------
    tickers
        Список тикеров.

    Returns
    -------
    pandas.Series
        В строках тикеры и поледние цены для них.
    """
    # Цены обновляются постоянно - поэтому можно вызывать функцию, требующую обновления данных
    df = get_security_info(tickers)
    return df.loc[tickers, 'LAST']


if __name__ == '__main__':
    print(get_security_info(['KBTK', 'MOEX', 'MTSS', 'SNGSP', 'GAZP', 'PHOR']), '\n')
    print(get_aliases_tickers(['MOEX', 'UPRO']))
