"""Поиск бумаг высоким momentum и с низкой корреляцией с текущим портфелем"""

import random

from metrics.portfolio import CASH, Portfolio
from metrics.returns_metrics import ReturnsMetrics
from web import moex
from web.labels import REG_NUMBER

# Позиция в строке, в которой отображаются результаты проверки бумаг
RESULT_ALIMENT = 70


def all_securities():
    """Возвращает данные по всем торгуемым бумагам и печатает их количество"""
    df = moex.securities_info()
    print()
    print('Общее количество торгуемых бумаг'.ljust(RESULT_ALIMENT), f'{len(df)}')
    return df


def all_securities_with_reg_number():
    """Возвращает множество всех бумаг с регистрационным номером и печатает их количество"""
    df = all_securities()
    df.dropna(subset=[REG_NUMBER], inplace=True)
    print('Количество бумаг с регистрационным номером'.ljust(RESULT_ALIMENT), f'{len(df)}')
    return set(df.index)


def non_portfolio_securities(portfolio: Portfolio):
    """Возвращает список бумаг не находящихся в портфеле и печатает их количество"""
    tickers = all_securities_with_reg_number()
    tickers = tickers - set(portfolio.positions)
    print('Количество бумаг не в портфеле'.ljust(RESULT_ALIMENT), f'{len(tickers)}')
    return list(tickers)


def make_new_portfolio(portfolio: Portfolio, new_ticker: str):
    """Создает портфель, в который добавлен новый тикер"""
    date = portfolio.date
    cash = portfolio.value[CASH]
    lots = portfolio.lots
    positions = {ticker: lots[ticker] for ticker in portfolio.positions[:-2]}
    positions[new_ticker] = 0
    return Portfolio(date=date,
                     cash=cash,
                     positions=positions)


def valid_volume(portfolio: Portfolio, ticker: str):
    """Распечатывает фактор оборота и проверяет, что он больше нуля"""
    volume = portfolio.volume_factor[ticker]
    print('Фактор оборота'.ljust(RESULT_ALIMENT), f'{volume: .4f} - ', end='')
    if volume > 0:
        print('OK')
        return True
    else:
        print('Не подходит')
        return False


def valid_return_gradient(portfolio: Portfolio, ticker: str, t_score: float):
    """Проверяет, что градиент доходности больше t_score СКО в момент просадки с поправкой на оборот"""
    returns_metrics = ReturnsMetrics(portfolio)
    std = returns_metrics.std_at_draw_down
    gradient = returns_metrics.gradient[ticker]
    volume = portfolio.volume_factor[ticker]
    ticker_t_score = gradient / std * volume
    print('Градиент просадки'.ljust(RESULT_ALIMENT), f'{gradient: .4f} - ', end='')
    if ticker_t_score > t_score:
        print(f'OK {ticker_t_score:.2f} > {t_score:.2f} СКО')
        return True
    else:
        print(f'Не подходит {ticker_t_score:.2f} < {t_score:.2f} СКО')
        return False


def find_momentum_tickers(portfolio: Portfolio, t_score: float):
    """Ищет торгуемый тикер, градиент роста просадки которого больше t_score СКО

    Такая бумага имеет хороший momentum и низкую корреляцию с портфелем, и является неплохим претендентом на включение в
    портфель. Отсеиваются бумаги, которые имеют слишком маленький оборот

    Поиск ведется в случайном порядке по всему перечню торгуемых бумага. Распечатывается информация об анализируемых
    бумагах. Процесс останавливается после нахождения первой подходящей

    Parameters
    ----------
    portfolio
        Портфель, в который потенциально может быть включена еще одна бумага
    t_score
        Требование по минимальной величине градиента просадки
    """
    tickers = non_portfolio_securities(portfolio)
    random.shuffle(tickers)
    for number, ticker in enumerate(tickers):
        print(f'\n{number + 1}. {ticker}')
        new_portfolio = make_new_portfolio(portfolio, ticker)
        if not valid_volume(new_portfolio, ticker):
            continue
        if valid_return_gradient(new_portfolio, ticker, t_score):
            break


if __name__ == '__main__':
    port = Portfolio(date='2018-03-19',
                     cash=1000.21,
                     positions=dict(GAZP=682, VSMO=145, TTLK=123),
                     value=3_699_111.41)
    print(port.volume_factor)
    metrics = ReturnsMetrics(port)
    print(metrics.gradient / metrics.std_at_draw_down)
