"""Функции проверки статуса дивидендов"""
import arrow
import numpy as np
import pandas as pd

from local import local_dividends_smart_lab, local_dividends_dohod
from local.local_dividends import DividendsDataManager, STATISTICS_START
from web.labels import TICKER, DIVIDENDS, DATE

DIVIDENDS_SOURCES = [local_dividends_dohod.dividends_dohod,
                     local_dividends_smart_lab.dividends_smart_lab]
DAYS_TO_MANUAL_UPDATE = 90


def smart_lab_status(tickers: tuple):
    """Информация об актуальности данных в основной локальной базе дивидендов

    Parameters
    ----------
    tickers
        Основные тикеры, для которых нужно проверить актуальность данных

    Returns
    -------
    tuple of list
        Нулевой элемент кортежа - список тикеров из переданных без актуальной информации в локальной базе
        Первый элемент кортежа - список тикеров со СмартЛаба, по которым нет актуальной информации в локальной базе
    """
    df = local_dividends_smart_lab.dividends_smart_lab()
    result = ([], [])
    for i in range(len(df)):
        date = df.index[i]
        ticker = df.iloc[i][TICKER]
        value = df.iloc[i][DIVIDENDS]
        local_data = DividendsDataManager(ticker).value
        if (date not in local_data.index) or (local_data[date] != value):
            if ticker in tickers:
                result[0].append(ticker)
            else:
                result[1].append(ticker)
    return result


def need_update(ticker: str):
    """Проверяет необходимость обновления данных

    Обновление нужно:
    при наличии новых данных в локальной версии web источника
    по прошествии времени (дивиденды не выплачиваются чаще чем раз в квартал)
    """
    manager = DividendsDataManager(ticker)
    last_update = manager.last_update
    if last_update.shift(days=DAYS_TO_MANUAL_UPDATE) < arrow.now():
        return f'Последнее обновление более {DAYS_TO_MANUAL_UPDATE} дней назад'
    for source in DIVIDENDS_SOURCES:
        df = manager.value
        local_web_df = source(manager.data_name).groupby(DATE).sum()
        local_web_df = local_web_df[local_web_df.index >= pd.Timestamp(STATISTICS_START)]
        additional_data = local_web_df.index.difference(df.index)
        if not additional_data.empty:
            return f'В источнике {source.__module__} присутствуют дополнительные данные {additional_data}'
        df = df[local_web_df.index]
        if not np.allclose(df, local_web_df):
            return f'В источнике {source.__module__} не совпадают данные'
    return 'OK'


if __name__ == '__main__':
    print(smart_lab_status(('AKRN', 'CHMF', 'RTKMP')))
    print(need_update('TTLK'))
