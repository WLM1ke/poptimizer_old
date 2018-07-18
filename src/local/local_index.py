"""Сохраняет, обновляет и загружает локальную версию данных по индексу MOEX Russia Net Total Return (Resident)"""

import web
from local.data_manager import DataManager

INDEX_CATEGORY = 'index'
INDEX_NAME = 'MCFTRR'


class IndexDataManager(DataManager):
    """Реализует особенность загрузки исторических котировок по индексу"""

    def __init__(self):
        super().__init__(INDEX_CATEGORY, INDEX_NAME, web.index, web.index)


def index():
    """
    Возвращает историю индекса полной доходности с учетом российских налогов из локальных данных

    При необходимости локальные данные обновляются для ускорения последующих загрузок

    Returns
    -------
    pandas.Series
        В строках даты торгов
    """
    data = IndexDataManager()
    return data.get()


if __name__ == '__main__':
    print(index())
