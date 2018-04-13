"""Сохраняет, обновляет и загружает локальную версию данных по индексу MOEX Russia Net Total Return (Resident)"""


from portfolio_optimizer import web
from portfolio_optimizer.local.data_manager import DataManager

INDEX_CATEGORY = 'index'
INDEX_NAME = 'MCFTRR'


def index():
    """
    Возвращает историю индекса полной доходности с учетом российских налогов из локальных данных

    При необходимости локальные данные обновляются для ускорения последующих загрузок

    Returns
    -------
    pandas.Series
        В строках даты торгов
    """
    data = DataManager(INDEX_CATEGORY, INDEX_NAME, web.index, web.index)
    return data.get()


if __name__ == '__main__':
    print(index())
