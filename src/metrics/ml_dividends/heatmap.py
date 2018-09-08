"""Визуализация ожидаемых дивидендов в зависимости от дивидендов предыдущего года"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from metrics.ml_dividends import model

DIVIDENDS_LIST = [i / 100 for i in range(0, 16, 1)]


def make_cases(positions: tuple):
    """Строит прогноз для всех сочетаний кортежа тикеров и набора предыдущих дивидендов"""
    return [[ticker, dividend] for ticker in positions for dividend in DIVIDENDS_LIST]


def make_heatmap_df(positions, date):
    """DataFrame для построения HeatMap

    Строки упорядоченные по средней прогнозной доходности тикеры, столбцы - доходность прошлого года
    """
    cases = make_cases(positions)
    result = model.DividendsML(positions, date).predict(cases)
    cases = pd.DataFrame(cases)
    cases['y'] = result
    cases.set_index([0, 1], inplace=True)
    cases = cases.unstack()
    cases = cases.mul(100)
    cases['mean'] = cases.mean(axis=1)
    cases.sort_values(by='mean', inplace=True)
    cases.drop(columns='mean', inplace=True)
    return cases


def make_heatmap(positions: tuple, date: pd.Timestamp):
    """Рисует HeatMap для набора тикеров для прогнозной доходности в зависимости от доходности прошлого года"""
    df = make_heatmap_df(positions, date)

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.imshow(df.values, aspect='auto')

    ax.set_xticks(np.arange(len(DIVIDENDS_LIST)))
    ax.set_yticks(np.arange(len(df.index)))
    ax.set_xticklabels([f'{i:0.0%}' for i in DIVIDENDS_LIST])
    ax.set_yticklabels(df.index)

    for i in range(len(positions)):
        for j in range(len(DIVIDENDS_LIST)):
            ax.text(j, i, f'{df.iloc[i, j]:0.1f}', ha='center', va='center', color='w')

    ax.set_title('Dividends predictions')
    ax.set_xlabel('Lagged dividends')
    fig.tight_layout()
    plt.show()


if __name__ == '__main__':
    try:
        from trading import POSITIONS, DATE
    except ModuleNotFoundError:
        POSITIONS = ['AKRN']
        DATE = '2018-09-06'

    make_heatmap(tuple(sorted(POSITIONS)), pd.Timestamp(DATE))
