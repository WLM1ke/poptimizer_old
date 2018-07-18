from pathlib import Path
from shutil import copyfile

import pandas as pd
import pytest

from portfolio import Portfolio
from reporter import reporter

POSITIONS = dict(MSTT=44,
                 RTKMP=15,
                 MTSS=14,
                 AKRN=12,
                 MSRS=57,
                 UPRO=13,
                 PMSBP=48)
CASH = 32412
DATE_OLD = '2018-04-19'
DATE_NEW = '2018-05-07'


@pytest.fixture(scope='module', autouse=True)
def make_fake_data(tmpdir_factory):
    saved_data_path = reporter.REPORTS_DATA_PATH
    saved_pdf_path = reporter.REPORTS_PDF_PATH
    temp_dir = tmpdir_factory.mktemp('test_report')
    reporter.REPORTS_DATA_PATH = Path(temp_dir) / 'data'
    reporter.REPORTS_PDF_PATH = Path(temp_dir) / 'pdf'
    reporter.REPORTS_DATA_PATH.mkdir(parents=True)
    copyfile(Path(__file__).parent / 'data' / 'test.xlsx', reporter.REPORTS_DATA_PATH / 'test.xlsx')
    yield
    reporter.REPORTS_DATA_PATH = saved_data_path
    reporter.REPORTS_PDF_PATH = saved_pdf_path


def test_report():
    port = Portfolio(date=DATE_OLD,
                     cash=CASH,
                     positions=POSITIONS)
    reporter.report('test', port, dict(), 0)
    date = port.date
    pdf_path, xlsx_path = reporter.make_report_files_path('test', date)
    assert pdf_path.exists()
    assert xlsx_path.exists()


def test_report_new_month():
    port = Portfolio(date=DATE_NEW,
                     cash=CASH,
                     positions=POSITIONS)
    reporter.report('test', port, dict(WLMike=10000, Igor=-5000), 4321)
    df = reporter.read_data('test')
    date = port.date
    assert df.index[-1].date() == date
    assert df.loc[date, 'WLMike'] == pytest.approx(10000)
    assert df.loc[date, 'Igor'] == pytest.approx(-5000)
    assert df.loc[date, 'Value_WLMike'] == pytest.approx(387550.829708377)
    assert df.loc[date, 'Value_Igor'] == pytest.approx(4972.170292)
    assert df.loc[date, 'Value'] == pytest.approx(392523)
    assert df.loc[date, 'Dividends'] == pytest.approx(4321)


def test_report_no_dividends():
    copyfile(Path(__file__).parent / 'data' / 'test.xlsx', reporter.REPORTS_DATA_PATH / 'test.xlsx')
    port = Portfolio(date=DATE_NEW,
                     cash=CASH,
                     positions=POSITIONS)
    reporter.report('test', port, dict(WLMike=10000, Igor=-5000), 0)
    df = reporter.read_data('test')
    date = port.date
    assert df.index[-1].date() == date
    assert df.loc[date, 'WLMike'] == pytest.approx(10000)
    assert df.loc[date, 'Igor'] == pytest.approx(-5000)
    assert df.loc[date, 'Value_WLMike'] == pytest.approx(387550.829708377)
    assert df.loc[date, 'Value_Igor'] == pytest.approx(4972.170292)
    assert df.loc[date, 'Value'] == pytest.approx(392523)
    assert pd.isnull(df.loc[date, 'Dividends'])
