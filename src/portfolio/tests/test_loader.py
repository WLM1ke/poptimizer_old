import datetime

from portfolio import loader


def test_security_info():
    data = loader.security_info(['aKRN', 'gAZP', 'LKOH', 'SBER'])
    print(data)

    assert loader.security_info('aKRN')


def test_quotes_history():
    data = loader.quotes_history('AKRN')
    print(data.head(10))
    print(data[99:101])
    print(data.tail())

    data = loader.quotes_history('SBER', datetime.date(2018, 2, 9))
    print(data)

    # TODO: монотонность индексов
    # TODO: уникальность индексов

    assert loader.quotes_history('aKRN')


def test_index_history():
    data = loader.index_history()
    print(data.head())
    print(data[99:101])
    print(data.tail())

    data = loader.index_history(datetime.date(2018, 2, 9))
    print(data)

    # TODO: монотонность индексов
    # TODO: уникальность индексов

    assert loader.index_history(datetime.date(2018, 2, 10))


def test_monthly_cpi():
    print(loader.monthly_cpi())

    assert False
