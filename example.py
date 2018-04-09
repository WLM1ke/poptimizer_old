from portfolio_optimizer.optimizer import Optimizer
from portfolio_optimizer.portfolio import Portfolio

pos = dict(BANEP=0,
           MFON=55,
           SNGSP=31,
           RTKM=0,
           MAGN=0,
           MSTT=4650,
           KBTK=9,
           MOEX=0,
           RTKMP=1475 + 312 + 39,
           NMTP=0,
           TTLK=0,
           LSRG=561 + 0 + 80,
           LSNGP=81,
           PRTK=101 + 0 + 18,
           MTSS=749,
           AKRN=795,
           MRKC=343,
           GAZP=0,
           AFLT=5,
           MSRS=699,
           UPRO=1267,
           PMSBP=450 + 232,
           CHMF=15 + 0 + 40,
           GMKN=166 + 57,
           VSMO=133 + 12,
           RSTIP=238 + 27,
           PHOR=0,
           MRSB=23,
           LKOH=123,
           ENRU=319 + 148,
           MVID=264 + 62)
port = Portfolio(date='2018-04-06',
                 cash=0 + 2749.64 + 4330.3,
                 positions=pos)
optimizer = Optimizer(port)
print(optimizer)
