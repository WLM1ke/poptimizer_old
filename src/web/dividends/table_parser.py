"""Абстрактный парсер html таблиц"""
from abc import ABC, abstractmethod
from typing import NamedTuple, Callable

import bs4
import pandas as pd


class DataColumn(NamedTuple):
    name: str
    index: int
    parser_func: Callable = pd.to_numeric


class AbstractTableParser(ABC):
    """Абстрактный парсер html таблиц"""
    TABLE_INDEX = None
    HEADER_TITLES = []
    FOOTER_TITLES = []
    DATA_COLUMNS = []

    def __iter__(self):
        """Возвращает строки таблицы в виде списков"""
        table = self.get_html_table()
        rows = table.find_all(name='tr')
        header = len(self.HEADER_TITLES)
        self._validate_table(rows[:header], self.HEADER_TITLES)
        footer = len(rows) - len(self.FOOTER_TITLES)
        self._validate_table(rows[footer:], self.FOOTER_TITLES)
        for row in rows[header:footer]:
            yield self._parse_row(row)

    @abstractmethod
    def get_html(self):
        """Возвращает html код страницы"""
        raise NotImplementedError

    def get_html_table(self):
        """Возвращает html таблицу в формате bs4"""
        html, url = self.get_html()
        soup = bs4.BeautifulSoup(html, 'lxml')
        index = self.TABLE_INDEX
        try:
            return soup.find_all('table')[index]
        except IndexError:
            raise IndexError(f'На странице {url} нет таблицы {index}')

    @staticmethod
    def _validate_table(rows, titles):
        """Проверяет корректность заголовков"""
        for row, row_titles in zip(rows, titles):
            cells = row.find_all('th')
            if len(cells) != len(row_titles):
                raise ValueError('Некорректная длинна строк с наименованиями')
            for cell, title in zip(cells, row_titles):
                if (title is not None) and (cell != title):
                    raise ValueError('Некорректные наименования в таблице')

    def _parse_row(self, row):
        cells = row.find_all('td')
        return [column.parser_func(cells[column.index]) for column in self.DATA_COLUMNS]

    def _get_columns_names(self):
        return [column.name for column in self.DATA_COLUMNS]

    def df(self):
        columns = self._get_columns_names()
        data = self
        return pd.DataFrame(data=data, columns=columns)
