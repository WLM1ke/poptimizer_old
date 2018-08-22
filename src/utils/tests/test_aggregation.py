import pandas as pd

from utils.aggregation import monthly_aggregator, monthly_aggregation_func, quarterly_aggregator, \
    quarterly_aggregation_func
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


def test_quarterly_aggregator():
    assert quarterly_aggregator(pd.Timestamp('2018-08-13'), pd.Timestamp('2011-03-11')) == pd.Timestamp('2018-09-11')
    assert quarterly_aggregator(pd.Timestamp('2014-09-14'), pd.Timestamp('2014-09-13')) == pd.Timestamp('2014-12-13')
    assert quarterly_aggregator(pd.Timestamp('2017-02-28'), pd.Timestamp('2014-01-31')) == pd.Timestamp('2017-04-30')
    assert quarterly_aggregator(pd.Timestamp('2017-02-28'), pd.Timestamp('2014-07-31')) == pd.Timestamp('2017-04-30')
    assert quarterly_aggregator(pd.Timestamp('2011-10-31'), pd.Timestamp('2013-02-28')) == pd.Timestamp('2011-11-28')
    assert quarterly_aggregator(pd.Timestamp('2011-01-31'), pd.Timestamp('2013-02-28')) == pd.Timestamp('2011-02-28')
    assert quarterly_aggregator(pd.Timestamp('2011-10-31'), pd.Timestamp('2012-02-29')) == pd.Timestamp('2011-11-29')
    assert quarterly_aggregator(pd.Timestamp('2011-01-31'), pd.Timestamp('2012-02-29')) == pd.Timestamp('2011-02-28')
    assert quarterly_aggregator(pd.Timestamp('2012-12-31'), pd.Timestamp('2012-02-29')) == pd.Timestamp('2013-02-28')


def test_quarterly_aggregation_func():
    result = quarterly_aggregation_func(pd.Timestamp('2019-04-11'))
    assert callable(result)
    assert result(pd.Timestamp('2018-08-13')) == pd.Timestamp('2018-10-11')
    assert result(pd.Timestamp('2016-03-11')) == pd.Timestamp('2016-04-11')
    assert result(pd.Timestamp('2014-01-31')) == pd.Timestamp('2014-04-11')
    assert result(pd.Timestamp('2012-02-28')) == pd.Timestamp('2012-04-11')
    assert result(pd.Timestamp('2015-09-13')) == pd.Timestamp('2015-10-11')


def test_monthly_aggregator():
    assert monthly_aggregator(pd.Timestamp('2018-08-13'), pd.Timestamp('2011-03-11')) == pd.Timestamp('2018-09-11')
    assert monthly_aggregator(pd.Timestamp('2019-03-11'), pd.Timestamp('2014-09-13')) == pd.Timestamp('2019-03-13')
    assert monthly_aggregator(pd.Timestamp('2017-02-28'), pd.Timestamp('2014-01-31')) == pd.Timestamp('2017-02-28')
    assert monthly_aggregator(pd.Timestamp('2017-02-28'), pd.Timestamp('2014-07-31')) == pd.Timestamp('2017-02-28')
    assert monthly_aggregator(pd.Timestamp('2011-10-31'), pd.Timestamp('2013-02-28')) == pd.Timestamp('2011-11-28')
    assert monthly_aggregator(pd.Timestamp('2011-01-31'), pd.Timestamp('2013-02-28')) == pd.Timestamp('2011-02-28')
    assert monthly_aggregator(pd.Timestamp('2011-10-31'), pd.Timestamp('2012-02-29')) == pd.Timestamp('2011-11-29')
    assert monthly_aggregator(pd.Timestamp('2011-01-31'), pd.Timestamp('2012-02-29')) == pd.Timestamp('2011-02-28')
    assert monthly_aggregator(pd.Timestamp('2012-12-31'), pd.Timestamp('2012-02-29')) == pd.Timestamp('2013-01-29')


def test_monthly_aggregation_func():
    result = monthly_aggregation_func(pd.Timestamp('2019-03-11'))
    assert callable(result)
    assert result(pd.Timestamp('2018-08-13')) == pd.Timestamp('2018-09-11')
    assert result(pd.Timestamp('2016-03-11')) == pd.Timestamp('2016-03-11')
    assert result(pd.Timestamp('2014-01-31')) == pd.Timestamp('2014-02-11')
    assert result(pd.Timestamp('2012-02-28')) == pd.Timestamp('2012-03-11')
    assert result(pd.Timestamp('2015-09-13')) == pd.Timestamp('2015-10-11')
