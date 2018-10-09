import collections
import numpy as np
import pandas as pd
import pytest

from ml.returns.cases import ReturnsCasesIterator


def test_iterable():
    data = ReturnsCasesIterator(('LSNGP', 'MTSS', 'PRTK', 'TTLK', 'AKRN'), pd.Timestamp('2018-10-08'), 9, 3)
    assert isinstance(data, collections.Iterable)
    iterator = iter(data)
    next(iterator)
    first_cases = next(iterator)
    assert isinstance(first_cases, pd.DataFrame)
    assert first_cases.shape == (1, 7)
    assert first_cases.iloc[0, 0] == 'MTSS'
    assert first_cases.iloc[0, 1] == pytest.approx(0.08320843735418346)
    assert first_cases.iloc[0, 2] == pytest.approx(-0.19106213084685936)
    assert first_cases.iloc[0, 3] == pytest.approx(-0.421300911815176)
    assert first_cases.iloc[0, -1] == pytest.approx(1.5118022699045564)


def test_cases_no_labels():
    data = ReturnsCasesIterator(('LSNGP', 'MTSS', 'PRTK', 'GMKN', 'AKRN'), pd.Timestamp('2018-10-08'), 9, 2)
    cases = data.cases(pd.Timestamp('2014-07-08'), False)
    assert isinstance(cases, pd.DataFrame)
    assert cases.shape == (1, 6)
    assert cases.iloc[0, 0] == 'MTSS'
    assert cases.iloc[0, 1] == pytest.approx(0.08764091492481606)
    assert cases.iloc[0, 2] == pytest.approx(0.17215988641016763)
    assert cases.iloc[0, -2] == pytest.approx(-0.4443653054433533)
    assert np.isnan(cases.iloc[0, -1])
