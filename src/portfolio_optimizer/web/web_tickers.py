"""Загружает информацию о тикерах для данного регистрационного номера с http://iss.moex.com"""

import requests


def get_json(reg_number: str):
    """Получает json с http://iss.moex.com"""
    url = f'http://iss.moex.com/iss/securities.json?q={reg_number}'
    respond = requests.get(url)
    json = respond.json()
    return json


def validate(reg_number: str, tickers: tuple):
    """Проверяет, что в ответе есть хотя бы один тикер"""
    if len(tickers) == 0:
        raise ValueError(f'Некорректный регистрационный номер {reg_number}')


def yield_parsed_tickers(json, reg_number: str):
    """Выбирает информацию по тикерам и последовательно возвращает ее"""
    header = json['securities']['columns']
    rows = json['securities']['data']
    ticker_index = header.index('secid')
    reg_number_index = header.index('regnumber')
    for row in rows:
        if row[reg_number_index] == reg_number:
            yield row[ticker_index]


def reg_number_tickers(reg_number: str):
    """
    Возвращает кортеж тикеров для заданного регистрационного номера с http://iss.moex.com

    Parameters
    ----------
    reg_number
        Регистрационный номер

    Returns
    -------
    tuple
        Кортеж тикеров
    """
    json = get_json(reg_number)
    tickers = tuple(yield_parsed_tickers(json, reg_number))
    validate(reg_number, tickers)
    return tickers


if __name__ == '__main__':
    print(reg_number_tickers('1-02-65104-D'))
    print(reg_number_tickers('10301481B'))
    print(reg_number_tickers('20301481B'))
    print(reg_number_tickers('1-02-06556-A'))
