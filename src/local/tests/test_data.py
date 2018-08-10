import time

from local.data import Data


def test_data():
    time0 = time.time()
    data = Data(42)
    time1 = time.time()
    assert data.value == 42
    assert time0 <= data.last_update <= time1
    data.value = 24
    time2 = time.time()
    assert data.value == 24
    assert time1 <= data.last_update <= time2


def test_str():
    assert 'Data(value=111, last_update=' in str(Data(111))


def test_empty_data():
    data = Data()
    assert data.value is None
    assert data.last_update is None
