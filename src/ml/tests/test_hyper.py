import hyperopt
import pandas as pd
import pytest

import ml.hyper
from utils.aggregation import Freq


def test_check_space_bounds_no_checks(capsys):
    space = {
        'data': {
            'lags_range': hyper.MAX_LAG - 1},
        'model': {
            'learning_rate': ml.hyper.MEAN_LEARNING_RATE,
            'depth': ml.hyper.DEPTH_RANGE - 1,
            'l2_leaf_reg': ml.hyper.MEAN_L2,
            'random_strength': ml.hyper.MEAN_RAND_STRENGTH,
            'bagging_temperature': ml.hyper.MEAN_BAGGING}}

    hyper.check_space_bounds(space)
    captured = capsys.readouterr()
    assert '' == captured.out


def test_check_space_upper_bound(capsys):
    space = {
        'data': {
            'lags_range': hyper.MAX_LAG},
        'model': {
            'learning_rate': ml.hyper.MEAN_LEARNING_RATE * (1 + 0.91 * ml.hyper.LEARNING_RATE_RANGE),
            'depth': ml.hyper.DEPTH_RANGE,
            'l2_leaf_reg': ml.hyper.MEAN_L2 * (1 + 0.91 * ml.hyper.L2_RANGE),
            'random_strength': ml.hyper.MEAN_RAND_STRENGTH * (1 + 0.91 * ml.hyper.RAND_STRENGTH_RANGE),
            'bagging_temperature': ml.hyper.MEAN_BAGGING * (1 + 0.91 * ml.hyper.BAGGING_RANGE)}}

    hyper.check_space_bounds(space)
    captured = capsys.readouterr()
    assert 'Необходимо увеличить MAX_LAG' in captured.out

    assert 'Необходимо изменить MEAN_LEARNING_RATE' in captured.out
    assert 'Необходимо увеличить RANGE_LEARNING_RATE' in captured.out

    assert 'Необходимо увеличить MAX_DEPTH' in captured.out

    assert 'Необходимо изменить MEAN_L2' in captured.out
    assert 'Необходимо увеличить RANGE_L2' in captured.out

    assert 'Необходимо изменить MEAN_RAND_STRENGTH' in captured.out
    assert 'Необходимо увеличить RANGE_RAND_STRENGTH' in captured.out

    assert 'Необходимо изменить MEAN_BAGGING' in captured.out
    assert 'Необходимо увеличить RANGE_BAGGING' in captured.out


def test_check_space_lower_bound(capsys):
    space = {
        'data': {
            'lags_range': hyper.MAX_LAG},
        'model': {
            'learning_rate': ml.hyper.MEAN_LEARNING_RATE / (1 + 0.91 * ml.hyper.LEARNING_RATE_RANGE),
            'depth': ml.hyper.DEPTH_RANGE,
            'l2_leaf_reg': ml.hyper.MEAN_L2 / (1 + 0.91 * ml.hyper.L2_RANGE),
            'random_strength': ml.hyper.MEAN_RAND_STRENGTH / (1 + 0.91 * ml.hyper.RAND_STRENGTH_RANGE),
            'bagging_temperature': ml.hyper.MEAN_BAGGING / (1 + 0.91 * ml.hyper.BAGGING_RANGE)}}

    hyper.check_space_bounds(space)
    captured = capsys.readouterr()
    assert 'Необходимо увеличить MAX_LAG' in captured.out

    assert 'Необходимо изменить MEAN_LEARNING_RATE' in captured.out
    assert 'Необходимо увеличить RANGE_LEARNING_RATE' in captured.out

    assert 'Необходимо увеличить MAX_DEPTH' in captured.out

    assert 'Необходимо изменить MEAN_L2' in captured.out
    assert 'Необходимо увеличить RANGE_L2' in captured.out

    assert 'Необходимо изменить MEAN_RAND_STRENGTH' in captured.out
    assert 'Необходимо увеличить RANGE_RAND_STRENGTH' in captured.out

    assert 'Необходимо изменить MEAN_BAGGING' in captured.out
    assert 'Необходимо увеличить RANGE_BAGGING' in captured.out


def test_validate_model_params():
    space = {
        'data': {
            'freq': None,
            'lags_range': hyper.MAX_LAG - 1},
        'model': {
            'one_hot_max_size': None,
            'learning_rate': ml.hyper.MEAN_LEARNING_RATE,
            'depth': ml.hyper.DEPTH_RANGE - 1,
            'l2_leaf_reg': ml.hyper.MEAN_L2,
            'random_strength': ml.hyper.MEAN_RAND_STRENGTH,
            'bagging_temperature': ml.hyper.MEAN_BAGGING}}
    assert hyper.validate_model_params(space) is None
    space['model']['iter'] = 1
    with pytest.raises(ValueError, match='Неверный перечень ключей в разделе model'):
        hyper.validate_model_params(space)
    del space['model']['iter']
    del space['data']['freq']
    with pytest.raises(ValueError, match='Неверный перечень ключей в разделе data'):
        hyper.validate_model_params(space)


def test_cv_model():
    date = '2018-09-03'
    pos = ('CHMF', 'RTKMP', 'SNGSP', 'VSMO', 'LKOH')
    params = {'data': {'freq': Freq.yearly,
                       'lags_range': 1},
              'model': {'iterations': 1,
                        'bagging_temperature': 1.3903075723869767,
                        'depth': 6,
                        'l2_leaf_reg': 2.39410372138012,
                        'learning_rate': 0.09938121413558951,
                        'one_hot_max_size': 2,
                        'random_strength': 1.1973699985671262}}
    with pytest.raises(ValueError, match='Неверный перечень ключей в разделе model'):
        ml.hyper.cv_model(, pd.Timestamp(date),, params, pos

    del params['model']['iterations']
        cv_result = ml.hyper.cv_model(, pd.Timestamp(date),, params, pos
    assert isinstance(cv_result, dict)

    assert cv_result['loss'] == pytest.approx(0.03958830516058179)
    assert cv_result['status'] == hyperopt.STATUS_OK
    assert cv_result['data'] == params['data']

        assert 0 < cv_result['model']['iterations'] < ml.hyper.MAX_ITERATIONS
    assert cv_result['model']['bagging_temperature'] == pytest.approx(1.3903075723869767)
    assert cv_result['model']['depth'] == 6
    assert cv_result['model']['l2_leaf_reg'] == pytest.approx(2.39410372138012)
    assert cv_result['model']['learning_rate'] == pytest.approx(0.09938121413558951)
    assert cv_result['model']['one_hot_max_size'] == 2
    assert cv_result['model']['random_strength'] == pytest.approx(1.1973699985671262)

        assert cv_result['model']['random_state'] == ml.hyper.SEED
    assert cv_result['model']['od_type'] == 'Iter'
    assert cv_result['model']['verbose'] is False
    assert cv_result['model']['allow_writing_files'] is False


def test_optimize_hyper(monkeypatch):
    fake_space = {
        'data': {'freq': ml.hyper.make_choice_space('freq', Freq),
                 'lags_range': ml.hyper.make_choice_space('lags_range', 3)},
        'model': {'one_hot_max_size': ml.hyper.make_choice_space('one_hot_max_size', ml.hyper.ONE_HOT_SIZE),
                  'learning_rate': ml.hyper.make_log_space('learning_rate', 0.1, 0.1),
                  'depth': ml.hyper.make_choice_space('depth', 8),
                  'l2_leaf_reg': ml.hyper.make_log_space('l2_leaf_reg', 2.3, 0.3),
                  'random_strength': ml.hyper.make_log_space('rand_strength', 1.3, 0.3),
                  'bagging_temperature': ml.hyper.make_log_space('bagging_temperature', 1.4, 0.4)}}

    monkeypatch.setattr(hyper, 'PARAM_SPACE', fake_space)
    monkeypatch.setattr(hyper, 'MAX_SEARCHES', 2)

    date = '2018-09-03'
    pos = ('CHMF', 'RTKMP', 'SNGSP', 'VSMO', 'LKOH')
    result = ml.hyper.optimize_hyper(, pos, pd.Timestamp(date),
    assert isinstance(result, dict)
    assert result['data'] == dict(freq=Freq.quarterly, lags=1)
    assert len(result['model']) == 6
    assert result['model']['bagging_temperature'] == pytest.approx(1.0557058439636)
    assert result['model']['depth'] == 1
    assert result['model']['l2_leaf_reg'] == pytest.approx(2.417498137284288)
    assert result['model']['learning_rate'] == pytest.approx(0.10806709959509389)
    assert result['model']['one_hot_max_size'] == 100
    assert result['model']['random_strength'] == pytest.approx(1.0813796592585887)
