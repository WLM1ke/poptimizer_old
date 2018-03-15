"""Load and update local securities info data."""

import numpy as np
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


def update_local_securities_info(tickers) -> pd.DataFrame:
    df = load_securities_info()
    df_update = download_securities_info(tickers)
    validate(df, df_update)
    not_updated_tickers = list(set(df.index) - set(df_update.index))
    df = pd.concat([df.loc[not_updated_tickers], df_update])
    save_security_info(df)
    return df.loc[tickers]


def create_local_security_info(tickers):
    df = download_securities_info(tickers)
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
    return df.loc[tickers, ['LOTSIZE']].transpose()


def get_last_prices(tickers: list):
    """
    Возвращает последние цены для тикеров из списка и обновляет локальные данные

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
    return df.loc[tickers, ['LAST']].transpose()


def get_tickers(ticker: str) -> str:
    # TODO: Проверка на наличие локальной версии
    # TODO: Нависать док
    info = load_securities_info()
    if (ticker in info.index) and not np.isnan(info.loc[ticker, 'TICKERS']):
        # если тикер и информация по долнительным тикерам есть, то берем ее из локальной версии
        tickers = info.loc[ticker, 'TICKERS']
    elif ticker in info.index:
        # если тикер присутсувет, но информации по долнительным тикерам нет,
        # то загружаем информацию и сохраняем локально
        tickers = download.tickers(ticker)
        info.loc[ticker, 'TICKERS'] = tickers
        save_security_info(info)
    else:
        # Если тикера нет в локальной версии, то загружаем информацию,
        # загружаем и добовляем информацию по дополнительным тикерам, объединяем с текущей информацией и сохраняем
        info_update = download_securities_info([ticker])
        tickers = download.tickers(ticker)
        info_update.loc[ticker, 'TICKERS'] = tickers
        info = pd.concat([info, info_update])
        save_security_info(info)
    return tickers


if __name__ == '__main__':
    # print(get_security_info(['KBTK', 'MOEX', 'MTSS', 'SNGSP', 'GAZP']))
    print(get_tickers('KBTK'))
