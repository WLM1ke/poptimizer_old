"""Парсер html-таблиц"""
from typing import NamedTuple, Callable

import bs4
import pandas as pd


class DataColumn(NamedTuple):
    """Описание колонки с данными"""
    index: int
    validation_dict: dict
    parser_func: Callable


class HTMLTableParser:
    """Парсер html-таблиц - если таблица содержит tbody, то парсится только tbody

    По номеру таблицы на странице формирует представление ее ячеек в виде списка списков. Ячейки с rowspan colspan
    представляются в виде набора атомарных ячеек с одинаковыми значениями
    """

    def __init__(self, html: str, table_index: int):
        soup = bs4.BeautifulSoup(html, 'lxml')
        try:
            self._table = soup.find_all('table')[table_index]
        except IndexError:
            raise IndexError(f'На странице нет таблицы {table_index}')
        table_body = self._table.find('tbody')
        if table_body:
            self._table = table_body
        self._parsed_table = []

    @property
    def parsed_table(self):
        """Распарсенная таблица"""
        if self._parsed_table:
            return self._parsed_table
        table = self._table
        row_pos = 0
        col_pos = 0
        for row in table.find_all('tr'):
            for cell in row.find_all():
                col_pos = self._find_empty_cell(row_pos, col_pos)
                row_span = int(cell.get('rowspan', 1))
                col_span = int(cell.get('colspan', 1))
                self._insert_cells(cell.text, row_pos, col_pos, row_span, col_span)
            row_pos += 1
            col_pos = 0
        return self._parsed_table

    def _find_empty_cell(self, row_pos, col_pos):
        """Ищет первую незаполненную ячейку в ряду и возвращает ее координату"""
        parse_table = self._parsed_table
        if row_pos >= len(parse_table):
            return col_pos
        while col_pos < len(parse_table[row_pos]) and parse_table[row_pos][col_pos] is not None:
            col_pos += 1
        return col_pos

    def _insert_cells(self, value, row, col, row_span, col_span):
        """Заполняет таблицу значениями с учетом rowspan и colspan ячейки"""
        for row_pos in range(row, row + row_span):
            for col_pos in range(col, col + col_span):
                self._insert_cell(value, row_pos, col_pos)

    def _insert_cell(self, value, row_pos, col_pos):
        """Заполняет значение, при необходимости расширяя таблицу"""
        parse_table = self._parsed_table
        while row_pos >= len(parse_table):
            parse_table.append([None])
        while col_pos >= len(parse_table[row_pos]):
            parse_table[row_pos].append(None)
        parse_table[row_pos][col_pos] = value

    def make_df(self, columns=None, drop_header=0, drop_footer=0):
        """Преобразует таблицу в DataFrame

        Если передан список колонок, то они валидируются, а значения преобразуются
        """
        if columns:
            self._validate_columns(columns)
        table = self._yield_rows(columns, drop_header, drop_footer)
        return pd.DataFrame(table)

    def _validate_columns(self, columns):
        """Проверка значений в колонках"""
        table = self.parsed_table
        for column in columns:
            for row, value in column.validation_dict.items():
                if table[row][column.index] != value:
                    raise ValueError(f'Значение в таблице "{table[row][column.index]}" - должно быть "{value}"')

    def _yield_rows(self, columns, drop_header, drop_footer):
        """Генерирует строки с избранными колонками со значениями после парсинга"""
        table = self.parsed_table
        if drop_footer >= 0:
            drop_footer = len(table) - drop_footer
        table = table[drop_header:drop_footer]
        for row in table:
            yield [column.parser_func(row[column.index]) for column in columns]
