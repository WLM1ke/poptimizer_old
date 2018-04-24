"""График динамики стоимости портфеля"""
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
    x = index.index.astype(str)
    x_ticks_loc = range(0, len(x), 12)
    x_ticks_labels = x[x_ticks_loc]
    plt.yticks(fontsize=8)
    plt.xticks(x_ticks_loc, x_ticks_labels, fontsize=8)
    plt.legend(('Portfolio', 'MOEX Russia Net Total Return (Resident)'), fontsize=8, frameon=False)

    file = BytesIO()
    plt.savefig(file, dpi=300, format='jpg', bbox_inches='tight')
    return Image(file, inch_width * inch, inch_height * inch)


def convent_to_list_of_lists(df: pd.Series):
    """Конвертирует серию в список списков"""
    list_of_lists = [['Period', 'Portfolio', 'Index']]
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


def make_table(df: pd.DataFrame):
    """Формирует и форматирует pdf таблицу"""
    portfolio = portfolio_cum_return(df)
    portfolio_return = portfolio.iloc[-1] / portfolio * 100 - 100
    index = index_cum_return(df)
    index_return = index.iloc[-1] / index * 100 - 100
    df = pd.concat([portfolio_return, index_return], axis='columns')
    data = convent_to_list_of_lists(df)

    style = TableStyle([('LINEBEFORE', (1, 0), (1, -1), 0.5, colors.black),
                        ('LINEABOVE', (0, 1), (-1, 1), 0.5, colors.black),
                        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                        ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTRE')])
    table = Table(data, style=style)
    table.hAlign = 'LEFT'
    return table
