import pandas as pd
import pytest

from metrics.ml_dividends import hyper, model
from metrics.ml_dividends.cases import Freq

PARAMS = {'data': {'freq': Freq.yearly,
                   'lags': 1},
          'model': {'bagging_temperature': 1.3463876077482095,
                    'depth': 3,
                    'l2_leaf_reg': 1.8578444629373057,
                    'learning_rate': 0.09300426944876264,
                    'one_hot_max_size': 2,
                    'random_strength': 1.0464151963029267}}


@pytest.fixture(scope='module', name='data')
def make_data():
    saved_params = model.PARAMS
    saved_searches = hyper.MAX_SEARCHES
    model.PARAMS = PARAMS
    hyper.MAX_SEARCHES = 2
    yield model.DividendsML(('CHMF', 'MSTT', 'PMSBP', 'SNGSP', 'NLMK'), pd.Timestamp('2018-09-05'))
    model.PARAMS = saved_params
    hyper.MAX_SEARCHES = saved_searches


def test_str(data):
    assert 'СКО - 4.0183%' in str(data)


def test_positions(data):
    assert data.positions == ('CHMF', 'MSTT', 'PMSBP', 'SNGSP', 'NLMK')


def test_date(data):
    assert data.date == pd.Timestamp('2018-09-05')


def test_std(data):
    assert data.std == pytest.approx(0.04018286219491704)


def test_model_params(data):
    assert data.params == {'data': {'freq': Freq.yearly,
                                          'lags': 1},
                                 'model': {'iterations': 45,
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
    assert data.div_prediction['CHMF'] == pytest.approx(0.10450239969349545)
    assert data.div_prediction['MSTT'] == pytest.approx(0.09941397711887319)
    assert data.div_prediction['PMSBP'] == pytest.approx(0.11062344589559978)
    assert data.div_prediction['SNGSP'] == pytest.approx(0.051546300190778445)
    assert data.div_prediction['NLMK'] == pytest.approx(0.09930524361854995)


def test_find_better_model(data, capsys):
    data.find_better_model()
    captured = capsys.readouterr()
    assert 'ЛУЧШАЯ МОДЕЛЬ - Базовая модель' in captured.out
    assert 'СКО - 4.0183%' in captured.out
    assert 'Количество итераций - 45' in captured.out
    assert "{'data': {'freq': <Freq.yearly" in captured.out

    assert 'Найденная модель' in captured.out
    assert 'СКО - 4.9914%' in captured.out
    assert 'Количество итераций - 78' in captured.out
    assert "{'data': {'freq': <Freq.quarterly" in captured.out


def test_find_better_model_fake_std(data, capsys, monkeypatch):
    saved_method = hyper.cv_model

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
    assert 'СКО - 4.0183%' in captured.out
    assert 'Количество итераций - 45' in captured.out
    assert "{'data': {'freq': <Freq.yearly" in captured.out

    assert 'ЛУЧШАЯ МОДЕЛЬ - Найденная модель' in captured.out
    assert 'СКО - 3.3300%' in captured.out
    assert 'Количество итераций - 78' in captured.out
    assert "{'data': {'freq': <Freq.quarterly" in captured.out
