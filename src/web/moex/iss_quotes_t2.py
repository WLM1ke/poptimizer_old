"""Загружает котировки и объемы торгов в режиме TQBR T+2 для тикеров с http://iss.moex.com"""
import pandas as pd

from web.labels import DATE
from web.moex import iss_quotes


class QuotesT2(iss_quotes.Quotes):
    """Представление ответа сервера по котировкам в режиме TQBR T+2 в виде итератора

    При большом запросе сервер ISS возвращает данные блоками обычно по 100 значений, поэтому класс является итератором
    Если начальная дата не указана, то загружается вся доступная история котировок
    """
    _BASE_URL = ('https://iss.moex.com/iss/history/engines/stock/markets/shares/boards/TQBR/securities/'
                 '{ticker}.json?{query}')

    def _validate_response(self, block_position, json_data):
        """Для TQBR возможны пустые ответы - проверка не нужна"""
        pass


def quotes_t2(ticker, start=None):
    """
    Возвращает историю котировок в режиме TQBR T+2 тикера начиная с даты start_date

    Если дата None, то загружается вся доступная история котировок

    Parameters
    ----------
    ticker : str
        Тикер, например, 'MOEX'

    start : pd.Timestamp or None
        Начальная дата котировок

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов
        В столбцах [CLOSE, VOLUME] цена закрытия и оборот в штуках
    """
    gen = QuotesT2(ticker, start)
    try:
        df = pd.concat(gen, ignore_index=True)
    except ValueError:
        return pd.DataFrame()
    else:
        df = df.set_index(DATE)
        return df


if __name__ == '__main__':
    pass
