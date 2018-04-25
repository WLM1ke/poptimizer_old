"""Таблица динамики дивидендов"""

import locale

import pandas as pd
from reportlab.lib import colors
from reportlab.platypus import TableStyle, Table


def make_12y_dividends_df(df: pd.DataFrame):
    return df['Dividends'].fillna(0).rolling(12).sum()


def convent_to_list_of_lists(df: pd.DataFrame):
    """Конвертирует серию в список списков"""
    locale.setlocale(locale.LC_ALL, 'ru_RU')
    list_of_lists = [['Period', 'Dividends']]
    index = df.index
    period = f'{index[-2].date()} - {index[-1].date()}'
    value = df['Dividends'].fillna(0).iloc[-1]
    list_of_lists.append([period, f'{value:n}'])
    df = make_12y_dividends_df(df)
    index = df.index
    for i in range(5):
        period = f'{index[-12 * i - 13].date()} - {index[-12 * i - 1].date()}'
        value = int(df.iloc[-12 * i - 1])
        list_of_lists.append([period, f'{value:n}'])
    return list_of_lists


def make_dividends_table(df: pd.DataFrame):
    """Формирует и форматирует pdf таблицу с дивидендными выплатами"""
    data = convent_to_list_of_lists(df)

    style = TableStyle([('LINEBEFORE', (1, 0), (1, -1), 0.5, colors.black),
                        ('LINEABOVE', (0, 1), (-1, 2), 0.5, colors.black),
                        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                        ('ALIGN', (0, 0), (0, -1), 'CENTRE')])
    table = Table(data, style=style)
    table.hAlign = 'LEFT'
    return table
