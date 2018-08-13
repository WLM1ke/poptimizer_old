import pandas as pd

from utils.aggregation import yearly_aggregator, yearly_aggregation_func


def test_yearly_aggregator():
    assert yearly_aggregator(pd.Timestamp('2018-08-13'), pd.Timestamp('2011-03-11')) == pd.Timestamp('2019-03-11')
    assert yearly_aggregator(pd.Timestamp('2019-03-11'), pd.Timestamp('2014-09-13')) == pd.Timestamp('2019-09-13')
    assert yearly_aggregator(pd.Timestamp('2017-02-28'), pd.Timestamp('2014-01-31')) == pd.Timestamp('2018-01-31')
    assert yearly_aggregator(pd.Timestamp('2017-02-28'), pd.Timestamp('2014-07-31')) == pd.Timestamp('2017-07-31')
    assert yearly_aggregator(pd.Timestamp('2011-10-31'), pd.Timestamp('2013-02-28')) == pd.Timestamp('2012-02-28')
    assert yearly_aggregator(pd.Timestamp('2011-01-31'), pd.Timestamp('2013-02-28')) == pd.Timestamp('2011-02-28')
    assert yearly_aggregator(pd.Timestamp('2011-10-31'), pd.Timestamp('2012-02-29')) == pd.Timestamp('2012-02-29')
    assert yearly_aggregator(pd.Timestamp('2011-01-31'), pd.Timestamp('2012-02-29')) == pd.Timestamp('2011-02-28')


def test_yearly_aggregation_func():
    result = yearly_aggregation_func(pd.Timestamp('2019-03-11'))
    assert callable(result)
    assert result(pd.Timestamp('2018-08-13')) == pd.Timestamp('2019-03-11')
    assert result(pd.Timestamp('2016-03-11')) == pd.Timestamp('2016-03-11')
    assert result(pd.Timestamp('2014-01-31')) == pd.Timestamp('2014-03-11')
    assert result(pd.Timestamp('2012-02-28')) == pd.Timestamp('2012-03-11')
    assert result(pd.Timestamp('2015-09-13')) == pd.Timestamp('2016-03-11')
