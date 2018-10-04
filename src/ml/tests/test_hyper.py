import hyperopt
import pandas as pd
import pytest

from ml import hyper
from ml.dividends import cases
from utils.aggregation import Freq

BASE_PARAMS = {
        'model': {
            'one_hot_max_size': 2,
            'ignored_features': (),
            'learning_rate': 0.1,
            'depth': hyper.MAX_DEPTH - 1,
            'l2_leaf_reg': 3,
            'random_strength': 1,
            'bagging_temperature': 1}}


def test_make_model_space():
    space = hyper.make_model_space(BASE_PARAMS)
    assert isinstance(space, dict)
    assert len(space) == 7
    assert isinstance(space['one_hot_max_size'], hyperopt.pyll.Apply)
    assert space['ignored_features'] == BASE_PARAMS['model']['ignored_features']
    assert isinstance(space['learning_rate'], hyperopt.pyll.Apply)
    assert isinstance(space['depth'], hyperopt.pyll.Apply)
    assert isinstance(space['l2_leaf_reg'], hyperopt.pyll.Apply)
    assert isinstance(space['random_strength'], hyperopt.pyll.Apply)
    assert isinstance(space['bagging_temperature'], hyperopt.pyll.Apply)


def test_check_model_bounds_no_checks(capsys):
    hyper.check_model_bounds(BASE_PARAMS, BASE_PARAMS)
    captured = capsys.readouterr()
    assert '' == captured.out


def test_check_model_upper_bound(capsys):
    params = {
        'model': {
            'learning_rate': 0.1 * (1 + 0.91 * hyper.LEARNING_RATE_RANGE),
            'depth': hyper.MAX_DEPTH,
            'l2_leaf_reg': 3 * (1 + 0.91 * hyper.L2_RANGE),
            'random_strength': 1 * (1 + 0.91 * hyper.RAND_STRENGTH_RANGE),
            'bagging_temperature': 1 * (1 + 0.91 * hyper.BAGGING_RANGE)}}
    hyper.check_model_bounds(params, BASE_PARAMS)
    captured = capsys.readouterr()
    assert 'Необходимо увеличить LEARNING_RATE_RANGE' in captured.out
    assert 'Необходимо увеличить MAX_DEPTH' in captured.out
    assert 'Необходимо увеличить L2_RANGE' in captured.out
    assert 'Необходимо увеличить RAND_STRENGTH_RANGE' in captured.out
    assert 'Необходимо увеличить BAGGING_RANGE' in captured.out


def test_check_model_lower_bound(capsys):
    space = {
        'model': {
            'learning_rate': 0.1 / (1 + 0.91 * hyper.LEARNING_RATE_RANGE),
            'depth': 1,
            'l2_leaf_reg': 3 / (1 + 0.91 * hyper.L2_RANGE),
            'random_strength': 1 / (1 + 0.91 * hyper.RAND_STRENGTH_RANGE),
            'bagging_temperature': 1 / (1 + 0.91 * hyper.BAGGING_RANGE)}}
    hyper.check_model_bounds(space, BASE_PARAMS)
    captured = capsys.readouterr()
    assert 'Необходимо увеличить LEARNING_RATE_RANGE' in captured.out
    assert 'Необходимо увеличить L2_RANGE' in captured.out
    assert 'Необходимо увеличить RAND_STRENGTH_RANGE' in captured.out
    assert 'Необходимо увеличить BAGGING_RANGE' in captured.out


def test_cv_model():
    date = '2018-09-03'
    pos = ('CHMF', 'RTKMP', 'SNGSP', 'VSMO', 'LKOH')
    params = {'data': {'freq': Freq.yearly,
                       'lags': 1},
              'model': {'bagging_temperature': 1.3903075723869767,
                        'depth': 6,
                        'l2_leaf_reg': 2.39410372138012,
                        'learning_rate': 0.09938121413558951,
                        'one_hot_max_size': 2,
                        'random_strength': 1.1973699985671262}}
    cv_result = hyper.cv_model(params, pos, pd.Timestamp(date), cases.learn_pool)
    assert isinstance(cv_result, dict)

    assert cv_result['loss'] == pytest.approx(0.843203601144351)
    assert cv_result['status'] == hyperopt.STATUS_OK
    assert cv_result['std'] == pytest.approx(0.03958830516058179)
    assert cv_result['r2'] == pytest.approx(0.28900768701719826)
    assert cv_result['data'] == params['data']

    assert 0 < cv_result['model']['iterations'] < hyper.MAX_ITERATIONS
    assert cv_result['model']['bagging_temperature'] == pytest.approx(1.3903075723869767)
    assert cv_result['model']['depth'] == 6
    assert cv_result['model']['l2_leaf_reg'] == pytest.approx(2.39410372138012)
    assert cv_result['model']['learning_rate'] == pytest.approx(0.09938121413558951)
    assert cv_result['model']['one_hot_max_size'] == 2
    assert cv_result['model']['random_strength'] == pytest.approx(1.1973699985671262)

    assert cv_result['model']['random_state'] == hyper.SEED
    assert cv_result['model']['od_type'] == 'Iter'
    assert cv_result['model']['verbose'] is False
    assert cv_result['model']['allow_writing_files'] is False


def test_optimize_hyper(monkeypatch):
    space = {
        'data': {'freq': hyper.make_choice_space('freq', Freq),
                 'lags': hyper.make_choice_space('lags_range', range(1, 4))},
        'model': {'one_hot_max_size': hyper.make_choice_space('one_hot_max_size', hyper.ONE_HOT_SIZE),
                  'learning_rate': hyper.make_log_space('learning_rate', 0.1, 0.1),
                  'depth': hyper.make_choice_space('depth', range(1, 9)),
                  'l2_leaf_reg': hyper.make_log_space('l2_leaf_reg', 2.3, 0.3),
                  'random_strength': hyper.make_log_space('rand_strength', 1.3, 0.3),
                  'bagging_temperature': hyper.make_log_space('bagging_temperature', 1.4, 0.4)}}
    params = {
        'data': {'freq': Freq.yearly,
                 'lags': 1},
        'model': {'one_hot_max_size': 2,
                  'learning_rate': 0.1,
                  'depth': 6,
                  'l2_leaf_reg': 2.3,
                  'random_strength': 1.3,
                  'bagging_temperature': 1.4}}

    monkeypatch.setattr(hyper, 'MAX_SEARCHES', 2)
    monkeypatch.setattr(hyper, 'make_model_space', lambda x: space['model'])

    date = '2018-09-03'
    pos = ('CHMF', 'RTKMP', 'SNGSP', 'VSMO', 'LKOH')
    result = hyper.optimize_hyper(params, pos, pd.Timestamp(date), cases.learn_pool, space['data'])
    assert isinstance(result, dict)
    assert result['data'] == dict(freq=Freq.quarterly, lags=1)
    assert len(result['model']) == 6
    assert result['model']['bagging_temperature'] == pytest.approx(1.0557058439636)
    assert result['model']['depth'] == 1
    assert result['model']['l2_leaf_reg'] == pytest.approx(2.417498137284288)
    assert result['model']['learning_rate'] == pytest.approx(0.10806709959509389)
    assert result['model']['one_hot_max_size'] == 100
    assert result['model']['random_strength'] == pytest.approx(1.0813796592585887)
