"""Реализация менеджера данных по дивидендам с smart-lab.ru"""
import web
from local.data_manager import AbstractDataManager
from web.labels import TICKER, DIVIDENDS

SMART_LAB_NAME = 'smart-lab'


class SmartLabDataManager(AbstractDataManager):
    """Организация создания, обновления и предоставления локальных DataFrame

    Данные загружаются с сайта smart-lab.ru
    """
    is_unique = False
    is_monotonic = False
    update_from_scratch = True
    def __init__(self):
        super().__init__(None, SMART_LAB_NAME)

    def download_all(self):
        return web.dividends_smart_lab()

    def download_update(self):
        super().download_update()


def dividends_smart_lab(ticker: str = None):
    """Возвращает данные об ожидаемых дивидендах на СмартЛабе

    Без параметров - всю имеющуюся информацию, или для конкретного тикера

    Parameters
    ----------
    ticker
        Тикер для которого необходимо предоставить информацию

    Returns
    -------
    pandas.DataFrame
        Информация сроках и размере предстоящих выплат
    """
    data = SmartLabDataManager().value
    if ticker:
        data = data[data[TICKER] == ticker][DIVIDENDS]
        data.name = ticker
        return data
    else:
        return data


if __name__ == '__main__':
    print(dividends_smart_lab('CHMF'))
    print(dividends_smart_lab())
