"""Сохраняет, обновляет и загружает локальную версию данных по индексу MOEX Russia Net Total Return (Resident)"""
import web
from local.data_manager import AbstractDataManager


INDEX_NAME = 'MCFTRR'


class IndexDataManager(AbstractDataManager):
    """Реализует особенность хранения и загрузки исторических котировок по индексу"""
    def __init__(self):
        super().__init__(None, INDEX_NAME)

    def download_all(self):
        return web.index()

    def download_update(self):
        last_date = self.value.index[-1]
        return web.index(last_date)

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
    return data.value


if __name__ == '__main__':
    print(index())
