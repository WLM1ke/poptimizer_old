"""Функции проверки статуса дивидендов"""
import numpy as np
import pandas as pd

from local.dividends import smart_lab_ru, dohod_ru
from local.dividends.sqlite import DividendsDataManager, STATISTICS_START
from web.labels import TICKER, DIVIDENDS

DIVIDENDS_SOURCES = [dohod_ru.dividends_dohod,
                     smart_lab_ru.dividends_smart_lab]


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
    df = smart_lab_ru.dividends_smart_lab()
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


def dividends_status(ticker: str):
    """Проверяет необходимость обновления данных

    Сравнивает основные данные по дивидендам с альтернативными источниками и выводит результаты сравнения

    Parameters
    ----------
    ticker
        Тикер

    Returns
    -------
    list
        Список из DataFrame с результатами сравнения для каждого источника данных
    """
    manager = DividendsDataManager(ticker)
    manager.update()
    df = manager.value
    result = []
    for source in DIVIDENDS_SOURCES:
        print(f'\nСРАВНЕНИЕ ОСНОВНЫХ ДАННЫХ С {source.__name__}\n')
        source_df = source(ticker)
        source_df = source_df[source_df.index >= pd.Timestamp(STATISTICS_START)]
        source_df.name = source.__name__
        compare_df = pd.concat([df, source_df], axis='columns')
        compare_df['STATUS'] = 'ERROR'
        compare_df.loc[np.isclose(compare_df[ticker].values, compare_df[source.__name__].values), 'STATUS'] = ''
        print(compare_df)
        result.append(compare_df)
    return result


if __name__ == '__main__':
    dividends_status('HYDR')
