"""ML-модель предсказания доходности"""
import pandas as pd
from hyperopt import hp

from ml import hyper
from ml.model_base import AbstractModel
from ml.returns import cases

PARAMS = {
    "data": {"ew_lags": 7.972_338_443_092_346, "returns_lags": 15},
    "model": {
        "bagging_temperature": 0.104_794_967_222_254_47,
        "depth": 9,
        "ignored_features": (),
        "l2_leaf_reg": 32.196_964_587_556_62,
        "learning_rate": 0.126_637_416_099_172_76,
        "one_hot_max_size": 2,
        "random_strength": 2.337_526_417_962_564_6,
    },
}

# Диапазон лагов относительно базового, для которого осуществляется поиск оптимальной ML-модели
EW_LAGS_RANGE = 0.02
MAX_RETURNS_LAGS = 15  # 2018-12-05


def ew_lags(base_params: dict, cut=1.0):
    """Формирует границы интервала поиска ew_lags

    Параметр cut (0.0, 1.0) сужает границы, что используется в функции проверки границ диапазона
    """
    lags = base_params["data"]["ew_lags"]
    return lags / (1 + cut * EW_LAGS_RANGE), lags * (1 + cut * EW_LAGS_RANGE)


def returns_lags():
    """Формирует список допустимых лагов доходности"""
    return list(range(MAX_RETURNS_LAGS + 1))


class ReturnsModel(AbstractModel):
    """Содержит прогноз доходности и его СКО"""

    PARAMS = PARAMS

    @staticmethod
    def _learn_pool_params(*args, **kwargs):
        """Параметры для создания catboost.Pool для обучения"""
        return cases.learn_pool_params(*args, **kwargs)

    @staticmethod
    def _predict_pool_func(*args, **kwargs):
        """catboost.Pool с данными для предсказания"""
        return cases.predict_pool(*args, **kwargs)

    def _make_data_space(self):
        """Пространство поиска параметров данных модели"""
        space = {
            "ew_lags": hp.uniform("ew_lags", *ew_lags(self.PARAMS)),
            "returns_lags": hyper.make_choice_space("returns_lags", returns_lags()),
        }
        return space

    def _check_data_space_bounds(self, params: dict):
        """Проверка, что параметры лежал не около границы вероятностного пространства"""
        lags = params["data"]["ew_lags"]
        lags_range = ew_lags(self.PARAMS, 0.9)
        if lags < lags_range[0] or lags_range[1] < lags:
            print(
                f"\nНеобходимо увеличить EW_LAGS_RANGE до {EW_LAGS_RANGE + 0.01:0.2f}"
            )
        lag = params["data"]["returns_lags"]
        if lag == MAX_RETURNS_LAGS:
            print(f"\nНеобходимо увеличить MAX_RETURNS_LAGS до {MAX_RETURNS_LAGS + 1}")

    @property
    def prediction_mean(self):
        """pd.Series с прогнозом дивидендов

        Так как данные нормированы по СКО прогноз умножается на СКО данных
        """
        return self._prediction * self._prediction_data["std"]

    @property
    def prediction_std(self):
        """pd.Series с прогнозом дивидендов

        Так как данные нормированы по СКО прогнозное СКО умножается на СКО данных
        """
        return self.std * self._prediction_data["std"]


if __name__ == "__main__":
    from trading import POSITIONS, DATE

    pred = ReturnsModel(tuple(sorted(POSITIONS)), pd.Timestamp(DATE))
    print(pred)
    # pred.find_better_model()
    pred.learning_curve()
