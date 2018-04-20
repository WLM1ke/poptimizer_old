"""Хранение истории стоимости портфеля и составление отчетов"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Frame

from portfolio_optimizer import Portfolio
from portfolio_optimizer.reporter import value_table
from portfolio_optimizer.settings import REPORTS_PATH

# Наименование файла отчета
REPORT_NAME = str(REPORTS_PATH / 'report.pdf')

# Наименование строки для мелких позиций
OTHER = 'OTHER'


def make_report(portfolio: Portfolio):
    """Формирует отчет"""
    canvas = Canvas(REPORT_NAME, pagesize=A4)
    table = value_table.make_table(portfolio)
    frame = Frame(inch, inch, 6 * inch, 9 * inch, showBoundary=1)
    frame.addFromList([table], canvas)
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
