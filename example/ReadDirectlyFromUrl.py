import pandas as pd
import requests
from io import StringIO

# URL 설정
url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'

# requests로 데이터 가져오기
response = requests.get(url)

# 인코딩 설정 (예: 'EUC-KR'로 시도해볼 수 있음)
response.encoding = 'euc-kr'  # 'euc-kr' 또는 'cp949' 같은 인코딩을 시도

# StringIO로 감싸서 pandas.read_html에 전달
tables = pd.read_html(StringIO(response.text))

# tables는 리스트이므로 첫 번째 테이블을 선택
df = tables[0]

# tables는 리스트이므로 첫 번째 테이블을 선택
df = tables[0]

# '종목코드'를 숫자 형식으로 변환하고, 6자리 문자열로 포맷팅
df['종목코드'] = df['종목코드'].astype(int).map('{:06d}'.format)

# '종목코드' 기준으로 정렬
df = df.sort_values(by='종목코드')

print(df)