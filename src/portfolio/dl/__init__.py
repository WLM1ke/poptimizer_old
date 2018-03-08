"""Download and transform data to pandas DataFrames."""

from .cpi import get_monthly_cpi
from .dividends import get_dividends
from .history import get_index_history, get_index_history_from_start
from .history import get_quotes_history, get_quotes_history_from_start
from .info import get_info
