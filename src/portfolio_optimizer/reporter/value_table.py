"""Составляет таблицу со стоимостью портфеля для отчета"""

import locale

import pandas as pd
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

from portfolio_optimizer import Portfolio
from portfolio_optimizer.reporter.reporter import OTHER
from portfolio_optimizer.settings import PORTFOLIO


def drop_small_positions(portfolio: Portfolio):
    """Объединяет самые мелкие позиции с суммарным весом меньше среднего веса остальных в Other"""
    value = portfolio.value
    portfolio_value = value.iloc[-1]
    sorted_value = value.iloc[:-1].sort_values()
    cum_value = sorted_value.cumsum()
    condition = (cum_value * range(cum_value.shape[0] - 1, -1, -1)) >= (portfolio_value - cum_value)
    value = sorted_value[condition]
    value.sort_values(ascending=False, inplace=True)
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
    """Преобразует серию в список списков"""
    table_dataframe = drop_small_positions(portfolio)
    data = convent_to_list_of_lists(table_dataframe)
    font_size = 10
    font_leading = font_size * 1.2
    style = TableStyle([('FONTSIZE', (0, 0), (-1, -1), font_size),
                        ('LEADING', (0, 0), (-1, -1), font_leading),
                        ('LINEBEFORE', (1, 0), (1, -1), 0.5, colors.black),
                        ('LINEABOVE', (0, 1), (-1, 1), 0.5, colors.black),
                        ('LINEABOVE', (0, -1), (-1, -1), 0.5, colors.black),
                        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTRE'),
                        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')])
    return Table(data, style=style)
