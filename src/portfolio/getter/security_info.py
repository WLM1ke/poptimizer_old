"""Load and update local securities info data."""

import pandas as pd

from portfolio import download
from portfolio import settings

DATA_FILE = 'securities_info.csv'


def securities_info_path():
    return settings.make_data_path(None, DATA_FILE)


def load_securities_info() -> pd.DataFrame:
    # TODO: add , ALIASES=pd.to_numeric
    converters = dict(LOTSIZE=pd.to_numeric, LAST=pd.to_numeric)
    # Значение sep гарантирует загрузку данных с добавленными PyCharm пробелами
    df = pd.read_csv(securities_info_path(), converters=converters, header=0, engine='python', sep='\s*,')
    return df.set_index('SECID')


def validate(df, df_update):
    common_tickers = list(set(df.index) & set(df_update.index))
    # TODO: add , 'ALIASES'
    df = df.loc[common_tickers, ['SHORTNAME', 'REGNUMBER', 'LOTSIZE']]
    df_update = df_update.loc[common_tickers, ['SHORTNAME', 'REGNUMBER', 'LOTSIZE']]
    if not df.equals(df_update):
        raise ValueError(f'Загруженные данные {common_tickers} не стыкуются с локальными. \n' +
                         f'{df} \n' +
                         f'{df_update}')


def update_securities_info(tickers) -> pd.DataFrame:
    df = load_securities_info()
    df_update = download.securities_info(tickers)
    validate(df, df_update)
    not_updated_tickers = list(set(df.index) - set(df_update.index))
    df = pd.concat([df.loc[not_updated_tickers], df_update]).sort_index()
    save_security_info(df)
    return df


def save_security_info(df: pd.DataFrame):
    df.to_csv(securities_info_path())


def get_security_info(tickers: list):
    """
    Возвращает данные по тикерам из списка

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
        df = update_securities_info(tickers)
    else:
        df = download.securities_info(tickers)
        save_security_info(df)
    return df


if __name__ == '__main__':
    print(get_security_info(['KBTK', 'MOEX']))
