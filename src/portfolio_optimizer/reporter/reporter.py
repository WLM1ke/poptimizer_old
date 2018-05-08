"""Хранение истории стоимости портфеля и составление отчетов"""

import pandas as pd

from portfolio_optimizer import Portfolio
from portfolio_optimizer.reporter.flow_and_dividends import flow_and_dividends_block
from portfolio_optimizer.reporter.pdf_style import blank_width, make_section_delimiter, make_header
from portfolio_optimizer.reporter.pdf_style import make_blank_report, left_margin, bottom_margin, blank_height
from portfolio_optimizer.reporter.portfolio_return import portfolio_return_block
from portfolio_optimizer.reporter.portfolio_structure import portfolio_structure_block
from portfolio_optimizer.settings import REPORTS_PATH

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


def make_files_path(report_name: str, date):
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
    pdf_path, xlsx_path = make_files_path(report_name, date)
    canvas = make_blank_report(pdf_path)
    make_header(canvas, date)
    # Верхний блок и разделитель за ним
    data = read_data('report')
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


if __name__ == '__main__':
    POSITIONS = dict(BANEP=200,
                     MFON=55,
                     SNGSP=235,
                     RTKM=0,
                     MAGN=0,
                     MSTT=4435,
                     KBTK=9,
                     MOEX=0,
                     RTKMP=1475 + 312 + 39,
                     NMTP=0,
                     TTLK=0,
                     LSRG=561 + 0 + 80,
                     LSNGP=81,
                     PRTK=70,
                     MTSS=749,
                     AKRN=795,
                     MRKC=0 + 0 + 36,
                     GAZP=0,
                     AFLT=0,
                     MSRS=699,
                     UPRO=1267,
                     PMSBP=1188 + 322 + 219,
                     CHMF=0,
                     GMKN=166 + 28,
                     VSMO=73,
                     RSTIP=87,
                     PHOR=0,
                     MRSB=0,
                     LKOH=123,
                     ENRU=319 + 148,
                     MVID=264 + 62)
    CASH = 596_156 + 470_259 + 481_849
    DATE = '2018-04-19'
    port = Portfolio(date=DATE,
                     cash=CASH,
                     positions=POSITIONS)
    make_report('report', port)
