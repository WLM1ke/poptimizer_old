from portfolio.download.cpi import get_monthly_cpi

    
def test_parse_local_dataframe_cpi():
    df = get_monthly_cpi()
    assert df.CPI.loc['1991-01-31'] == 1.0620   
    assert df.CPI.loc['2018-01-31'] == 1.0031 