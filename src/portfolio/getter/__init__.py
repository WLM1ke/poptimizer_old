"""Load local copy of data and updates it."""

from portfolio.getter.cpi import get_cpi as cpi
from portfolio.getter.dividends import get_dividends as dividends
from portfolio.getter.dividends import get_legacy_dividends as legacy_dividends
from portfolio.getter.history import get_index_history as index_history
from portfolio.getter.history import get_prices_history as prices_history
from portfolio.getter.history import get_volumes_history as volumes_history
from portfolio.getter.securities_info import get_last_prices as last_prices
from portfolio.getter.securities_info import get_security_info as security_info
