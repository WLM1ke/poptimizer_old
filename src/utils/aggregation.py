"""Функции агрегации по времени"""
import functools
from enum import Enum

import pandas as pd


def yearly_aggregator(date: pd.Timestamp, end_of_year: pd.Timestamp):
    """Округляет дату вверх до месяца и числа конца года

    Parameters
    ----------
    date
        Дата, для которой необходимо рассчитать годовую агрегацию
    end_of_year
        Пример даты окончания года - ее месяц и число используются для агрегации
    Returns
    -------
    pd.Timestamp
        Возвращает дату окончания года для указанной даты
    """
    end_month = end_of_year.month
    end_day = end_of_year.day
    if (date.month, date.day) <= (end_month, end_day):
        return date + pd.DateOffset(month=end_month, day=end_day)
    else:
        return date + pd.DateOffset(years=1, month=end_month, day=end_day)


def yearly_aggregation_func(end_of_year: pd.Timestamp):
    """Возвращает функцию для годовой агрегации

    Parameters
    ----------
    end_of_year
        Дата месяц и число которой считаются окончанием года
    Returns
    -------
    function
        Агрегирующая функция - принимает дату в формате pd.Timestamp в качестве единственного аргумента и возвращает
        дату окончания года для нее
    """
    return functools.partial(yearly_aggregator, end_of_year=end_of_year)


def quarterly_aggregator(date: pd.Timestamp, end_of_quarter: pd.Timestamp):
    """Округляет дату вверх числа конца квартала

    Parameters
    ----------
    date
        Дата, для которой необходимо рассчитать квартальную агрегацию
    end_of_quarter
        Пример даты окончания квартала - ее число используются для агрегации
    Returns
    -------
    pd.Timestamp
        Возвращает дату окончания квартала для указанной даты
    """
    end_day = end_of_quarter.day
    months_to_end_of_quarter = (end_of_quarter.month - date.month) % 3
    if (0, date.day) <= (months_to_end_of_quarter, end_day):
        return date + pd.DateOffset(months=months_to_end_of_quarter, day=end_day)
    else:
        return date + pd.DateOffset(months=3, day=end_day)


def quarterly_aggregation_func(end_of_quarter: pd.Timestamp):
    """Возвращает функцию для квартальной агрегации

    Parameters
    ----------
    end_of_quarter
        Дата число которой считаются окончанием квартала
    Returns
    -------
    function
        Агрегирующая функция - принимает дату в формате pd.Timestamp в качестве единственного аргумента и возвращает
        дату окончания квартала для нее
    """
    return functools.partial(quarterly_aggregator, end_of_quarter=end_of_quarter)


def monthly_aggregator(date: pd.Timestamp, end_of_month: pd.Timestamp):
    """Округляет дату вверх числа конца месяца

    Parameters
    ----------
    date
        Дата, для которой необходимо рассчитать месячную агрегацию
    end_of_month
        Пример даты окончания месяца - ее число используются для агрегации
    Returns
    -------
    pd.Timestamp
        Возвращает дату окончания месяца для указанной даты
    """
    end_day = end_of_month.day
    if date.day <= end_day:
        return date + pd.DateOffset(day=end_day)
    else:
        return date + pd.DateOffset(months=1, day=end_day)


def monthly_aggregation_func(end_of_month: pd.Timestamp):
    """Возвращает функцию для месячной агрегации

    Parameters
    ----------
    end_of_month
        Дата число которой считаются окончанием месяца
    Returns
    -------
    function
        Агрегирующая функция - принимает дату в формате pd.Timestamp в качестве единственного аргумента и возвращает
        дату окончания месяца для нее
    """
    return functools.partial(monthly_aggregator, end_of_month=end_of_month)


class Freq(Enum):
    """Различные периоды агригации данных"""
    monthly = (monthly_aggregation_func, 12)
    quarterly = (quarterly_aggregation_func, 4)
    yearly = (yearly_aggregation_func, 1)

    def __init__(self, aggregation_func, times_in_year):
        self._aggregation_func = aggregation_func
        self._times_in_year = times_in_year

    def __str__(self):
        return f'{self.__class__.__name__}.{self.name}'

    @property
    def aggregation_func(self):
        """Функция агригации"""
        return self._aggregation_func

    @property
    def times_in_year(self):
        """Количество периодов в году"""
        return self._times_in_year


if __name__ == '__main__':
    mon = Freq.monthly
    print(mon)
