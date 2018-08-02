"""Класс с данными, который хранит и автоматически обновляет дату последнего изменения данных"""

import arrow

TIME_ZONE = 'Europe/Moscow'


class Datum:
    """Класс с данными, который хранит и автоматически обновляет дату последнего изменения данных

    Поддерживается операция присвоения значения с помощью =
    Время изменения данных хранится в часовом поясе MOEX
    """

    def __init__(self, value):
        self._value = value
        self._time = arrow.now(TIME_ZONE)

    def __str__(self):
        return f'Datum(Value={self.value}, time={self.time})'

    @property
    def value(self):
        """Данные"""
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self._time = arrow.now(TIME_ZONE)

    @property
    def time(self):
        """Время обновления данных в часовом поясе MOEX"""
        return self._time


if __name__ == '__main__':
    data = Datum(42)
    print(data)
    data.value = 24
    print(data)
