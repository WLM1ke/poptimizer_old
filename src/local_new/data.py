"""Класс с данными, который хранит и автоматически обновляет дату последнего изменения данных"""

import time


class Data:
    """Класс с данными, который хранит и автоматически обновляет дату последнего изменения данных

    Поддерживается операция присвоения значения с  оператором =
    Время хранится в формате epoch
    Если значение не присвоено при создании, значение и время обновления None
    """

    def __init__(self, value=None):
        self._value = value
        if value is None:
            self._last_update = None
        else:
            self._last_update = time.time()

    def __str__(self):
        last_update = None if self._last_update is None else time.ctime(self._last_update)
        return f'{self.__class__.__name__}(value={self.value}, last_update={last_update})'

    @property
    def value(self):
        """Данные"""
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self._last_update = time.time()

    @property
    def last_update(self):
        """Время обновления данных - epoch"""
        return self._last_update


if __name__ == '__main__':
    data = Data(42)
    print(data)
    data.value = 24
    print(data)
    print(data.last_update)
    print(Data())
