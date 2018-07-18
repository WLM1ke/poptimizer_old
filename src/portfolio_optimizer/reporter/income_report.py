"""Расчет дивидендов и дохода за последний год в пересчете на неделю и месяц в постоянных ценах"""

import pandas as pd

from portfolio_optimizer import local
from portfolio_optimizer.reporter.reporter import read_data


def get_investor_data(report_name: str, investor_name: str):
    """Формирует DataFrame с вкладами, стоимостью активов и дивидендами инвестора"""
    df = read_data(report_name)
    value_column = 'Value_' + investor_name
    investor_share = df[value_column] / df['Value']
    df['Dividends'] = df['Dividends'] * investor_share
    df = df[[investor_name, value_column, 'Dividends']]
    df.columns = ['Inflow', 'Value', 'Dividends']
    return df


def constant_prices_data(report_name: str, investor_name: str, start_date: pd.Timestamp):
    """Переводит данные в постоянные цены"""
    df = get_investor_data(report_name, investor_name)
    df = df.loc[start_date:]
    cpi = local.cpi()
    cpi = cpi[-len(df):]
    cpi = cpi.cumprod()
    cpi = cpi.iloc[-1] / cpi
    return df.mul(cpi.values, axis='index')


def rescale_and_format(x, multiplier):
    """Умножает на множитель и форматирует с округлением до тысяч, разделением разрядов и выравниванием вправо"""
    return f'{round(x * multiplier, -3):,.0f}'.replace(',', ' ').rjust(9)


def income_report(report_name: str, investor_name: str, start_date: pd.Timestamp):
    """Расчет дивидендов и дохода с начальной даты в среднем за год, месяц и неделю в постоянных ценах

    Parameters
    ----------
    report_name
        Наименование файла с отчетом, из которого берутся исторические данные
    investor_name
        Имя инвестора, для которого осуществляется расчет
    start_date
        Начальная дата, с которой анализируется статистика

    Returns
    -------
        Распечатывает информационную сводку по дивидендам и доходам
    """
    df = constant_prices_data(report_name, investor_name, start_date)
    dividends = df['Dividends'].iloc[1:].sum()
    income = df['Value'].iloc[-1] - df['Value'].iloc[0] - df['Inflow'].iloc[1:].sum()
    months = len(df) - 1
    time_periods = dict(Y=12 / months, M=1 / months, W=12 * 7 / months / 365.25)
    print(f'\n{investor_name} - from {start_date.date()} inflation adjusted average')
    for period, multiplier in time_periods.items():
        print(f'1{period}:',
              f'Dividends = {rescale_and_format(dividends, multiplier)},',
              f'Income = {rescale_and_format(income, multiplier)}')


if __name__ == '__main__':
    income_report('report', 'WLMike', pd.Timestamp('2016-12-19'))
