from bs4 import BeautifulSoup
import requests
import pandas as pd
from io import StringIO
import mplfinance as mpf

# 1. 일별 시세 페이지 url 설정
code = '005930'
domain = 'https://finance.naver.com'
uri = '/item/sise_day.nhn?code=' + code
first_page = 1

# URL 설정
url = domain + uri + '&page=' + str(first_page)

# print(url)

# 2. 맨 뒤 페이지 숫자 구하기
response = requests.get(url, headers={'User-agent': 'Mozilla/5.0'}).text
bs = BeautifulSoup(response, 'lxml')
# gpRR = page Right Right (>>)
class_pgrr = bs.find('td', class_='pgRR')

# class_pgrr의 text 출력 확인
# print(class_pgrr.prettify())

# 전체 페이지수 확인
all_pages = class_pgrr.a['href'].split('=')[-1]
# print(all_pages) # 708

# 3. 전체 페이지 읽어오기
df_list = []  # 빈 리스트를 사용하여 데이터프레임을 저장
for page in range(1, int(all_pages)+1):
    url = domain + uri + '&page=' + str(page)
    response = requests.get(url, headers={'User-agent': 'Mozilla/5.0'}).text

    # pandas.read_html()에 HTML 문자열을 직접 전달하는 것이 곧 더 이상 지원되지 않음
    # StringIO로 감싸서 read_html에 전달
    df_list.append(pd.read_html(StringIO(response), header=0)[0])

# pandas 2.0 버전부터 append() 메서드는 더 이상 사용되지 않으며, 대신 pd.concat()을 사용해야 합니다.
df = pd.concat(df_list, ignore_index=True) # 리스트 내 모든 DataFrame을 병합
df = df.dropna()  # 결측값 제거
# print(df)

# 4. 차트 출력을 위한 데이터프레임(df) 가공하기
df = df.iloc[0:30]  # 최근 30일 데이터만 사용
df = df.sort_values(by='날짜')  # 날짜 기준으로 오름차순 정렬
df = df.rename(columns={'날짜': 'Date', '시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close', '거래량': 'Volume'})
df = df.sort_values(by='Date')  # 날짜 기준으로 오름차순 정렬
df.index = pd.to_datetime(df['Date'])  # 날짜를 Datetime 형으로 변환
df = df[['Open', 'High', 'Low', 'Close', 'Volume']]  # 필요한 열만 선택

# 5. 차트 - 종가 그래프
kwargs = dict(title='Celltrion (005930) - Candle Chart', type='candle', mav=(2, 4, 6), volume=True, ylabel='ohlc candles')
mc = mpf.make_marketcolors(up='r', down='b', inherit=True)
s = mpf.make_mpf_style(marketcolors=mc)
mpf.plot(df, **kwargs, style=s)
