"""Формирование блока pdf-файла с информацией о структуре портфеля"""

from io import BytesIO

import matplotlib

matplotlib.use('Agg')  # Для тестирования на Travis
import matplotlib.pyplot as plt
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Table, TableStyle, Image, Paragraph, Frame

from portfolio_optimizer import Portfolio
from portfolio_optimizer.reporter.pdf_style import BLOCK_HEADER_STYLE, LINE_COLOR, LINE_WIDTH, BOLD_FONT
from portfolio_optimizer.settings import PORTFOLIO

# Количество строк в таблице, которое влезает в блок и нормально выглядит на диаграмме
MAX_TABLE_ROWS = 9

# Общее наименование мелких позиций в портфеле
OTHER = 'OTHER'

# Доля левой части блока - используется для таблицы. В правой расположена диаграмма
LEFT_PART_OF_BLOCK = 1 / 3


def drop_small_positions(portfolio: Portfolio):
    """Отбрасывает нулевые позиции и при необходимости сокращает число строк до максимального

    Объединяет самые мелкие позиции в категорию OTHER и сортирует позиции по убыванию
    """
    value = portfolio.value
    portfolio_value = value.iloc[-1]
    value = value.iloc[:-1]
    value = value[value > 0]
    sorted_value = value.sort_values(ascending=False)
    if len(sorted_value) > MAX_TABLE_ROWS:
        sorted_value = sorted_value.iloc[:MAX_TABLE_ROWS]
        sorted_value[OTHER] = portfolio_value - sorted_value.sum()
    sorted_value[PORTFOLIO] = portfolio_value
    return sorted_value


def make_plot(portfolio: Portfolio, width: float, height: float):
    """Строит диаграмму структуры портфеля и возвращает объект pdf-изображения"""
    position_value = drop_small_positions(portfolio)
    position_share = position_value.iloc[:-1] / position_value.iloc[-1]
    labels = position_share.index + position_share.apply(lambda x: f'\n{x * 100:.1f}%')

    fig, ax = plt.subplots(1, 1, figsize=(width / inch, height / inch))
    _, texts = ax.pie(position_share, labels=labels, startangle=90, counterclock=False, labeldistance=1.2)
    plt.setp(texts, size=8)
    ax.axis('equal')

    file = BytesIO()
    plt.savefig(file, dpi=300, format='png', transparent=True)
    return Image(file, width, height)


def make_list_of_lists_table(portfolio: Portfolio):
    """Создает таблицу в виде списка списков"""
    position_value = drop_small_positions(portfolio)
    position_share = position_value / position_value.iloc[-1]
    list_of_lists = [['Name', 'Value', 'Share']]
    for i in position_value.index:
        name = i
        value = f'{position_value[i]:,.0f}'.replace(',', ' ')
        share = f'{position_share[i] * 100:.1f}%'
        list_of_lists.append([name, value, share])
    return list_of_lists


def make_pdf_table(portfolio: Portfolio):
    """Создает и форматирует pdf-таблицу"""
    data = make_list_of_lists_table(portfolio)

    style = TableStyle([('LINEBEFORE', (1, 0), (1, -1), LINE_WIDTH, LINE_COLOR),
                        ('LINEABOVE', (0, 1), (-1, 1), LINE_WIDTH, LINE_COLOR),
                        ('LINEABOVE', (0, -1), (-1, -1), LINE_WIDTH, LINE_COLOR),
                        ('ALIGN', (-2, 1), (-1, -1), 'RIGHT'),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTRE'),
                        ('FONTNAME', (0, -1), (-1, -1), BOLD_FONT)])

    table = Table(data=data, style=style)
    table.hAlign = 'LEFT'
    return table


def portfolio_structure_block(portfolio: Portfolio, canvas: Canvas, x: float, y: float, width: float, height: float):
    """Формирует блок pdf-файла с информацией о структуре портфеля

    В левой части располагается табличка структуры, а в правой части диаграмма
    """
    block_header = Paragraph('Portfolio Structure', BLOCK_HEADER_STYLE)
    table = make_pdf_table(portfolio)
    frame = Frame(x, y, width * LEFT_PART_OF_BLOCK, height,
                  leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=6,
                  showBoundary=0)
    frame.addFromList([block_header, table], canvas)
    image = make_plot(portfolio, width * (1 - LEFT_PART_OF_BLOCK), height)
    image.drawOn(canvas, x + width * LEFT_PART_OF_BLOCK, y)
