"""Глобальные параметры"""

from pathlib import Path

# Путь к данным - данные состоящие из нескольких серий хранятся в отдельных директориях внутри базовой директории
DATA_PATH = Path(__file__).parents[2] / 'data'

# Путь к отчетам
REPORTS_PATH = Path(__file__).parents[2] / 'reports'

# Параметр для доверительных интервалов
T_SCORE = 2.0

# Множитель, для переходя к после налоговым значениям
AFTER_TAX = 1 - 0.13

# Максимальный объем операций в долях портфеля
MAX_TRADE = 0.01

# Минимальный оборот акции - преимущества акции квадратичо снижаются при приближении оборота к данному уровню
VOLUME_CUT_OFF = 1.5 * MAX_TRADE
