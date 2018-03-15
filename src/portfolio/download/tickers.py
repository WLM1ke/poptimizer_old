"""Return list of ticker for given registration number from ISS.

    get_tickers(reg_number)
"""

import requests


def get_json(reg_number):
    url = f'https://iss.moex.com/iss/securities.json?q={reg_number}'
    respond = requests.get(url)
    json = respond.json()
    return json


def validate(reg_number, tickers):
    if len(tickers) == 0:
        raise ValueError(f'Некорректный регистрационный номер {reg_number}')


def yield_parsed_tickers(json, reg_number):
    header = json['securities']['columns']
    rows = json['securities']['data']
    ticker_index = header.index('secid')
    reg_number_index = header.index('regnumber')
    for row in rows:
        if row[reg_number_index] == reg_number:
            yield row[ticker_index]


def get_tickers(reg_number):
    """
    Возвращает список тикеров для заданного регистрационного номера с ISS сервера.

    Parameters
    ----------
    reg_number: str
        Регистрационный номер.

    Returns
    -------
    str
        Разделенный пробелами список тикеров.
    """
    json = get_json(reg_number)
    tickers = list(yield_parsed_tickers(json, reg_number))
    validate(reg_number, tickers)
    return ' '.join(yield_parsed_tickers(json, reg_number))


if __name__ == '__main__':
    print(get_tickers('1-02-65104-D'))
    print(get_tickers('10301481B'))
    print(get_tickers('20301481B'))
    print(get_tickers('1-02-06556-A'))
