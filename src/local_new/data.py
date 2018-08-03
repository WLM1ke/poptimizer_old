"""Класс с данными, который хранит и автоматически обновляет дату последнего изменения данных"""

import time

class Data:
    """Класс с данными, который хранит и автоматически обновляет дату последнего изменения данных

    Поддерживается операция присвоения значения с  оператором =
    Время хранится в формате epoch
    """

    def __init__(self, value):
        self._value = value
        self._time = time.time()

    def __str__(self):
        return f'{data.__class__.__name__}(value={self.value}, time={time.ctime(self.time)})'

    @property
    def value(self):
        """Данные"""
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self._time = time.time()

    @property
    def time(self):
        """Время обновления данных - epoch"""
        return self._time


if __name__ == '__main__':
    data = Data(42)
    print(data)
    data.value = 24
    print(data)
    print(data.time)
