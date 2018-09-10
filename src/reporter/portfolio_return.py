"""Формирование блока pdf-файла с информацией о доходности портфеля"""

from io import BytesIO

import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib.units import inch
from reportlab.platypus import Image, TableStyle, Table, Paragraph, Frame

from local import moex
from reporter.pdf_style import BLOCK_HEADER_STYLE, LINE_COLOR, LINE_WIDTH, BlockPosition

# Доля левой части блока - используется для таблицы. В правой расположена диаграмма
LEFT_PART_OF_BLOCK = 1 / 3


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
    index = moex.index()
    index = index[df.index]
    return index / index.iloc[0]


def make_plot(df: pd.DataFrame, width: float, height: float):
    """Строит график стоимости портфеля и возвращает объект pdf-изображения"""
    _, ax = plt.subplots(1, 1, figsize=(width / inch, height / inch))
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
    return Image(file, width, height)


def make_list_of_lists_table(df: pd.DataFrame):
    """Создает таблицу доходности портфеля и индекса в виде списка списков"""
    portfolio = portfolio_cum_return(df)
    portfolio_return = portfolio.iloc[-1] / portfolio * 100 - 100
    index = index_cum_return(df)
    index_return = index.iloc[-1] / index * 100 - 100
    list_of_lists = [['Period', 'Portfolio', 'MOEX']]
    i = 1
    while i < len(df):
        if i == 1:
            name = '1M'
        else:
            year = i // 12
            name = f'{year}Y'
        portfolio = portfolio_return.iloc[-i - 1]
        index = index_return.iloc[-i - 1]
        list_of_lists.append([f'{name}', f'{portfolio: .1f}%', f'{index: .1f}%'])
        if i == 1:
            i = 12
        else:
            i += 12
    return list_of_lists


def make_pdf_table(df: pd.DataFrame):
    """Формирует и форматирует pdf-таблицу доходности портфеля и индекса"""
    data = make_list_of_lists_table(df)

    style = TableStyle([('LINEBEFORE', (1, 0), (1, -1), LINE_WIDTH, LINE_COLOR),
                        ('LINEABOVE', (0, 1), (-1, 2), LINE_WIDTH, LINE_COLOR),
                        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTRE')])

    table = Table(data, style=style)
    table.hAlign = 'LEFT'
    return table


def portfolio_return_block(df: pd.DataFrame, block_position: BlockPosition):
    """Формирует блок pdf-файла с информацией доходности портфеля и индекса

    В левой части располагается табличка, а в правой части диаграмма
    """
    block_header = Paragraph('Portfolio Return', BLOCK_HEADER_STYLE)
    table = make_pdf_table(df)
    frame = Frame(block_position.x, block_position.y,
                  block_position.width * LEFT_PART_OF_BLOCK, block_position.height,
                  leftPadding=0, bottomPadding=0,
                  rightPadding=0, topPadding=6,
                  showBoundary=0)
    frame.addFromList([block_header, table], block_position.canvas)
    image = make_plot(df, block_position.width * (1 - LEFT_PART_OF_BLOCK), block_position.height)
    image.drawOn(block_position.canvas, block_position.x + block_position.width * LEFT_PART_OF_BLOCK, block_position.y)
