import locale

import pandas as pd
from reportlab.lib import colors
from reportlab.platypus import TableStyle, Table

from portfolio_optimizer.reporter.portfolio_return import get_investors_names


def make_flow_df(df: pd.DataFrame):
    """Формирует фрейм для отчета"""
    columns = df.columns
    columns_names = columns[columns.str.contains('Value')]
    df_table = df[columns_names].iloc[-2:]

    df_table.index = [str(i.date()) for i in df_table.index]

    investors_names = get_investors_names(df)
    inflow = df[investors_names].iloc[0].fillna(0)
    pre_inflow_value = df['Value'].iloc[-1] - inflow.sum()
    df_table.loc['Pre Inflow'] = df_table.iloc[-2] * pre_inflow_value / df_table['Value'].iloc[-2]

    df_share = df_table.div(df_table['Value'], axis='index')
    df_share.index = ['%'] * len(df_share)
    df_table = pd.concat([df_table, df_share])

    inflow['Value'] = inflow.sum()
    df_table.loc['Inflow'] = inflow.values

    df_table = df_table.iloc[[0, 3, 2, 5, 6, 1, 4]]

    df_table.columns = list(investors_names) + ['Portfolio']
    return df_table


def convent_flow_df_to_list_of_lists(df: pd.DataFrame):
    """Конвертирует фрейм в список списков"""
    locale.setlocale(locale.LC_ALL, 'ru_RU')
    list_of_lists = [[''] + list(df.columns)]
    for row, name in enumerate(df.index):
        row_list = [name]
        for column, _ in enumerate(df.columns):
            value = df.iat[row, column]
            if name == '%':
                row_list.append(f'{value * 100:.2f}%')
            else:
                row_list.append(f'{int(value):n}')
        list_of_lists.append(row_list)
    return list_of_lists


def make_flow_table(df: pd.DataFrame):
    """Формирует и форматирует pdf таблицу изменение стоимости долей"""
    flow_df = make_flow_df(df)
    data = convent_flow_df_to_list_of_lists(flow_df)

    style = TableStyle([('LINEBEFORE', (1, 0), (1, -1), 0.5, colors.black),
                        ('LINEBEFORE', (-1, 0), (-1, -1), 0.5, colors.black),
                        ('LINEABOVE', (0, 1), (-1, 1), 0.5, colors.black),
                        ('LINEABOVE', (0, 3), (-1, 3), 0.5, colors.black),
                        ('LINEABOVE', (0, 5), (-1, 5), 0.5, colors.black),
                        ('LINEABOVE', (0, 6), (-1, 6), 0.5, colors.black),
                        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTRE'),
                        ('ALIGN', (0, 2), (0, 2), 'CENTRE'),
                        ('ALIGN', (0, 4), (0, 4), 'CENTRE'),
                        ('ALIGN', (0, -1), (0, -1), 'CENTRE')])
    table = Table(data, style=style)
    table.hAlign = 'LEFT'
    return table
