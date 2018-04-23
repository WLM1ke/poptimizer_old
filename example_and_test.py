"""Пример использования на основе реалистичного портфеля и тест скорости исполнения"""

import cProfile
import pstats

from portfolio_optimizer import Optimizer
from portfolio_optimizer import Portfolio

# Идеи для добавления в анализ
# HYDR
# MTLRP
# RASP
# OGKB
# RASP
# AFKS
# TGKA
# TGKB

POSITIONS = dict(BANEP=200,
                 MFON=55,
                 SNGSP=235,
                 RTKM=0,
                 MAGN=0,
                 MSTT=4435,
                 KBTK=9,
                 MOEX=0,
                 RTKMP=1504 + 382 + 67,
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
                 PMSBP=1683 + 322 + 219,
                 CHMF=0,
                 GMKN=166 + 28,
                 VSMO=73,
                 RSTIP=87,
                 PHOR=0,
                 MRSB=0,
                 LKOH=123,
                 ENRU=319 + 148,
                 MVID=264 + 62)
CASH = 22_412 + 37_052 + 308_463
DATE = '2018-04-20'
VALUE = None


def trading():
    """Распечатка всей аналитики, необходимой для управления портфелем"""
    port = Portfolio(date=DATE,
                     cash=CASH,
                     positions=POSITIONS,
                     value=VALUE)
    optimizer = Optimizer(port)
    print(optimizer.portfolio)
    print(optimizer.dividends_metrics)
    print(optimizer.returns_metrics)
    print(optimizer)


def speed_test():
    """Функция тестирования скорости

    Используется реалистичный портфель и комплексные функции распечатки метрик портфеля
    """
    pr = cProfile.Profile()
    pr.enable()

    trading()

    pr.disable()
    ps = pstats.Stats(pr).sort_stats('cumulative')
    ps.print_stats()


if __name__ == '__main__':
    trading()
