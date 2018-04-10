"""Download and transform data to pandas DataFrames."""

from .web_cpi import cpi
from .web_dividends import dividends as dividends
from .web_history import get_index_history as index_history
from .web_history import get_quotes_history as quotes_history
from .web_securities_info import get_securities_info as securities_info
from .web_tickers import get_reg_number_tickers as reg_number_tickers
