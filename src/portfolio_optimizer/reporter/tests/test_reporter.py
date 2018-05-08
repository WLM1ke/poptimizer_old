from pathlib import Path
from shutil import copyfile

import pytest

from portfolio_optimizer import Portfolio
from portfolio_optimizer.reporter import reporter

POSITIONS = dict(MSTT=44,
                 RTKMP=15,
                 MTSS=14,
                 AKRN=12,
                 MSRS=57,
                 UPRO=13,
                 PMSBP=48)
CASH = 32412
DATE = '2018-04-19'
PORTFOLIO = Portfolio(date=DATE,
                      cash=CASH,
                      positions=POSITIONS)


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


def test_make_report():
    reporter.make_report('test', PORTFOLIO)
    date = PORTFOLIO.date
    pdf_path, xlsx_path = reporter.make_files_path('test', date)
    assert pdf_path.exists()
    assert xlsx_path.exists()
