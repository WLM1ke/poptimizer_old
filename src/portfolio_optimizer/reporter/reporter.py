"""Хранение истории стоимости портфеля и составление отчетов"""

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Frame

from portfolio_optimizer import Portfolio
from portfolio_optimizer.reporter import value_table
from portfolio_optimizer.settings import REPORTS_PATH

# Наименование файла отчета
REPORT_NAME = str(REPORTS_PATH / 'report.pdf')

# Каталог с данными
REPORTS_DATA_PATH = REPORTS_PATH / 'data'

# Лис с данными
SHEET_NAME = 'Data'


def read_data(report_name: str):
    data = pd.read_excel(REPORTS_DATA_PATH / f'{report_name}.xlsx',
                         sheet_name=SHEET_NAME,
                         header=0,
                         index_col=0,
                         converters={'Date': pd.to_datetime})
    return data


def make_report(report_name: str, portfolio: Portfolio, month_to_report: int = 60):
    """Формирует отчет"""
    page_width, page_height = A4
    margin = 1.5 * cm
    blank_width = page_width - 2 * margin
    blank_height = page_height - 2 * margin

    frame_ul = Frame(margin, margin + blank_height / 2, blank_width / 2, blank_height / 2, showBoundary=1)
    frame_ur = Frame(margin + blank_width / 2, margin + blank_height / 2, blank_width / 2, blank_height / 2,
                     showBoundary=1)
    frame_bl = Frame(margin, margin, blank_width / 2, blank_height / 2, showBoundary=1)
    frame_br = Frame(margin + blank_width / 2, margin, blank_width / 2, blank_height / 2, showBoundary=1)

    canvas = Canvas(REPORT_NAME, pagesize=(page_width, page_height))
    table = value_table.make_table(portfolio)
    table2 = value_table.make_table(portfolio)

    frame_ul.addFromList([table, table2], canvas)
    frame_ur.addFromList([table], canvas)
    frame_bl.addFromList([table], canvas)
    frame_br.addFromList([table], canvas)

    canvas.save()


# TODO: сделать прокладывание пути


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
    make_report(port)
