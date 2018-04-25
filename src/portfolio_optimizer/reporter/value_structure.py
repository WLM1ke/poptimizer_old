"""Составляет таблицу со стоимостью портфеля для отчета"""

import locale
from io import BytesIO

import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle, Image

from portfolio_optimizer import Portfolio
from portfolio_optimizer.settings import PORTFOLIO

# Количество строк в таблице, которое влезает на страницу - иначе она не рисуется
FIT_PAGE_ROWS = 9

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


def make_plot(portfolio: Portfolio, inch_width: float, inch_height: float):
    """Строит диаграмму структуры портфеля"""
    table_dataframe = drop_small_positions(portfolio)
    values = table_dataframe.iloc[:-1] / table_dataframe.iloc[-1]
    labels = table_dataframe.index[:-1] + values.apply(lambda x: f'\n{x * 100:.1f}%')

    fig, ax = plt.subplots(1, 1, figsize=(inch_width, inch_height))
    _, texts = ax.pie(values, labels=labels, startangle=90, counterclock=False, labeldistance=1.2)
    plt.setp(texts, size=8)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

    file = BytesIO()
    plt.savefig(file, dpi=300, format='png', transparent=True)
    return Image(file, inch_width * inch, inch_height * inch)


def convent_to_list_of_lists(df: pd.Series):
    """Конвертирует серию в список списков"""
    locale.setlocale(locale.LC_ALL, 'ru_RU')
    list_of_lists = [['Name', 'Value', 'Share']]
    for i in df.index:
        name = i
        value = int(df[i])
        share = df[i] / df[PORTFOLIO] * 100
        list_of_lists.append([f'{name}', f'{value:n}', f'{share:.1f}%'])
    return list_of_lists


def make_table(portfolio: Portfolio):
    """Формирует и форматирует pdf таблицу"""
    table_dataframe = drop_small_positions(portfolio)
    data = convent_to_list_of_lists(table_dataframe)
    style = TableStyle([('LINEBEFORE', (1, 0), (1, -1), 0.5, colors.black),
                        ('LINEABOVE', (0, 1), (-1, 1), 0.5, colors.black),
                        ('LINEABOVE', (0, -1), (-1, -1), 0.5, colors.black),
                        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTRE'),
                        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')])
    table = Table(data, style=style)
    table.hAlign = 'LEFT'
    return table
