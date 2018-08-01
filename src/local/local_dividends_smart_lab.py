"""Сохраняет локальную версию дивидендов со smart-lab.ru"""

import arrow

import web
from local.data_manager import DataManager
from web.labels import TICKER, DIVIDENDS

DIVIDENDS_CATEGORY = 'dividends_smart_lab'
DIVIDENDS_NAME = 'dividends_smart_lab'
DAYS_TO_UPDATE = 1


class SmartLabDataManager(DataManager):
    """Осуществляет загрузку локальной версии данных раз в день"""
    days_to_update = DAYS_TO_UPDATE

    def __init__(self):
        super().__init__(DIVIDENDS_CATEGORY, DIVIDENDS_NAME, web.dividends_smart_lab)

    def _need_update(self):
        """Обновление осуществляется через DAYS_TO_UPDATE дней после предыдущего"""
        if self.file.last_update().shift(days=self.days_to_update) < arrow.now():
            return True
        return False

    def update(self):
        """Обновляет локальные данные, если наступило время очередного обновления

        Во время обновления проверяется совпадение новых данных со существующими
        """
        if self._need_update():
            print(f'Обновление локальных данных {self.frame_category} -> {self.frame_name}')
            df_new = self.source_function()
            self.file.dump(df_new)


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
    data = SmartLabDataManager().get()
    if ticker:
        data = data[data[TICKER] == ticker][DIVIDENDS]
        data.name = ticker
        return data
    else:
        return data


if __name__ == '__main__':
    print(dividends_smart_lab('CHMF'))
    print(dividends_smart_lab())
