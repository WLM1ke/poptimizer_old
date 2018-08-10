"""Функции проверки статуса дивидендов"""
import pandas as pd

from local import local_dividends_smart_lab, local_dividends_dohod
from local.local_dividends import DividendsDataManager, STATISTICS_START
from web.labels import TICKER, DIVIDENDS

DIVIDENDS_SOURCES = [local_dividends_dohod.dividends_dohod,
                     local_dividends_smart_lab.dividends_smart_lab]


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
    df = manager.value
    result = []
    for source in DIVIDENDS_SOURCES:
        print(f'\nСРАВНЕНИЕ ОСНОВНЫХ ДАННЫХ С {source.__name__}\n')
        source_df = source(ticker)
        source_df = source_df[source_df.index >= pd.Timestamp(STATISTICS_START)]
        source_df.name = source.__name__
        compare_df = pd.concat([df, source_df], axis='columns')
        compare_df['STATUS'] = ''
        compare_df.loc[compare_df[ticker] != compare_df[source.__name__], 'STATUS'] = 'ERROR'
        print(compare_df)
        result.append(compare_df)
    return result


if __name__ == '__main__':
    print(smart_lab_status(('AKRN', 'CHMF', 'RTKMP')))
    dividends_status('ENRU')