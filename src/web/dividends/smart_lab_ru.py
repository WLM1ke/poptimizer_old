"""Загружает данные по предстоящим дивидендам с https://www.smart-lab.ru"""
from web.dividends import dohod_ru, parser
from web.labels import TICKER, DATE, DIVIDENDS

URL = 'https://smart-lab.ru/dividends/index/order_by_yield/desc/'
TABLE_INDEX = 2
HEADER_SIZE = 1
FOOTER_SIZE = 1

TICKER_COLUMN = parser.DataColumn(1,
                                  {0: 'Тикер',
                                   -1: '\n+добавить дивиденды\nИстория выплаченных дивидендов\n'},
                                  lambda x: x)

DATE_COLUMN = parser.DataColumn(4,
                                {0: 'дата отсечки',
                                 -1: '\n+добавить дивиденды\nИстория выплаченных дивидендов\n'},
                                parser.date_parser)

DIVIDENDS_COLUMN = parser.DataColumn(7,
                                     {0: 'дивиденд,руб',
                                      -1: '\n+добавить дивиденды\nИстория выплаченных дивидендов\n'},
                                     parser.div_parser)


def dividends_smart_lab():
    """
    Возвращает ожидаемые дивиденды с сайта https://smart-lab.ru/

    Returns
    -------
    pandas.DataFrame
        Строки - тикеры
        столбцы - даты закрытия и дивиденды
    """
    html = dohod_ru.get_html(URL)
    table = parser.HTMLTableParser(html, TABLE_INDEX)
    columns = [TICKER_COLUMN, DATE_COLUMN, DIVIDENDS_COLUMN]
    df = table.make_df(columns, HEADER_SIZE, FOOTER_SIZE)
    df.columns = [TICKER, DATE, DIVIDENDS]
    return df.set_index(DATE)


if __name__ == '__main__':
    print(dividends_smart_lab())
