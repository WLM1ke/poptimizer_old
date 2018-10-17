"""Сохраняет, обновляет и загружает локальную версию данных по индексу MOEX Russia Net Total Return (Resident)"""
from utils.data_manager import AbstractDataManager
from web import moex

INDEX_NAME = 'MCFTRR'


class IndexDataManager(AbstractDataManager):
    """Реализует особенность хранения и загрузки исторических котировок по индексу"""
    def __init__(self):
        super().__init__(None, INDEX_NAME)

    def download_all(self):
        """Загружает все данные по индексу полной доходности"""
        return moex.index()

    def download_update(self):
        """Загружает новые данные с последнего значения, включительно

        Последнее значение используется для проверки стыковки данных
        """
        last_date = self.value.index[-1]
        return moex.index(last_date)


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
