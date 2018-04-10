"""Download and transform data to pandas DataFrames."""

from .web_cpi import cpi
from .web_dividends import dividends
from .web_index import index
from .web_quotes import quotes
from .web_securities_info import get_securities_info as securities_info
from .web_tickers import get_reg_number_tickers as reg_number_tickers
