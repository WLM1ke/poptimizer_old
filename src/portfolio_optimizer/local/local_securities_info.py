"""Сохраняет, обновляет и загружает локальную версию информации об акциях"""

from portfolio_optimizer import web
from portfolio_optimizer.local.data_manager import DataManager
from portfolio_optimizer.settings import LOT_SIZE, COMPANY_NAME, REG_NUMBER

SECURITIES_INFO_CATEGORY = 'securities_info'
SECURITIES_INFO_MANE = 'securities_info'


class SecuritiesInfoDataManager(DataManager):
    """Реализует особенность валидации информации об акциях"""

    def __init__(self, tickers: tuple):
        self.tickers = tickers

        def source_function():
            """Возвращает web данные кроме последней цены, которая непрерывно обновляется"""
            return web.securities_info(tickers)[[COMPANY_NAME, REG_NUMBER, LOT_SIZE]]

        super().__init__(SECURITIES_INFO_CATEGORY, SECURITIES_INFO_MANE, source_function)

    def _need_update(self):
        if super()._need_update():
            return True
        if not all(self.get().index.contains(ticker) for ticker in self.tickers):
            return True
        return False


def security_info(tickers: tuple):
    """
    Возвращает данные по тикерам из списка и при необходимости обновляет локальные данные

    Parameters
    ----------
    tickers
        Кортеж тикеров

    Returns
    -------
    pandas.DataFrame
        В строках тикеры
        В столбцах данные по размеру лота, регистрационному номеру и краткому наименованию
    """
    data = SecuritiesInfoDataManager(tickers)
    return data.get().loc[tickers, :]


def aliases(ticker: str):
    """
    Возвращает список тикеров аналогов для заданного тикера

    Функция нужна для выгрузки длинной истории котировок с учетом изменения тикера

    Parameters
    ----------
    ticker
        Тикер

    Returns
    -------
    tuple
        Тикеры аналоги с таким же регистрационным номером
    """
    reg_number = security_info((ticker,)).loc[ticker, REG_NUMBER]
    return web.reg_number_tickers(reg_number)


if __name__ == '__main__':
    print(security_info(('KBTK', 'MOEX')))
    print(aliases('UPRO'))
