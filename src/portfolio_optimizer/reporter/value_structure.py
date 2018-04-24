"""Составляет таблицу со стоимостью портфеля для отчета"""

import locale

import pandas as pd
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

from portfolio_optimizer import Portfolio
from portfolio_optimizer.settings import PORTFOLIO

# Количество строк в таблице, которое влезает на страницу - иначе она не рисуется
FIT_PAGE_ROWS = 10

# Общее наименование мелких позиций в портфеле
OTHER = 'OTHER'


def drop_small_positions(portfolio: Portfolio):
    """Объединяет самые мелкие позиции с суммарным весом меньше среднего веса остальных в Other

    Если строк очень много, они обрезаются, чтобы таблица поместилась
    """
    value = portfolio.value
    portfolio_value = value.iloc[-1]
    sorted_value = value.iloc[:-1].sort_values()
    cum_value = sorted_value.cumsum()
    condition = (cum_value * range(cum_value.shape[0] - 1, -1, -1)) >= (portfolio_value - cum_value)
    value = sorted_value[condition]
    value.sort_values(ascending=False, inplace=True)
    if len(value) > FIT_PAGE_ROWS:
        value = value.iloc[:FIT_PAGE_ROWS]
    value[OTHER] = portfolio_value - value.sum()
    value[PORTFOLIO] = portfolio_value
    return value


def convent_to_list_of_lists(df: pd.Series):
    """Конвертирует серию в список списков"""
    locale.setlocale(locale.LC_ALL, 'ru_RU')
    list_of_lists = [['Name', 'Value']]
    for i in df.index:
        name = i
        value = int(df[i])
        list_of_lists.append([f'{name}', f'{value:n}'])
    return list_of_lists


def make_table(portfolio: Portfolio):
    """Формирует и форматирует pdf таблицу"""
    table_dataframe = drop_small_positions(portfolio)
    data = convent_to_list_of_lists(table_dataframe)
    style = TableStyle([('LINEBEFORE', (1, 0), (1, -1), 0.5, colors.black),
                        ('LINEABOVE', (0, 1), (-1, 1), 0.5, colors.black),
                        ('LINEABOVE', (0, -1), (-1, -1), 0.5, colors.black),
                        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTRE'),
                        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')])
    table = Table(data, style=style)
    table.hAlign = 'LEFT'
    return table
