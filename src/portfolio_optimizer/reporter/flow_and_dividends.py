"""Таблица динамики дивидендов"""

import pandas as pd
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import TableStyle, Table, Paragraph, Frame

from portfolio_optimizer.reporter.pdf_style import TABLE_LINE_WIDTH, TABLE_LINE_COLOR, BLOCK_HEADER_STYLE
from portfolio_optimizer.reporter.portfolio_return import get_investors_names

# Доля левой части блока - используется для таблицы движения средств. В правой расположена таблица дивидендов
LEFT_PART_OF_BLOCK = 0.55


def make_flow_df(df: pd.DataFrame):
    """Формирует фрейм для отчета"""
    columns = df.columns
    # Колонки со стоимостью активов инвесторов и портфеля начинаются с Value
    columns_names = columns[columns.str.contains('Value')]
    df_table = df[columns_names].iloc[-2:]
    df_table.index = df_table.index.date.astype(str)
    # Расчет стоимости до внесения средств
    investors_names = get_investors_names(df)
    inflow = df[investors_names].iloc[-1].fillna(0)
    pre_inflow_value = df['Value'].iloc[-1] - inflow.sum()
    df_table.loc['Pre Inflow'] = df_table.iloc[-2] * pre_inflow_value / df_table['Value'].iloc[-2]
    # Долей инвесторов в стоимости активов
    df_share = df_table.div(df_table['Value'], axis='index')
    df_share.index = ['%'] * len(df_share)
    df_table = pd.concat([df_table, df_share])
    # Объем внесенных средств за последний период
    inflow['Value'] = inflow.sum()
    df_table.loc['Inflow'] = inflow.values
    # Правильная последовательность строк и наименования
    df_table = df_table.iloc[[0, 3, 2, 5, 6, 1, 4]]
    df_table.columns = list(investors_names) + ['Portfolio']
    return df_table


def make_list_of_lists_flow(df: pd.DataFrame):
    """Создает таблицу движения средств в виде списка списков"""
    flow_df = make_flow_df(df)
    list_of_lists = [[''] + list(flow_df.columns)]
    # Адресация по номерам позиций из-за дубликатов % в индексе
    for row, name in enumerate(flow_df.index):
        row_list = [name]
        for column, _ in enumerate(flow_df.columns):
            value = flow_df.iat[row, column]
            if name == '%':
                row_list.append(f'{value * 100:.2f}%')
            else:
                value = f'{value:,.0f}'.replace(',', ' ')
                row_list.append(value)
        list_of_lists.append(row_list)
    return list_of_lists


def make_pdf_flow_table(df: pd.DataFrame):
    """Формирует и форматирует pdf таблицу движения средств"""
    data = make_list_of_lists_flow(df)

    style = TableStyle([('LINEBEFORE', (1, 0), (1, -1), TABLE_LINE_WIDTH, TABLE_LINE_COLOR),
                        ('LINEBEFORE', (-1, 0), (-1, -1), TABLE_LINE_WIDTH, TABLE_LINE_COLOR),
                        ('LINEABOVE', (0, 1), (-1, 1), TABLE_LINE_WIDTH, TABLE_LINE_COLOR),
                        ('LINEABOVE', (0, 3), (-1, 3), TABLE_LINE_WIDTH, TABLE_LINE_COLOR),
                        ('LINEABOVE', (0, 5), (-1, 6), TABLE_LINE_WIDTH, TABLE_LINE_COLOR),
                        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTRE'),
                        ('ALIGN', (0, 2), (0, 2), 'CENTRE'),
                        ('ALIGN', (0, 4), (0, 4), 'CENTRE'),
                        ('ALIGN', (0, -1), (0, -1), 'CENTRE')])

    table = Table(data, style=style)
    table.hAlign = 'LEFT'
    return table


def make_12m_dividends_df(df: pd.DataFrame):
    """Скользящие дивиденды за последние 12 месяцев"""
    return df['Dividends'].fillna(0).rolling(12).sum()


def make_list_of_lists_dividends(df: pd.DataFrame):
    """Создает таблицу дивидендов в виде списка списков"""
    list_of_lists = [['Period', 'Dividends']]
    index = df.index
    period = f'{index[-2].date()} - {index[-1].date()}'
    value = df['Dividends'].fillna(0).iloc[-1]
    value = f'{value:,.0f}'.replace(',', ' ')
    list_of_lists.append([period, value])
    df = make_12m_dividends_df(df)
    index = df.index
    for i in range(5):
        period = f'{index[-12 * i - 13].date()} - {index[-12 * i - 1].date()}'
        value = df.iloc[-12 * i - 1]
        value = f'{value:,.0f}'.replace(',', ' ')
        list_of_lists.append([period, value])
    return list_of_lists


def make_pdf_dividends_table(df: pd.DataFrame):
    """Формирует и форматирует pdf таблицу с дивидендными выплатами"""
    data = make_list_of_lists_dividends(df)

    style = TableStyle([('LINEBEFORE', (1, 0), (1, -1), TABLE_LINE_WIDTH, TABLE_LINE_COLOR),
                        ('LINEABOVE', (0, 1), (-1, 2), TABLE_LINE_WIDTH, TABLE_LINE_COLOR),
                        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                        ('ALIGN', (0, 0), (0, -1), 'CENTRE')])

    table = Table(data=data, style=style)
    table.hAlign = 'LEFT'
    return table


def flow_and_dividends_block(df: pd.DataFrame, canvas: Canvas, x: float, y: float, width: float, height: float):
    """Формирует блок pdf-файла с информацией движении средств и дивидендах

    В левой части располагается табличка движения средств, а в правой - таблица дивидендов
    """
    left_block_header = Paragraph('Last Month Change and Inflow', BLOCK_HEADER_STYLE)
    left_table = make_pdf_flow_table(df)
    left_frame = Frame(x, y, width * LEFT_PART_OF_BLOCK, height,
                       leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=6,
                       showBoundary=0)
    left_frame.addFromList([left_block_header, left_table], canvas)

    right_block_header = Paragraph('Portfolio Dividends', BLOCK_HEADER_STYLE)
    right_table = make_pdf_dividends_table(df)
    right_frame = Frame(x + width * LEFT_PART_OF_BLOCK, y, width * (1 - LEFT_PART_OF_BLOCK), height,
                        leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=6,
                        showBoundary=0)
    right_frame.addFromList([right_block_header, right_table], canvas)
