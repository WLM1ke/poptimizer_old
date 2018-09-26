import copy

import pandas as pd
import pytest

from ml.dividends import manager
from ml.dividends import model


def test_manager_first_time():
    positions = tuple(['MSTT', 'MVID', 'CHMF', 'MTSS', 'PMSBP'])
    date = pd.Timestamp('2018-09-06')
    data = manager.DividendsMLDataManager(positions, date)
    assert data.value.params == model.DividendsML(positions, date).params


def test_manager_second_time():
    positions = tuple(['MSTT', 'MVID', 'CHMF', 'MTSS', 'PMSBP'])
    date = pd.Timestamp('2018-09-06')
    data = manager.DividendsMLDataManager(positions, date)
    assert data.value.params == model.DividendsML(positions, date).params


def test_manager_change_date():
    positions = tuple(['MSTT', 'MVID', 'CHMF', 'MTSS', 'PMSBP'])
    date = pd.Timestamp('2018-09-05')
    data = manager.DividendsMLDataManager(positions, date)
    assert data.value.params == model.DividendsML(positions, date).params


def test_manager_change_positions():
    positions = tuple(['PRTK', 'MVID', 'CHMF', 'MTSS', 'PMSBP'])
    date = pd.Timestamp('2018-09-06')
    data = manager.DividendsMLDataManager(positions, date)
    assert data.value.params == model.DividendsML(positions, date).params


def test_manager_change_params(monkeypatch):
    fake_params = copy.deepcopy(model.PARAMS)
    fake_params['data']['lags_range'] = model.PARAMS['data']['lags_range'] + 1
    test_lags = model.PARAMS['data']['lags_range'] + 1
    monkeypatch.setattr(model, 'PARAMS', fake_params)
    positions = tuple(['PRTK', 'MVID', 'CHMF', 'MTSS', 'PMSBP'])
    date = pd.Timestamp('2018-09-06')
    data = manager.DividendsMLDataManager(positions, date)
    assert data.value.params['data']['lags_range'] == test_lags
    assert data.value.params == model.DividendsML(positions, date).params


def test_download_update():
    positions = tuple(['PRTK', 'MVID', 'CHMF', 'MTSS', 'PMSBP'])
    date = pd.Timestamp('2018-09-06')
    with pytest.raises(NotImplementedError):
        manager.DividendsMLDataManager(positions, date).download_update()
