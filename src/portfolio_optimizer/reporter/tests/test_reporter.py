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
    assert False
    date = PORTFOLIO.date
    with open(reporter.make_files_path('test', date)[0], 'rb') as file:
        result = file.read()
    with open(Path(__file__).parent / 'data' / f'{date}.pdf', 'rb') as file:
        test_case = file.read()
    # В конце файла содержатся данные, зависящие от даты создания
    assert result[:197442] == test_case[:197442]
