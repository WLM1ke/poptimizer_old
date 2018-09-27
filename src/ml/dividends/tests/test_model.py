import pandas as pd
import pytest

import ml.hyper
from ml.dividends import hyper
from ml.dividends import model
from utils.aggregation import Freq

PARAMS = {'data': {'freq': Freq.yearly,
                   'lags_range': 1},
          'model': {'bagging_temperature': 1.3463876077482095,
                    'depth': 3,
                    'l2_leaf_reg': 1.8578444629373057,
                    'learning_rate': 0.09300426944876264,
                    'one_hot_max_size': 2,
                    'random_strength': 1.0464151963029267}}

SPACE = {
    'data': {'freq': ml.hyper.make_choice_space('freq', Freq),
             'lags_range': ml.hyper.make_choice_space('lags_range', 3)},
    'model': {'one_hot_max_size': ml.hyper.make_choice_space('one_hot_max_size', ml.hyper.ONE_HOT_SIZE),
              'learning_rate': ml.hyper.make_log_space('learning_rate', 0.1, 0.1),
              'depth': ml.hyper.make_choice_space('depth', 8),
              'l2_leaf_reg': ml.hyper.make_log_space('l2_leaf_reg', 2.3, 0.3),
              'random_strength': ml.hyper.make_log_space('rand_strength', 1.3, 0.3),
              'bagging_temperature': ml.hyper.make_log_space('bagging_temperature', 1.4, 0.4)}}


@pytest.fixture(scope='module', name='data')
def make_data():
    saved_params = model._PARAMS
    saved_searches = ml.hyper.MAX_SEARCHES
    saved_space = hyper.PARAM_SPACE
    model._PARAMS = PARAMS
    ml.hyper.MAX_SEARCHES = 2
    hyper.PARAM_SPACE = SPACE
    yield model.DividendsModel(('CHMF', 'MSTT', 'PMSBP', 'SNGSP', 'NLMK'), pd.Timestamp('2018-09-05'))
    model._PARAMS = saved_params
    ml.hyper.MAX_SEARCHES = saved_searches
    hyper.PARAM_SPACE = saved_space


def test_str(data):
    assert 'СКО - 4.0920%' in str(data)


def test_positions(data):
    assert data.positions == ('CHMF', 'MSTT', 'PMSBP', 'SNGSP', 'NLMK')


def test_date(data):
    assert data.date == pd.Timestamp('2018-09-05')


def test_std(data):
    assert data.std == pytest.approx(0.040920258736284)


def test_model_params(data):
    assert data.params == {
        'data': {
            'freq': Freq.yearly,
            'lags_range': 1},
        'model': {
            'iterations': 50,
            'random_state': 284704,
            'od_type': 'Iter',
            'verbose': False,
            'allow_writing_files': False,
            'bagging_temperature': 1.3463876077482095,
            'depth': 3,
            'l2_leaf_reg': 1.8578444629373057,
            'learning_rate': 0.09300426944876264,
            'one_hot_max_size': 2,
            'random_strength': 1.0464151963029267}}


def test_div_prediction(data):
    assert data.prediction_mean['CHMF'] == pytest.approx(0.10459980858366799)
    assert data.prediction_mean['MSTT'] == pytest.approx(0.1071490717673651)
    assert data.prediction_mean['PMSBP'] == pytest.approx(0.11000412382799508)
    assert data.prediction_mean['SNGSP'] == pytest.approx(0.05088185727905429)
    assert data.prediction_mean['NLMK'] == pytest.approx(0.1071490717673651)


def test_find_better_model(data, capsys):
    data.find_better_model()
    captured = capsys.readouterr()
    assert 'ЛУЧШАЯ МОДЕЛЬ - Базовая модель' in captured.out
    assert 'СКО - 4.0920%' in captured.out
    assert 'Количество итераций - 50' in captured.out
    assert "{'data': {'freq': <Freq.yearly" in captured.out

    assert 'Найденная модель' in captured.out
    assert 'СКО - 4.9768%' in captured.out
    assert 'Количество итераций - 57' in captured.out
    assert "{'data': {'freq': <Freq.quarterly" in captured.out


def test_find_better_model_fake_std(data, capsys, monkeypatch):
    saved_method = ml.hyper.cv_model

    def fake_cv_model(params, positions, date):
        if params['data']['freq'] == Freq.yearly:
            return saved_method(params, positions, date)
        fake_result = saved_method(params, positions, date)
        fake_result['loss'] = 0.0333
        return fake_result

    monkeypatch.setattr(hyper, 'cv_model', fake_cv_model)
    data.find_better_model()
    captured = capsys.readouterr()
    assert 'Базовая модель' in captured.out
    assert 'СКО - 4.0920%' in captured.out
    assert 'Количество итераций - 50' in captured.out
    assert "{'data': {'freq': <Freq.yearly" in captured.out

    assert 'ЛУЧШАЯ МОДЕЛЬ - Найденная модель' in captured.out
    assert 'СКО - 3.3300%' in captured.out
    assert 'Количество итераций - 57' in captured.out
    assert "{'data': {'freq': <Freq.quarterly" in captured.out
