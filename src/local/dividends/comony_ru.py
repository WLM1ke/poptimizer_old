"""Организация хранения локальных данных с https://www.conomy.ru"""
from utils.data_manager import AbstractDataManager
from web import dividends
from web.labels import DATE

CONOMY_NAME = 'conomy'


class ConomyDataManager(AbstractDataManager):
    """Организация создания, обновления и предоставления локальных DataFrame

    Данные загружаются с сайта https://www.conomy.ru
    """

    def __init__(self, ticker: str):
        super().__init__(CONOMY_NAME, ticker)

    def download_all(self):
        """Загружаются все данные

        Несколько выплат в одну дату объединяются для уникальности индекса и удобства сопоставления"""
        return dividends.conomy(self.data_name).groupby(DATE).sum()

    def download_update(self):
        """Нет возможности загрузить данные частично"""
        super().download_update()


def dividends_conomy(ticker: str):
    """Сохраняет, при необходимости обновляет и возвращает дивиденды для тикеров

    Parameters
    ----------
    ticker
        Список тикеров
    Returns
    -------
    pd.Series
        В строках - даты выплаты дивидендов
        Значения - выплаченные дивиденды
    """
    data = ConomyDataManager(ticker)
    return data.value


if __name__ == '__main__':
    print(dividends_conomy('SNGSP'))
