import requests
import pandas as pd


def make_url(tickers):
    if isinstance(tickers, str):
        tickers = [tickers]    
    url_base = 'https://iss.moex.com/iss/engines/stock/markets/shares/boards/TQBR/securities.json?securities={tickers}'
    return url_base.format(tickers=','.join(tickers))

def get_raw_json(tickers):
    url = make_url(tickers)
    r = requests.get(url)
    result = r.json()
    validate_response(result, tickers)
    return result

def validate_response(data, tickers):
    n = len(tickers)
    msg = ('Количество тикеров в ответе не соответсвует запросу'
           ' - возможно ошибка в написании')
    if len(data['securities']['data']) != n:
        raise ValueError(msg)
    if len(data['marketdata']['data']) != n:
        raise ValueError(msg)        
        
# ВОПРОС: зачем этот результат нужен в фрейме пандас? 
#         несколько подозрительно краткое название тянуть в фрейм

def get_securities_info(tickers):
    """
    Возвращает краткое наименование, размер лота и последнюю цену

    Parameters
    ----------
    tickers : str or list of str
        Тикер или список тикеров.

    Returns
    -------
    pandas.DataFrame
        В строках тикеры (используется написание из выдачи ISS).
        В столбцах краткое наименование, размер лота и последняя цена.
    """
    # Ответ сервера - словарь со сложной многоуровневой структурой
    # По ключу securities - словарь с описанием инструментов
    # По ключу marketdata - словарь с последними котировками
    # В каждом из вложеных словарей есть ключи columns и data с массивами 
    # описания колонок и данными
    # В массиве данных содержатся массивы для каждого запрошенного тикера
    data = get_raw_json(tickers)
    securities = pd.DataFrame(data=data['securities']['data'], columns=data['securities']['columns'])
    marketdata = pd.DataFrame(data=data['marketdata']['data'], columns=data['marketdata']['columns'])
    securities = securities.set_index('SECID')[['SHORTNAME', 'LOTSIZE']]
    marketdata = marketdata.set_index('SECID')['LAST']
    return pd.concat([securities, marketdata], axis=1)

if __name__ == "__main__":
    assert make_url('AKRN') == make_url(['AKRN'])
    assert make_url(['AKRN', 'GAZP', 'LKOH', 'SBER']).endswith('SBER') 
    d = get_raw_json(['AKRN', 'GAZP', 'LKOH', 'SBER'])
    assert isinstance(d, dict)
    assert list(d.keys()) == ['securities', 'marketdata', 'dataversion']   
