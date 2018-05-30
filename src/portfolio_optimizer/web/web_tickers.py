"""Загружает информацию о тикерах для данного регистрационного номера с http://iss.moex.com"""

import json
import time
from urllib import request
from urllib.error import URLError


def get_json(reg_number: str):
    """Получает json с http://iss.moex.com"""
    try:
        url = f'http://iss.moex.com/iss/securities.json?q={reg_number}'
        with request.urlopen(url) as response:
            data = json.load(response)
    except URLError as error:
        if error.errno == 60:
            print(error)
            print('Новая попытка через 5 секунд')
            time.sleep(5)
            data = get_json(reg_number)
        else:
            raise error
    return data


def validate(reg_number: str, tickers: tuple):
    """Проверяет, что в ответе есть хотя бы один тикер"""
    if len(tickers) == 0:
        raise ValueError(f'Некорректный регистрационный номер {reg_number}')


def yield_parsed_tickers(raw_json, reg_number: str):
    """Выбирает информацию по тикерам и последовательно возвращает ее"""
    header = raw_json['securities']['columns']
    rows = raw_json['securities']['data']
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
    raw_json = get_json(reg_number)
    tickers = tuple(yield_parsed_tickers(raw_json, reg_number))
    validate(reg_number, tickers)
    return tickers


if __name__ == '__main__':
    print(reg_number_tickers('1-02-65104-D'))
    print(reg_number_tickers('10301481B'))
    print(reg_number_tickers('20301481B'))
    print(reg_number_tickers('1-02-06556-A'))
