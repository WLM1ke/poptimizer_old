"""Хранение истории стоимости портфеля и составление отчетов"""

import numpy as np
import pandas as pd

from portfolio_optimizer import Portfolio
from portfolio_optimizer.reporter.flow_and_dividends import flow_and_dividends_block
from portfolio_optimizer.reporter.pdf_style import blank_width, make_section_delimiter, make_header
from portfolio_optimizer.reporter.pdf_style import make_blank_report, left_margin, bottom_margin, blank_height
from portfolio_optimizer.reporter.portfolio_return import portfolio_return_block, get_investors_names
from portfolio_optimizer.reporter.portfolio_structure import portfolio_structure_block
from portfolio_optimizer.settings import REPORTS_PATH, PORTFOLIO

# Каталог с данными
REPORTS_DATA_PATH = REPORTS_PATH / 'data'

# Каталог с pdf-отчетами
REPORTS_PDF_PATH = REPORTS_PATH / 'pdf'

# Лист с данными
SHEET_NAME = 'Data'

# Положение блоков относительно нижнего поля
FIRST_BLOCK_POSITION = blank_height() * 0.76
SECOND_BLOCK_POSITION = blank_height() * 0.38
THIRD_BLOCK_POSITION = blank_height() * 0


def read_data(report_name: str):
    """Читает исходные данные по стоимости портфеля из файла"""
    data = pd.read_excel(REPORTS_DATA_PATH / f'{report_name}.xlsx',
                         sheet_name=SHEET_NAME,
                         header=0,
                         index_col=0,
                         converters={'Date': pd.to_datetime})
    return data


def update_data(report_name: str, date, value: float, inflows: dict, dividends: float):
    """Обновляет файл с данными статистики изменения стоимости портфеля

    inflow - словарь с имен инвесторов и внесенных ими средств за период
    """
    df = read_data(report_name)
    date = pd.to_datetime(date)
    next_month_flag = df.index[-1] + pd.DateOffset(months=1, day=1) <= date
    if (not next_month_flag) and (date not in df.index):
        raise ValueError(f'Дата {date} отсутствует в статистике {df.index}')
    elif next_month_flag:
        df.loc[date, 'Value'] = value
        if dividends == 0:
            df.loc[date, 'Dividends'] = np.nan
        else:
            df.loc[date, 'Dividends'] = dividends
        total_inflow = 0
        for investor, inflow in inflows.items():
            if investor not in df.columns:
                raise ValueError(f'Неверное имя инвестора - {investor}')
            df.loc[date, investor] = inflow
            total_inflow += inflow
        portfolio_return = (value - total_inflow) / df['Value'].iloc[-2]
        investors = get_investors_names(df)
        value_labels = 'Value_' + investors
        pre_inflow_value = df[value_labels].iloc[-2] * portfolio_return
        df.loc[date, value_labels] = pre_inflow_value.add(df.loc[date, investors].values, fill_value=0)
        df.to_excel(REPORTS_DATA_PATH / f'{report_name}.xlsx', SHEET_NAME)


def make_report_files_path(report_name: str, date):
    """Прокладывает путь и возвращает путь к файлу pdf-отчета и xlsx-отчета"""
    subfolder_name = f'{report_name} {date}'
    report_folder = REPORTS_PDF_PATH / f'{subfolder_name}'
    if not report_folder.exists():
        report_folder.mkdir(parents=True)
    return report_folder / f'{date}.pdf', report_folder / f'{date}.xlsx'


def make_report(report_name: str, portfolio: Portfolio):
    """Формирует отчет из pdf-файла и исходных xlsx-данных

    Отчет сохраняется в REPORTS_PDF_PATH. Для каждого отчета создается папка с наименованием и датой, куда
    помещаются pdf и xlsx
    """
    # pdf-файл с заголовком в верхнем колонтитуле
    date = portfolio.date
    pdf_path, xlsx_path = make_report_files_path(report_name, date)
    canvas = make_blank_report(pdf_path)
    make_header(canvas, date)
    # Верхний блок и разделитель за ним
    data = read_data(report_name)
    flow_and_dividends_block(data[-61:], canvas,
                             left_margin(), bottom_margin() + FIRST_BLOCK_POSITION,
                             blank_width(), blank_height() - FIRST_BLOCK_POSITION)
    make_section_delimiter(canvas, bottom_margin() + FIRST_BLOCK_POSITION)
    # Второй блок и разделитель за ним
    portfolio_return_block(data[-61:], canvas,
                           left_margin(), bottom_margin() + SECOND_BLOCK_POSITION,
                           blank_width(), FIRST_BLOCK_POSITION - SECOND_BLOCK_POSITION)
    make_section_delimiter(canvas, bottom_margin() + SECOND_BLOCK_POSITION)
    # Нижний блок
    portfolio_structure_block(portfolio, canvas,
                              left_margin(), bottom_margin() + THIRD_BLOCK_POSITION,
                              blank_width(), SECOND_BLOCK_POSITION - THIRD_BLOCK_POSITION)
    # Сохранение pdf-отчета и xlsx-данных
    canvas.save()
    data.to_excel(xlsx_path, SHEET_NAME)


def report(report_name: str, portfolio: Portfolio, inflows: dict, dividends: float):
    """Обновляет данные статистики стоимости портфеля и создает отчет"""
    update_data(report_name, portfolio.date, portfolio.value[PORTFOLIO], inflows, dividends)
    make_report(report_name, portfolio)
