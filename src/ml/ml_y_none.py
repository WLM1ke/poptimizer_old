"""Тестирование ML на основании данных о годовых не пересекающихся дивидендах"""
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression

from ml.cases_non_overlapping import cases_non_overlapping
from ml.cross_val_analysis import RegressionCase, draw_cross_val_analysis
from ml.current_predictor import AverageRegressor

if __name__ == '__main__':
    POSITIONS = dict(AKRN=563,
                     BANEP=488 + 19,
                     CHMF=234 + 28 + 8,
                     GMKN=146 + 29,
                     LKOH=340 + 18,
                     LSNGP=18,
                     LSRG=2346 + 64 + 80,
                     MSRS=128 + 117,
                     MSTT=1823,
                     MTSS=1383 + 36,
                     PMSBP=2873 + 418 + 336,
                     RTKMP=1726 + 382 + 99,
                     SNGSP=318,
                     TTLK=234,
                     UPRO=986 + 0 + 9,
                     VSMO=102,
                     PRTK=0,
                     MVID=0,
                     IRKT=0,
                     TATNP=0)
    DATE = '2018-08-17'
    data_ = cases_non_overlapping(tuple(key for key in POSITIONS), pd.Timestamp(DATE), 5)

    regressions_ = [RegressionCase(DummyRegressor(),
                                   None,
                                   None),
                    RegressionCase(AverageRegressor(),
                                   None,
                                   None),
                    RegressionCase(LinearRegression(),
                                   None,
                                   None)]

    draw_cross_val_analysis(regressions_, data_)
