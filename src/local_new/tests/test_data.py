import time

from local_new.data import Data


def test_data():
    time0 = time.time()
    data = Data(42)
    time1 = time.time()
    assert data.value == 42
    assert time0 <= data.update_time <= time1
    data.value = 24
    time2 = time.time()
    assert data.value == 24
    assert time1 <= data.update_time <= time2


def test_str():
    assert 'Data(value=111, update_time=' in str(Data(111))
