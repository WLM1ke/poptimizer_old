"""Функции агрегации по времени"""
import functools

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
