"""Загружает котировки и объемы торгов для тикеров с http://iss.moex.com"""

import pandas as pd
import requests

from portfolio_optimizer.settings import DATE, CLOSE_PRICE, VOLUME


class Quotes:
    """Представление ответа сервера по котировкам в виде итератора

    При большом запросе сервер ISS возвращает данные блоками обычно по 100 значений, поэтому класс является итератором
    Если начальная дата не указана, то загружается вся доступная история котировок
    """
    _base_url = 'https://iss.moex.com/iss/history/engines/stock/markets/shares/securities/'

    def __init__(self, ticker: str, start_date):
        self._ticker, self._start_date = ticker, start_date
        self._block_position = 0
        self._data = None
        self.get_json()

    @property
    def url(self):
        """Создает url для запроса к серверу http://iss.moex.com"""
        url = self._base_url + f'{self._ticker}.json'
        query_args = [f'start={self._block_position}']
        if self._start_date:
            if not isinstance(self._start_date, pd.Timestamp):
                raise TypeError(self._start_date)
            query_args.append(f"from={self._start_date:%Y-%m-%d}")
        arg_str = '&'.join(query_args)
        return f'{url}?{arg_str}'

    def get_json(self):
        """Загружает и проверяет json с данными"""
        response = requests.get(self.url)
        self._data = response.json()
        self._validate()

    def _validate(self):
        """Первый запрос должен содержать не нулевое количество строк"""
        if self._block_position == 0 and len(self) == 0:
            raise ValueError(f'Пустой ответ. Проверьте запрос: {self.url}')

    def __len__(self):
        return len(self.rows)

    @property
    def rows(self):
        """Извлекает массив строк с данными из json"""
        return self._data['history']['data']

    @property
    def columns(self):
        """"Извлекает массив наименований столбцов с данными из json"""
        return self._data['history']['columns']

    @property
    def df(self):
        """Формирует DataFrame и выбирает необходимые колонки - даты, цены закрытия и объемы."""
        df = pd.DataFrame(data=self.rows, columns=self.columns)
        df[DATE] = pd.to_datetime(df['TRADEDATE'])
        df[CLOSE_PRICE] = pd.to_numeric(df['CLOSE'])
        df[VOLUME] = pd.to_numeric(df['VOLUME'])
        return df[[DATE, CLOSE_PRICE, VOLUME]]

    def __iter__(self):
        return self

    def __next__(self):
        # если блок не пустой
        if self:
            # используем текущий результат парсинга
            df = self.df
            # перещелкиваем сдвиг на следующий блок и получаем новые данные
            self._block_position += len(self)
            self.get_json()
            # выводим текущий результат парсинга
            return df
        else:
            raise StopIteration


def quotes(ticker, start_date=None):
    """
    Возвращает историю котировок тикера начиная с даты start_date

    Если дата None, то загружается вся доступная история котировок

    Parameters
    ----------
    ticker : str
        Тикер, например, 'MOEX'

    start_date : pd.Timestamp or None
        Начальная дата котировок

    Returns
    -------
    pandas.DataFrame
        В строках даты торгов
        В столбцах [CLOSE, VOLUME] цена закрытия и оборот в штуках
    """
    gen = Quotes(ticker, start_date)
    df = pd.concat(gen, ignore_index=True)
    # Для каждой даты выбирается режим торгов с максимальным оборотом
    df = df.loc[df.groupby(DATE)[VOLUME].idxmax()]
    df = df.set_index(DATE).sort_index()
    return df


if __name__ == '__main__':
    z = quotes('AKRN', start_date=pd.to_datetime('2017-10-02'))
    print(z.head())
    print(z.tail())
