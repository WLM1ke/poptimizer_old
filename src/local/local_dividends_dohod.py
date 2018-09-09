"""Реализация менеджера данных по дивидендам с dohod.ru"""
from utils.data_manager import AbstractDataManager
from web import dividends
from web.labels import DATE

DOHOD_CATEGORY = 'dohod.ru'


class DohodDataManager(AbstractDataManager):
    """Организация создания, обновления и предоставления локальных DataFrame

    Данные загружаются с сайта dohod.ru
    """
    def __init__(self, ticker: str):
        super().__init__(DOHOD_CATEGORY, ticker)

    def download_all(self):
        return dividends.dohod(self.data_name).groupby(DATE).sum()

    def download_update(self):
        super().download_update()


def dividends_dohod(ticker: str):
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
    data = DohodDataManager(ticker)
    return data.value


if __name__ == '__main__':
    print(dividends_dohod('MFON'))
