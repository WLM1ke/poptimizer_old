"""Расчет дивидендов и дохода за последний год в пересчете на неделю и месяц в постоянных ценах"""

from portfolio_optimizer import local
from portfolio_optimizer.reporter.reporter import read_data


def get_investor_data(report_name: str, investor_name: str):
    """Формирует DataFrame с вкладами, стоимостью активов и дивидендами инвестора"""
    df = read_data(report_name)
    df = df.iloc[-13:]
    value_column = 'Value_' + investor_name
    investor_share = df[value_column] / df['Value']
    df['Dividends'] = df['Dividends'] * investor_share
    df = df[[investor_name, value_column, 'Dividends']]
    df.columns = ['Inflow', 'Value', 'Dividends']
    return df


def constant_prices_data(report_name: str, investor_name: str):
    """Переводит данные в постоянные цены"""
    df = get_investor_data(report_name, investor_name)
    cpi = local.cpi()
    cpi = cpi[-13:]
    cpi = cpi.cumprod()
    cpi = cpi.iloc[-1] / cpi
    return df.mul(cpi.values, axis='index')


def rescale_and_format(x, multiplier):
    """Умножает на множитель и форматирует с округлением до тысяч, разделением разрядов и выравниванием вправо"""
    return f'{round(x * multiplier, -3):,.0f}'.replace(',', ' ').rjust(9)


def income_report(report_name: str, investor_name: str):
    """Расчет дивидендов и дохода за последний год в пересчете на неделю и месяц в постоянных ценах"""
    df = constant_prices_data(report_name, investor_name)
    dividends = df['Dividends'].iloc[-12:].sum()
    income = df['Value'].iloc[-1] - df['Value'].iloc[0] - df['Inflow'].iloc[-12:].sum()
    time_periods = dict(Y=1, M=1 / 12, W=7 / 365.25)
    print(f'\n{investor_name}')
    for period, multiplier in time_periods.items():
        print(f'1{period}:',
              f'Real Dividends = {rescale_and_format(dividends, multiplier)},',
              f'Real Income = {rescale_and_format(income, multiplier)}')
