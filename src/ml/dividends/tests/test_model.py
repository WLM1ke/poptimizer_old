import pandas as pd
import pytest

from ml import hyper
from ml.dividends import model
from utils.aggregation import Freq

PARAMS = {'data': {'freq': Freq.yearly,
                   'lags': 1},
          'model': {'bagging_temperature': 1.3463876077482095,
                    'depth': 3,
                    'l2_leaf_reg': 1.8578444629373057,
                    'learning_rate': 0.09300426944876264,
                    'one_hot_max_size': 2,
                    'random_strength': 1.0464151963029267}}

SPACE = {
    'data': {'freq': hyper.make_choice_space('freq', Freq),
             'lags_range': hyper.make_choice_space('lags_range', list(range(1, 4)))},
    'model': {'one_hot_max_size': hyper.make_choice_space('one_hot_max_size', hyper.ONE_HOT_SIZE),
              'learning_rate': hyper.make_log_space('learning_rate', 0.1, 0.1),
              'depth': hyper.make_choice_space('depth', list(range(1, 9))),
              'l2_leaf_reg': hyper.make_log_space('l2_leaf_reg', 2.3, 0.3),
              'random_strength': hyper.make_log_space('rand_strength', 1.3, 0.3),
              'bagging_temperature': hyper.make_log_space('bagging_temperature', 1.4, 0.4)}}


def fake_make_model_space(_):
    return SPACE['model']


@pytest.fixture(scope='module', name='data')
def make_data():
    saved_params = model.DividendsModel.PARAMS
    saved_searches = hyper.MAX_SEARCHES
    saved_space = hyper.make_model_space
    model.DividendsModel.PARAMS = PARAMS
    hyper.MAX_SEARCHES = 2
    hyper.make_model_space = fake_make_model_space
    yield model.DividendsModel(('CHMF', 'MSTT', 'PMSBP', 'SNGSP', 'NLMK'), pd.Timestamp('2018-09-05'))
    model.DividendsModel.PARAMS = saved_params
    hyper.MAX_SEARCHES = saved_searches
    hyper.make_model_space = saved_space


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
            'lags': 1},
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
    assert 'R2 - 37.8509%' in captured.out
    assert 'Количество итераций - 50' in captured.out
    assert "{'data': {'freq': <Freq.yearly" in captured.out

    assert 'Найденная модель' in captured.out
    assert 'R2 - 17.7351%' in captured.out
    assert 'Количество итераций - 57' in captured.out
    assert "{'data': {'freq': <Freq.quarterly" in captured.out


def test_find_better_model_fake_std(data, capsys, monkeypatch):
    saved_method = hyper.cv_model

    def fake_cv_model(params, positions, date, data_pool_func):
        if params['data']['freq'] == Freq.yearly:
            return saved_method(params, positions, date, data_pool_func)
        fake_result = saved_method(params, positions, date, data_pool_func)
        fake_result['loss'] = 0.0333
        return fake_result

    monkeypatch.setattr(hyper, 'cv_model', fake_cv_model)
    data.find_better_model()
    captured = capsys.readouterr()
    assert 'Базовая модель' in captured.out
    assert 'R2 - 37.8509%' in captured.out
    assert 'Количество итераций - 50' in captured.out
    assert "{'data': {'freq': <Freq.yearly" in captured.out

    assert 'ЛУЧШАЯ МОДЕЛЬ - Найденная модель' in captured.out
    assert 'R2 - 17.7351%' in captured.out
    assert 'Количество итераций - 57' in captured.out
    assert "{'data': {'freq': <Freq.quarterly" in captured.out


def test_check_data_space_bounds(data, monkeypatch, capsys):
    monkeypatch.setattr(model, 'MAX_LAGS', 1)
    data._check_data_space_bounds(PARAMS)
    captured = capsys.readouterr()
    assert 'Необходимо увеличить MAX_LAGS до 2' in captured.out
