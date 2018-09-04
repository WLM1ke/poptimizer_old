import hyperopt
import pandas as pd
import pytest

from ml import hyper
from ml.cases import Freq


def test_check_space_bounds_no_checks(capsys):
    space = {
        'data': {
            'lags': hyper.MAX_LAG - 1},
        'model': {
            'learning_rate': hyper.MEAN_LEARNING_RATE,
            'depth': hyper.MAX_DEPTH - 1,
            'l2_leaf_reg': hyper.MEAN_L2,
            'random_strength': hyper.MEAN_RAND_STRENGTH,
            'bagging_temperature': hyper.MEAN_BAGGING}}

    hyper.check_space_bounds(space)
    captured = capsys.readouterr()
    assert '' == captured.out


def test_check_space_upper_bound(capsys):
    space = {
        'data': {
            'lags': hyper.MAX_LAG},
        'model': {
            'learning_rate': hyper.MEAN_LEARNING_RATE * (1 + 0.91 * hyper.RANGE_LEARNING_RATE),
            'depth': hyper.MAX_DEPTH,
            'l2_leaf_reg': hyper.MEAN_L2 * (1 + 0.91 * hyper.RANGE_L2),
            'random_strength': hyper.MEAN_RAND_STRENGTH * (1 + 0.91 * hyper.RANGE_RAND_STRENGTH),
            'bagging_temperature': hyper.MEAN_BAGGING * (1 + 0.91 * hyper.RANGE_BAGGING)}}

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
            'lags': hyper.MAX_LAG},
        'model': {
            'learning_rate': hyper.MEAN_LEARNING_RATE / (1 + 0.91 * hyper.RANGE_LEARNING_RATE),
            'depth': hyper.MAX_DEPTH,
            'l2_leaf_reg': hyper.MEAN_L2 / (1 + 0.91 * hyper.RANGE_L2),
            'random_strength': hyper.MEAN_RAND_STRENGTH / (1 + 0.91 * hyper.RANGE_RAND_STRENGTH),
            'bagging_temperature': hyper.MEAN_BAGGING / (1 + 0.91 * hyper.RANGE_BAGGING)}}

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
            'lags': hyper.MAX_LAG - 1},
        'model': {
            'one_hot_max_size': None,
            'learning_rate': hyper.MEAN_LEARNING_RATE,
            'depth': hyper.MAX_DEPTH - 1,
            'l2_leaf_reg': hyper.MEAN_L2,
            'random_strength': hyper.MEAN_RAND_STRENGTH,
            'bagging_temperature': hyper.MEAN_BAGGING}}
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
                       'lags': 1},
              'model': {'iterations': 1,
                        'bagging_temperature': 1.3903075723869767,
                        'depth': 6,
                        'l2_leaf_reg': 2.39410372138012,
                        'learning_rate': 0.09938121413558951,
                        'one_hot_max_size': 2,
                        'random_strength': 1.1973699985671262}}
    with pytest.raises(ValueError, match='Неверный перечень ключей в разделе model'):
        hyper.cv_model(params, pos, pd.Timestamp(date))

    del params['model']['iterations']
    cv_result = hyper.cv_model(params, pos, pd.Timestamp(date))
    assert isinstance(cv_result, dict)

    assert cv_result['loss'] == pytest.approx(0.04033618184101815)
    assert cv_result['status'] == hyperopt.STATUS_OK
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


def test_optimize_hyper():
    hyper.MAX_SEARCHES = 2
    date = '2018-09-03'
    pos = ('CHMF', 'RTKMP', 'SNGSP', 'VSMO', 'LKOH')
    result = hyper.optimize_hyper(pos, pd.Timestamp(date))
    assert isinstance(result, dict)
    assert result['data'] == dict(freq=Freq.quarterly, lags=1)
    assert len(result['model']) == 6
    assert result['model']['bagging_temperature'] == pytest.approx(1.0557058439636)
    assert result['model']['depth'] == 1
    assert result['model']['l2_leaf_reg'] == pytest.approx(2.7951209738402794)
    assert result['model']['learning_rate'] == pytest.approx(0.10806709959509389)
    assert result['model']['one_hot_max_size'] == 100
    assert result['model']['random_strength'] == pytest.approx(1.0813796592585887)
