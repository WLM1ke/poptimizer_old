from urllib import request
from urllib.error import URLError

from web.moex.iss_tickers import reg_number_tickers

'''check_points = [('1-02-65104-D', ('UPRO', 'EONR', 'OGK4')),
                ('10301481B', ('SBER', 'SBER03')),
                ('20301481B', ('SBERP', 'SBERP03')),
                ('1-02-06556-A', ('PHOR',))]


@pytest.mark.parametrize("reg_number, expected", check_points)
def test_reg_number_tickers(reg_number, expected):
    assert reg_number_tickers(reg_number) == expected'''


class FakeUrlopen:

    def __init__(self):
        self.saved_urlopen = request.urlopen
        request.urlopen = self
        self.called = False

    def __call__(self, url):
        if not self.called:
            self.called = True
            request.urlopen = self.saved_urlopen
            raise URLError(TimeoutError())
        else:
            self.saved_urlopen(url)


def test_get_json_error():
    FakeUrlopen()
    assert reg_number_tickers('1-02-65104-D') == ('UPRO', 'EONR', 'OGK4')
