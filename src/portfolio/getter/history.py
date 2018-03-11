"""Load and update local data of daily quotes history and returns pandas DataFrames."""

import pandas as pd

from portfolio import download
from portfolio import settings

QUOTES_PATH = 'quotes'


def quotes_path(ticker: str):
    """Возвращает и при необходимости создает путь к файлу с котировками."""
    return settings.make_data_path(QUOTES_PATH, f'{ticker}.csv')


def load_quotes_history(ticker: str):
    df = pd.read_csv(quotes_path(ticker), header=0)
    df['TRADEDATE'] = pd.to_datetime(df['TRADEDATE'])
    df['CLOSE'] = pd.to_numeric(df['CLOSE'])
    df['VOLUME'] = pd.to_numeric(df['VOLUME'])
    return df.set_index('TRADEDATE')


def validate(df_old: pd.DataFrame, df_new: pd.DataFrame):
    if not (df_old.iloc[-1] == df_new.iloc[0]).all(skipna=False):
        print(df_old.iloc[-1])
        print(df_new.iloc[0])
        raise ValueError('Загруженные данные не стыкуются с локальными.')


def save_quotes_history(ticker: str, df: pd.DataFrame):
    df.to_csv(quotes_path(ticker))


def update_quotes_history(ticker: str):
    df_old = load_quotes_history(ticker)
    # TODO: проверка на время обновление файла
    df_new = download.quotes_history(ticker, df_old.index[-1])
    validate(df_old, df_new)
    df = pd.concat([df_old, df_new.iloc[1:]])
    return df


def get_quotes_history(ticker: str):
    if quotes_path(ticker).exists():
        df = update_quotes_history(ticker)
    else:
        df = download.quotes_history_from_start(ticker)
    save_quotes_history(ticker, df)
    return df


if __name__ == '__main__':
    print(get_quotes_history('AKRN'))
