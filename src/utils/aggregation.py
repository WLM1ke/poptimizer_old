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


if __name__ == '__main__':
    func = quarterly_aggregation_func(pd.Timestamp('2018-08-20'))
    print(func(pd.Timestamp('2018-08-18')))
    print(func(pd.Timestamp('2018-08-20')))
    print(func(pd.Timestamp('2018-08-21')))
    print(func(pd.Timestamp('2018-07-21')))
    print(func(pd.Timestamp('2018-06-21')))
    print(func(pd.Timestamp('2018-05-21')))
    print(func(pd.Timestamp('2018-04-21')))
    print(func(pd.Timestamp('2018-03-21')))
    print(func(pd.Timestamp('2018-12-21')))
