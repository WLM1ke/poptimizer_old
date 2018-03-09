"""Helper functions for data path finding"""


def make_path(data_type=None, series_name):
    folder = find_root() / 'data' / subfolder
    if not folder.exists():
        folder.mkdir(parents=True)
    return str(folder / filename)


def make_path_raw(filename):
    return make_path('raw', filename)


def make_path_parsed(filename):
    return make_path('parsed', filename)


URL_CPI = 'http://www.gks.ru/free_doc/new_site/prices/potr/I_ipc.xlsx'
PATH_RAW_CPI = make_path_raw('I_ipc.xlsx')
PATH_PARSED_CPI = make_path_parsed('cpi.txt')
