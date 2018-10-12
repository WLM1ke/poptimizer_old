import copy

import hyperopt
import pandas as pd

from ml.returns import model


def test_ew_lags(monkeypatch):
    monkeypatch.setattr(model, 'EW_LAGS_RANGE', 1)
    params = {'data': {'ew_lags': 10}}
    assert model.ew_lags(params) == (5, 20)
    assert model.ew_lags(params, 0.9) == (10 / 1.9, 19)


def test_returns_lags(monkeypatch):
    monkeypatch.setattr(model, 'MAX_RETURNS_LAGS', 9)
    assert model.returns_lags() == list(range(10))


def test_make_data_space():
    returns = model.ReturnsModel(('CHMF', 'MSTT', 'RTKMP', 'UPRO', 'FEES'), pd.Timestamp('2018-10-11'))
    space = returns._make_data_space()
    assert isinstance(space, dict)
    assert len(space) == 2
    assert isinstance(space['ew_lags'], hyperopt.pyll.Apply)
    assert isinstance(space['returns_lags'], hyperopt.pyll.Apply)


def test_check_data_space_bounds(capsys):
    returns = model.ReturnsModel(('CHMF', 'MSTT', 'RTKMP', 'UPRO', 'FEES'), pd.Timestamp('2018-10-11'))
    returns._check_data_space_bounds(model.PARAMS)
    captured = capsys.readouterr()
    assert captured.out == ''


def test_check_data_space_bounds_upper(capsys):
    returns = model.ReturnsModel(('CHMF', 'MSTT', 'RTKMP', 'UPRO', 'FEES'), pd.Timestamp('2018-10-11'))
    params = copy.deepcopy(model.PARAMS)
    params['data']['ew_lags'] *= 1 + model.EW_LAGS_RANGE * 0.91
    params['data']['returns_lags'] = model.MAX_RETURNS_LAGS
    returns._check_data_space_bounds(params)
    captured = capsys.readouterr()
    assert 'Необходимо увеличить EW_LAGS_RANGE до' in captured.out
    assert 'Необходимо увеличить MAX_RETURNS_LAGS до' in captured.out


def test_check_data_space_bounds_lower(capsys):
    returns = model.ReturnsModel(('CHMF', 'MSTT', 'RTKMP', 'UPRO', 'FEES'), pd.Timestamp('2018-10-11'))
    params = copy.deepcopy(model.PARAMS)
    params['data']['ew_lags'] /= 1 + model.EW_LAGS_RANGE * 0.91
    returns._check_data_space_bounds(params)
    captured = capsys.readouterr()
    assert 'Необходимо увеличить EW_LAGS_RANGE до' in captured.out
    assert 'Необходимо увеличить MAX_RETURNS_LAGS до' not in captured.out


def test_prediction_mean(monkeypatch):
    params = {'data': {'ew_lags': 12.166882847847372,
                       'returns_lags': 5},
              'model': {'bagging_temperature': 1.5889359773128047,
                        'depth': 2,
                        'ignored_features': (),
                        'l2_leaf_reg': 3.0691833972589424,
                        'learning_rate': 0.04230361495762283,
                        'one_hot_max_size': 2,
                        'random_strength': 3.6085599262888683}}
    monkeypatch.setattr(model.ReturnsModel, 'PARAMS', params)
    returns = model.ReturnsModel(('MSRS', 'MSTT', 'RTKMP', 'UPRO', 'FEES'), pd.Timestamp('2018-10-11')).prediction_mean
    assert isinstance(returns, pd.Series)
    assert len(returns) == 5
    assert returns.index.tolist() == ['MSRS', 'MSTT', 'RTKMP', 'UPRO', 'FEES']
    assert returns['MSRS'] == 0.0018521857721484048
    assert returns['MSTT'] == 0.004415906411386809
    assert returns['RTKMP'] == 0.002905142786419567
    assert returns['UPRO'] == 0.0028195209196578627
    assert returns['FEES'] == 0.0037373919332427726


def test_prediction_std(monkeypatch):
    params = {'data': {'ew_lags': 12.166882847847372,
                       'returns_lags': 5},
              'model': {'bagging_temperature': 1.5889359773128047,
                        'depth': 2,
                        'ignored_features': (),
                        'l2_leaf_reg': 3.0691833972589424,
                        'learning_rate': 0.04230361495762283,
                        'one_hot_max_size': 2,
                        'random_strength': 3.6085599262888683}}
    monkeypatch.setattr(model.ReturnsModel, 'PARAMS', params)
    std = model.ReturnsModel(('MSRS', 'RTKM', 'RTKMP', 'UPRO', 'FEES'), pd.Timestamp('2018-10-11')).prediction_std
    assert isinstance(std, pd.Series)
    assert len(std) == 5
    assert std.index.tolist() == ['MSRS', 'RTKM', 'RTKMP', 'UPRO', 'FEES']
    assert std['MSRS'] == 0.049892858163254374
    assert std['RTKM'] == 0.04798205289008257
    assert std['RTKMP'] == 0.03734821638483238
    assert std['UPRO'] == 0.046223684807991286
    assert std['FEES'] == 0.08119363794137813
