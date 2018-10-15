import copy

import pandas as pd
import pytest

from ml.returns import manager, model


def test_new_manager():
    positions = ('LSRG', 'VSMO', 'AKRN', 'GCHE', 'MTSS')
    date = pd.Timestamp('2018-10-12')
    data = manager.ReturnsMLDataManager(positions, date)
    assert data.value.params == model.ReturnsModel(positions, date).params
    assert data.value.positions == positions
    assert data.value.date == date


def test_manager_change_positions():
    positions = ('LSRG', 'VSMO', 'AKRN', 'GCHE', 'MTSS')
    date = pd.Timestamp('2018-10-12')
    data = manager.ReturnsMLDataManager(positions, date)
    assert data.value.params == model.ReturnsModel(positions, date).params
    assert data.value.positions == positions
    assert data.value.date == date


def test_manager_change_date():
    positions = ('LSRG', 'VSMO', 'MSRS', 'GCHE', 'MTSS')
    date = pd.Timestamp('2018-10-11')
    data = manager.ReturnsMLDataManager(positions, date)
    assert data.value.params == model.ReturnsModel(positions, date).params
    assert data.value.positions == positions
    assert data.value.date == date


def test_manager_change_params(monkeypatch):
    fake_params = copy.deepcopy(model.ReturnsModel.PARAMS)
    fake_params['data']['returns_lags'] += 1
    monkeypatch.setattr(model.ReturnsModel, 'PARAMS', fake_params)
    positions = ('LSRG', 'VSMO', 'MSRS', 'GCHE', 'MTSS')
    date = pd.Timestamp('2018-10-11')
    data = manager.ReturnsMLDataManager(positions, date)
    assert data.value.params == model.ReturnsModel(positions, date).params
    assert data.value.params['data']['returns_lags'] == fake_params['data']['returns_lags']
    assert data.value.positions == positions
    assert data.value.date == date


def test_download_update():
    positions = ('LSRG', 'VSMO', 'MSRS', 'GCHE', 'MTSS')
    date = pd.Timestamp('2018-10-11')
    with pytest.raises(NotImplementedError):
        manager.ReturnsMLDataManager(positions, date).download_update()
