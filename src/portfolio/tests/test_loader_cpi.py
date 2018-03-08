import tempfile
from pathlib import Path

from ..loader_cpi import download, update_from_web_cpi, parse_local_dataframe_cpi, URL_CPI


def test_download():    
    with tempfile.NamedTemporaryFile() as f:
        path1 = f.name
    download(URL_CPI, local_path=path1)
    assert Path(path1).exists()
    
def test_parse_local_dataframe_cpi():
    update_from_web_cpi()
    df = parse_local_dataframe_cpi()
    assert df.CPI.loc['1991-01-31'] == 1.0620   
    assert df.CPI.loc['2018-01-31'] == 1.0031 