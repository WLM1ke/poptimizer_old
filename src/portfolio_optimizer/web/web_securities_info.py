"""Загружает информацию о тикерах с http://iss.moex.com"""

import json
from urllib import request

import pandas as pd

from portfolio_optimizer.web.labels import LAST_PRICE, LOT_SIZE, COMPANY_NAME, REG_NUMBER, TICKER


def make_url(tickers: tuple):
    """Формирует url для запроса информации на http://iss.moex.com"""
    url_base = ('https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json?'
                'securities={tickers}')
    return url_base.format(tickers=','.join(tickers))


def get_json(tickers: tuple):
    """Загружает и проверяет json"""
    url = make_url(tickers)
    with request.urlopen(url) as response:
        data = json.load(response)
    validate_response(data, tickers)
    return data


def validate_response(data, tickers: tuple):
    """Проверяет что количество размер массивов с информации соответствует количеству тикеров

    Данные в ответе находятся в двух блоках: общая информация и котировки текущих торгов
    """
    n = len(tickers)
    msg = (f'Количество тикеров в ответе не соответствует запросу {tickers}'
           f' - возможно ошибка в написании')
    if len(data['securities']['data']) != n:
        raise ValueError(msg)
    if len(data['marketdata']['data']) != n:
        raise ValueError(msg)


def make_df(raw_json):
    """Данные из двух подразделов в ответе объединяются в единый DataFrame

    Данные в ответе находятся в двух блоках: общая информация и котировки текущих торгов
    """
    securities = pd.DataFrame(data=raw_json['securities']['data'],
                              columns=raw_json['securities']['columns'])
    market_data = pd.DataFrame(data=raw_json['marketdata']['data'],
                               columns=raw_json['marketdata']['columns'])
    securities = securities.set_index('SECID')[['SHORTNAME', 'REGNUMBER', 'LOTSIZE']]
    market_data = pd.to_numeric(market_data.set_index('SECID')['LAST'])
    df = pd.concat([securities, market_data], axis=1)
    df.index.name = TICKER
    df.columns = [COMPANY_NAME, REG_NUMBER, LOT_SIZE, LAST_PRICE]
    return df


def securities_info(tickers: tuple):
    """
    Возвращает краткое наименование, размер лота и последнюю цену

    Parameters
    ----------
    tickers
        Кортеж тикеров

    Returns
    -------
    pandas.DataFrame
        В строках тикеры (используется написание из выдачи ISS)
        В столбцах краткое наименование, регистрационный номер, размер лота и последняя цена
    """
    raw_json = get_json(tickers)
    return make_df(raw_json)


if __name__ == "__main__":
    print(securities_info(('UPRO', 'MRSB')))
