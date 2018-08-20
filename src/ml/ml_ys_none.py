"""Тестирование ML на основании данных о годовых не пересекающихся дивидендах нормированных по СКО"""
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.svm import LinearSVR

from ml.cases_non_overlapping import cases_non_overlapping, Data
from ml.cross_val_analysis import RegressionCase, SEED, draw_cross_val_analysis
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
    x, y, groups = data_
    std = x.std(axis=1)
    y = y.div(std, axis=0)
    x = x.div(std, axis=0)
    data_ = Data(x, y, groups)

    regressions_ = [RegressionCase(AverageRegressor(),
                                   None,
                                   None),
                    RegressionCase(Ridge(alpha=40, random_state=SEED),
                                   'alpha',
                                   [10, 20, 40, 80, 160]),
                    RegressionCase(LinearSVR(epsilon=0.30, C=0.02, random_state=SEED),
                                   'C',
                                   [0.005, 0.01, 0.02, 0.04, 0.08])]
    clf = Ridge(alpha=40, random_state=SEED)
    clf.fit(x, y)
    print(clf.coef_, clf.coef_.sum())
    print(clf.intercept_)

    clf = LinearSVR(epsilon=0.30, C=0.02, random_state=SEED)
    clf.fit(x, y)
    print(clf.coef_, clf.coef_.sum())
    print(clf.intercept_)

    draw_cross_val_analysis(regressions_, data_)
