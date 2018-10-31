"""Абстрактный парсер html таблиц"""
from abc import ABC, abstractmethod
from typing import NamedTuple, Callable

import bs4
import pandas as pd


class DataColumn(NamedTuple):
    """Описание колонки с данными"""
    name: str
    index: int
    parser_func: Callable = pd.to_numeric


class AbstractTableParser(ABC):
    """Абстрактный парсер html таблиц"""
    TABLE_INDEX = None
    # Каждая строка заголовка отдельный массив срок. Если проверка наименования строки не нужно, то None
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
            table = soup.find_all('table')[index]
        except IndexError:
            raise IndexError(f'На странице {url} нет таблицы {index}')
        table_body = table.find('tbody')
        if table_body:
            return table_body
        return table

    @staticmethod
    def _validate_table(rows, titles):
        """Проверяет корректность наименований"""
        for row, row_titles in zip(rows, titles):
            cells = row.find_all()
            if len(cells) != len(row_titles):
                raise ValueError(f'Длинна строки с наименованиями {len(cells)} - должна быть {len(row_titles)}')
            for cell, title in zip(cells, row_titles):
                if (title is not None) and (cell.text != title):
                    raise ValueError(f'Наименования в таблице "{cell.text}" - должно быть "{title}"')

    def _parse_row(self, row):
        """Выбирает столбцы с данными и  преобразует значения"""
        cells = row.find_all()
        return [column.parser_func(cells[column.index].text) for column in self.DATA_COLUMNS]

    def _get_columns_names(self):
        """Возвращает список с названиями столбцов с данными"""
        return [column.name for column in self.DATA_COLUMNS]

    @property
    def df(self):
        """DataFrame с таблицей"""
        columns = self._get_columns_names()
        data = iter(self)
        return pd.DataFrame(data=data, columns=columns)
