"""График динамики стоимости портфеля"""

import locale
from io import BytesIO

import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import Image, TableStyle, Table

from portfolio_optimizer import local


def get_investors_names(df: pd.DataFrame):
    """Получает имена инвесторов"""
    columns = df.columns
    names = columns[columns.str.contains('Value_')]
    names = names.str.slice(6)
    return names


def portfolio_cum_return(df: pd.DataFrame):
    """Кумулятивная доходность портфеля"""
    names = get_investors_names(df)
    # После внесения средств
    post_value = df['Value']
    # Перед внесением средств
    pre_value = post_value.subtract(df[names].sum(axis='columns'), fill_value=0)
    portfolio_return = pre_value / post_value.shift(1)
    portfolio_return.iloc[0] = 1
    return portfolio_return.cumprod()


def index_cum_return(df):
    """Кумулятивная доходность индекса в течении отчетного периода"""
    index = local.index()
    index = index[df.index]
    return index / index.iloc[0]


def make_plot(df: pd.DataFrame, inch_width: float, inch_height: float):
    """Строит график стоимости портфеля"""
    fig, ax = plt.subplots(1, 1, figsize=(inch_width, inch_height))
    ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.yaxis.set_major_formatter(plt.FuncFormatter('{:.0f}%'.format))
    plt.grid(True, 'major', lw=.5, c='black', alpha=.3)
    plt.tick_params(bottom=False, top=False, left=False, right=False)

    portfolio = portfolio_cum_return(df) * 100 - 100
    index = index_cum_return(df) * 100 - 100
    plt.plot(portfolio.values)
    plt.plot(index.values)
    x = index.index.astype(str).str.slice(stop=7)
    x_ticks_loc = range(0, len(x), 12)
    x_ticks_labels = x[x_ticks_loc]
    plt.yticks(fontsize=8)
    plt.xticks(x_ticks_loc, x_ticks_labels, fontsize=8)
    plt.legend(('Portfolio', 'MOEX Russia Net Total Return (Resident)'), fontsize=8, frameon=False)

    file = BytesIO()
    plt.savefig(file, dpi=300, format='png', transparent=True)
    return Image(file, inch_width * inch, inch_height * inch)


def convent_to_list_of_lists(df: pd.Series):
    """Конвертирует серию в список списков"""
    list_of_lists = [['Period', 'Portfolio', 'MOEX']]
    i = 1
    while i < len(df):
        if i == 1:
            name = '1M'
        else:
            year = i // 12
            name = f'{year}Y'
        portfolio = df.iloc[-i - 1, 0]
        index = df.iloc[-i - 1, 1]
        list_of_lists.append([f'{name}', f'{portfolio: .1f}', f'{index: .1f}'])
        if i == 1:
            i = 12
        else:
            i += 12
    return list_of_lists


def make_dynamics_table(df: pd.DataFrame):
    """Формирует и форматирует pdf таблицу с изменением стоимости за анализируемый период"""
    portfolio = portfolio_cum_return(df)
    portfolio_return = portfolio.iloc[-1] / portfolio * 100 - 100
    index = index_cum_return(df)
    index_return = index.iloc[-1] / index * 100 - 100
    df = pd.concat([portfolio_return, index_return], axis='columns')
    data = convent_to_list_of_lists(df)

    style = TableStyle([('LINEBEFORE', (1, 0), (1, -1), 0.5, colors.black),
                        ('LINEABOVE', (0, 1), (-1, 2), 0.5, colors.black),
                        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTRE')])
    table = Table(data, style=style)
    table.hAlign = 'LEFT'
    return table


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
