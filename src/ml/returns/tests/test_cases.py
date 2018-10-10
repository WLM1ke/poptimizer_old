import catboost
import collections
import numpy as np
import pandas as pd
import pytest

from ml.returns.cases import ReturnsCasesIterator, learn_pool, predict_pool
from web.labels import TICKER


def test_iterable():
    data = ReturnsCasesIterator(('LSNGP', 'MTSS', 'PRTK', 'TTLK', 'AKRN'), pd.Timestamp('2018-10-08'), 9, 3)
    assert isinstance(data, collections.Iterable)
    iterator = iter(data)
    first_cases = next(iterator)
    assert isinstance(first_cases, pd.DataFrame)
    assert first_cases.shape == (1, 7)
    assert first_cases.iloc[0, 0] == 'MTSS'
    assert first_cases.iloc[0, 1] == pytest.approx(0.08320843735418346)
    assert first_cases.iloc[0, 2] == pytest.approx(-0.19106213084685936)
    assert first_cases.iloc[0, 3] == pytest.approx(-0.6123630426620353)
    assert first_cases.iloc[0, -1] == pytest.approx(1.3207401390576972)


def test_cases_no_labels():
    data = ReturnsCasesIterator(('LSNGP', 'MTSS', 'PRTK', 'GMKN', 'AKRN'), pd.Timestamp('2018-10-08'), 9, 2)
    cases = data.cases(pd.Timestamp('2014-07-08'), False)
    assert isinstance(cases, pd.DataFrame)
    assert cases.shape == (1, 6)
    assert cases.iloc[0, 0] == 'MTSS'
    assert cases.iloc[0, 1] == pytest.approx(0.08764091492481606)
    assert cases.iloc[0, 2] == pytest.approx(0.17215988641016763)
    assert cases.iloc[0, -2] == pytest.approx(-0.2722054190331857)
    assert np.isnan(cases.iloc[0, -1])


def test_pools():
    learn = learn_pool(('LSNGP', 'MTSS', 'VSMO', 'GMKN', 'AKRN'), pd.Timestamp('2018-10-09'), 10, 4)
    predict = predict_pool(('LSNGP', 'MTSS', 'VSMO', 'GMKN', 'AKRN'), pd.Timestamp('2018-10-09'), 10, 4)

    assert isinstance(learn, catboost.Pool)
    assert isinstance(predict, catboost.Pool)

    assert learn.num_col() == predict.num_col() == 7

    assert learn.num_row() == (64 - 22) * 4 + 64 - 11
    assert predict.num_row() == 5

    assert learn.get_cat_feature_indices() == [0]
    assert predict.get_cat_feature_indices() == [0]

    assert learn.get_feature_names() == [TICKER, 'std', 'mean'] + [f'lag - {i}' for i in range(4, 0, -1)]
    assert predict.get_feature_names() == [TICKER, 'std', 'mean'] + [f'lag - {i}' for i in range(4, 0, -1)]

    features = learn.get_features()

    assert features[0][1] == pytest.approx(0.0938999354839325)
    assert features[0][2] == pytest.approx(0.04971304163336754)
    assert features[0][5] == pytest.approx(-0.03501853719353676)
    assert learn.get_label()[0] == pytest.approx(1.0595999956130981)

    assert features[-1][1] == pytest.approx(0.05029456689953804)
    assert features[-1][2] == pytest.approx(0.4745929539203644)
    assert features[-1][5] == pytest.approx(0.2619769871234894)
    assert learn.get_label()[-1] == pytest.approx(0.5663775205612183)

    features = predict.get_features()

    assert features[0][1] == pytest.approx(0.10742760449647903)
    assert features[1][2] == pytest.approx(0.10586801171302795)
    assert features[2][3] == pytest.approx(-0.7268054485321045)
    assert features[3][4] == pytest.approx(-0.17948931455612183)
    assert features[4][5] == pytest.approx(0.015230 / 0.047723)
    assert predict.get_label() is None
