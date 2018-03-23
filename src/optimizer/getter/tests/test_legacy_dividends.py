import pandas as pd
import pytest

from optimizer.getter import local_dividends


def test_get_legacy_dividends():
    df = local_dividends.get_legacy_dividends(['UPRO', 'RTKMP', 'MSTT', 'MAGN', 'LSRG'])
    assert df.index.equals(pd.Index([2012, 2013, 2014, 2015, 2016]))
    assert df.columns.equals(pd.Index(['UPRO', 'RTKMP', 'MSTT', 'MAGN', 'LSRG']))
    assert df.loc[2012, 'UPRO'] == pytest.approx(0.289541278733806)
    assert df.loc[2013, 'RTKMP'] == pytest.approx(4.848555414552)
    assert df.loc[2014, 'MSTT'] == pytest.approx(7.09)
    assert df.loc[2015, 'MAGN'] == pytest.approx(0.89)
    assert df.loc[2016, 'LSRG'] == pytest.approx(78)
