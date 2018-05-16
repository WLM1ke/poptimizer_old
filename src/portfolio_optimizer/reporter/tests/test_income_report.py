from pathlib import Path
from shutil import copyfile

import pytest

from portfolio_optimizer import local
from portfolio_optimizer.reporter import reporter
from portfolio_optimizer.reporter.income_report import get_investor_data, constant_prices_data, rescale_and_format, \
    income_report


@pytest.fixture(scope='module', autouse=True)
def make_fake_data(tmpdir_factory):
    saved_data_path = reporter.REPORTS_DATA_PATH
    temp_dir = tmpdir_factory.mktemp('test_income_report')
    reporter.REPORTS_DATA_PATH = Path(temp_dir) / 'data'
    reporter.REPORTS_DATA_PATH.mkdir(parents=True)
    copyfile(Path(__file__).parent / 'data' / 'test.xlsx', reporter.REPORTS_DATA_PATH / 'test.xlsx')
    yield
    reporter.REPORTS_DATA_PATH = saved_data_path


def test_get_investor_data():
    df = get_investor_data('test', 'Igor')
    assert df.shape == (13, 3)
    assert df.loc['2018-01-19', 'Inflow'] == pytest.approx(-6300)
    assert df.loc['2018-04-19', 'Value'] == pytest.approx(10094.11382)
    assert df.loc['2017-06-19', 'Dividends'] == pytest.approx(12.18696831)


def make_fake_cpi():
    """Тестовые сценарии подготовлены для данных инфляции на конец марта 2018 года"""
    cpi_data = local.cpi()

    def fake_cpi():
        return cpi_data.loc[:'2018-03-31']

    return fake_cpi


def test_constant_prices_data(monkeypatch):
    monkeypatch.setattr(local, 'cpi', make_fake_cpi())
    df = constant_prices_data('test', 'Igor')
    assert df.shape == (13, 3)
    assert df.loc['2018-01-19', 'Inflow'] == pytest.approx(-6351.166136)
    assert df.loc['2017-07-19', 'Value'] == pytest.approx(12875.75482)
    assert df.loc['2017-06-19', 'Dividends'] == pytest.approx(12.38775237)


def test_rescale_and_format():
    assert rescale_and_format(1234567, 1) == '1 235 000'
    assert rescale_and_format(1234567, 0.1) == '  123 000'


def test_income_report(monkeypatch, capsys):
    monkeypatch.setattr(local, 'cpi', make_fake_cpi())
    income_report('test', 'WLMike')
    captured_string = capsys.readouterr().out
    assert 'WLMike' in captured_string
    assert '1Y: Real Dividends =    28 000, Real Income =    85 000' in captured_string
    assert '1M: Real Dividends =     2 000, Real Income =     7 000' in captured_string
    assert '1W: Real Dividends =     1 000, Real Income =     2 000' in captured_string
