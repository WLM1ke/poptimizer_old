from pathlib import Path
from shutil import copyfile

import matplotlib.pyplot as plt
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
    # В конце файла содержатся мета данные, зависящие от даты создания - проверятся совпадение основной части файла
    start_of_meta = 197442
    with open(reporter.make_files_path('test', date)[0], 'rb') as file:
        result = file.read(start_of_meta)
    with open(Path(__file__).parent / 'data' / f'{date}.pdf', 'rb') as file:
        test_case = file.read(start_of_meta)
    assert result == test_case
    assert False
    # Travis зависает, если не закрыть все окна
    plt.close('all')
