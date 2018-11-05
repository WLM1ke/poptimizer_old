import pandas as pd

from local.dividends import smart_lab_ru
from local.dividends.dividends_status import dividends_status, smart_lab_status


def test_smart_lab_status(monkeypatch):
    data = {'TICKER': ['PIKK', 'ALRS', 'CHMF', 'MTSS', 'NLMK'], 'DIVIDENDS': [22.0, 5.930, 45.940, 2.600, 5.0]}
    index = [pd.Timestamp('2018-09-04'),
             pd.Timestamp('2018-10-16'),
             pd.Timestamp('2018-09-25'),
             pd.Timestamp('2018-10-09'),
             pd.Timestamp('2018-10-12')]
    fake_df = pd.DataFrame(data=data, index=index)
    monkeypatch.setattr(smart_lab_ru, 'dividends_smart_lab', lambda: fake_df)
    result = smart_lab_status(tuple(['PIKK', 'CHMF']))
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert len(result[0]) == 1
    assert result[0][0] == 'PIKK'
    assert len(result[1]) == 2
    assert result[1][0] == 'ALRS'
    assert result[1][1] == 'NLMK'


def test_dividends_status(capsys):
    result = dividends_status('ENRU')
    captured = capsys.readouterr()

    assert isinstance(result, list)
    assert len(result) == 3

    assert result[0].shape >= (4, 3)
    assert result[0].iloc[0, 2] == ''
    assert result[0].iloc[3, 2] == 'ERROR'
    assert 'СРАВНЕНИЕ ОСНОВНЫХ ДАННЫХ С dividends_dohod' in captured.out

    assert result[1].shape >= (4, 3)
    assert result[1].iloc[2, 2] == ''
    assert result[1].iloc[1, 2] == 'ERROR'
    assert 'СРАВНЕНИЕ ОСНОВНЫХ ДАННЫХ С dividends_conomy' in captured.out

    assert 'СРАВНЕНИЕ ОСНОВНЫХ ДАННЫХ С dividends_smart_lab' in captured.out


def test_dividends_status_no_table(capsys):
    dividends_status('NKHP')
    captured = capsys.readouterr()
    assert 'На странице http://www.dohod.ru/ik/analytics/dividend/nkhp нет таблицы с дивидендами.' in captured.out
