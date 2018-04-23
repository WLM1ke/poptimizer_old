"""График динамики стоимости портфеля"""

import matplotlib.pyplot as plt
import pandas as pd

from portfolio_optimizer import local
from portfolio_optimizer.reporter.reporter import read_data


def get_investors_names(df: pd.DataFrame):
    """Получает имена инвесторов"""
    columns = df.columns
    names = columns[columns.str.contains('Value_')]
    names = names.str.slice(6)
    return names


def portfolio_cum_return(df: pd.DataFrame):
    """Кумулятивная доходность портфеля"""
    names = get_investors_names(df)
    # После внесения средств
    post_value = df['Value']
    # Перед внесением средств
    pre_value = post_value.subtract(df[names].sum(axis='columns'), fill_value=0)
    portfolio_return = pre_value / post_value.shift(1)
    portfolio_return.iloc[0] = 1
    return portfolio_return.cumprod()


def index_cum_return(df):
    """Кумулятивная доходность индекса в течении отчетного периода"""
    index = local.index()
    index = index[df.index]
    return index / index.iloc[0]


def make_plot(df: pd.DataFrame):
    """Строит график стоимости портфеля"""
    data = pd.concat([portfolio_cum_return(df), index_cum_return(df)], axis='columns')
    data.columns = ['Portfolio', 'MOEX Net Total Return Index']
    data.index = data.index.astype(str)
    xticks = data.index[0:: 12]
    plt.savefig('chart', bbox_inches='tight')


if __name__ == '__main__':
    data = read_data('report')
    make_plot(data[-61:])
