"""Load local copy of data and updates it."""

from portfolio_optimizer.local.legacy_dividends import get_legacy_dividends as legacy_dividends
from portfolio_optimizer.local.local_cpi import cpi as cpi
from portfolio_optimizer.local.local_dividends import get_dividends as dividends
from portfolio_optimizer.local.local_index import get_index_history as index_history
from portfolio_optimizer.local.local_quotes import get_prices_history as prices_history
from portfolio_optimizer.local.local_quotes import get_volumes_history as volumes_history
from portfolio_optimizer.local.local_securities_info import get_last_prices as last_prices
from portfolio_optimizer.local.local_securities_info import get_security_info as security_info
