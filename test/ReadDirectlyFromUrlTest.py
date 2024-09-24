import pytest
import pandas as pd
from io import StringIO

@pytest.fixture
def sample_html():
    # KRX에서 받아올 HTML 구조의 예시 데이터를 반환
    html_data = '''
    <table>
        <tr><th>종목코드</th><th>회사명</th></tr>
        <tr><td>1</td><td>삼성전자</td></tr>
        <tr><td>2</td><td>LG전자</td></tr>
    </table>
    '''
    return html_data

def test_read_krx_table(sample_html):
    tables = pd.read_html(StringIO(sample_html))
    df = tables[0]

    # '종목코드'가 6자리로 변환되는지 확인
    df['종목코드'] = df['종목코드'].astype(int).map('{:06d}'.format)
    assert df['종목코드'].iloc[0] == '000001'
    assert df['종목코드'].iloc[1] == '000002'

    # 정렬이 제대로 되는지 확인
    df = df.sort_values(by='종목코드')
    assert df.iloc[0]['종목코드'] == '000001'
    assert df.iloc[1]['종목코드'] == '000002'
