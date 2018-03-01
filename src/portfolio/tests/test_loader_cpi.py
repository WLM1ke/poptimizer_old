from ..loader_cpi import download, parse_local_dataframe_cpi, URL_CPI
from pathlib import Path
import tempfile


def test_download():    
    with tempfile.NamedTemporaryFile() as f:
        path1 = f.name
    download(URL_CPI, local_path = path1)
    assert Path(path1).exists()
    
def test_parse_local_dataframe_cpi():
    df = parse_local_dataframe_cpi()
    assert df.CPI.loc['1991-01-31'] == 1.0620   
    assert df.CPI.loc['2018-01-31'] == 1.0031 