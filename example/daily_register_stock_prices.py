from sqlalchemy import create_engine, text, Column, CHAR, DECIMAL, Date, BigInteger, DateTime, String, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo  # Python 3.9 이상에서 사용할 수 있는 표준 라이브러리
import time
import random
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
import os
import logging

# SQLAlchemy Base 클래스
Base = declarative_base()

# 로깅 설정
logging.basicConfig(
    filename='scraping_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Company 모델 정의
class Company(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)  # 회사명
    stock_code = Column(String(10), unique=True, nullable=False)  # 종목코드
    industry = Column(String(100), nullable=False)  # 업종
    main_product = Column(String(255))  # 주요 제품
    listing_date = Column(Date)  # 상장일
    fiscal_month = Column(String(10))  # 결산월
    ceo_name = Column(String(100))  # 대표자명
    website = Column(String(255))  # 홈페이지
    region = Column(String(100))  # 지역
    updated_at = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Seoul')))  # KST로 설정

    def __repr__(self):
        return f"<Company(name={self.name}, stock_code={self.stock_code})>"

# StockPrice 모델 정의 (stock_prices 테이블과 매핑)
class StockPrice(Base):
    __tablename__ = 'stock_prices'

    stock_code = Column(CHAR(6), primary_key=True, nullable=False)  # 종목코드
    trading_date = Column(Date, primary_key=True, nullable=False)  # 거래 날짜
    open = Column(DECIMAL(10, 2), nullable=False)  # 시가
    high = Column(DECIMAL(10, 2), nullable=False)  # 고가
    low = Column(DECIMAL(10, 2), nullable=False)  # 저가
    close = Column(DECIMAL(10, 2), nullable=False)  # 종가
    volume = Column(BigInteger, nullable=False)  # 거래량
    updated_at = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Seoul')))  # 최종 업데이트 시간

# ScrapingResults 모델 정의
class ScrapingResult(Base):
    __tablename__ = 'scraping_results'

    stock_code = Column(CHAR(6), primary_key=True, nullable=False)  # 종목코드
    last_trading_date = Column(Date, primary_key=True, nullable=False)  # 마지막 거래 날짜
    scraping_status = Column(String(20), default='READY', nullable=False)  # 스크래핑 처리 상태
    updated_at = Column(DateTime, default=lambda: datetime.now(ZoneInfo('Asia/Seoul')), onupdate=datetime.now)  # 업데이트 날짜


# NaverFinanceScraper 클래스 정의 (시세 정보 스크래핑)
class NaverFinanceScraper:
    """
    Naver 금융 사이트에서 주식 시세 데이터를 스크래핑하는 클래스.
    """

    def __init__(self, stock_code):
        self.stock_code = stock_code
        self.domain = 'https://finance.naver.com'
        self.uri = f'/item/sise_day.nhn?code={self.stock_code}'
        self.headers = {'User-agent': 'Mozilla/5.0'}

    def fetch_page(self, page_number):
        """특정 페이지의 데이터를 가져오는 메서드"""
        url = f"{self.domain}{self.uri}&page={page_number}"
        response = requests.get(url, headers=self.headers).text
        return pd.read_html(StringIO(response), header=0)[0]  # HTML 데이터를 pandas DataFrame으로 변환

    def get_total_pages(self):
        """종목코드의 총 페이지 수를 가져오는 메서드"""
        url = f"{self.domain}{self.uri}&page=1"
        response = requests.get(url, headers=self.headers).text
        bs = BeautifulSoup(response, 'lxml')
        class_pgrr = bs.find('td', class_='pgRR')

        if class_pgrr is None:
            # HTML 페이지 구조가 변경되었을 수 있으므로, 페이지 내용을 출력
            print("페이지 정보를 찾을 수 없습니다. 페이지 내용을 확인하세요.")
            print(bs.prettify())  # BeautifulSoup으로 파싱된 페이지 출력
            raise ValueError("페이지 정보가 없습니다.")

        total_pages = class_pgrr.a['href'].split('=')[-1]
        return int(total_pages)

    def get_stock_data(self, max_retries=5, backoff_factor=1):
        """
        종목코드에 대한 모든 페이지의 시세 데이터를 스크래핑하여
        pandas DataFrame으로 반환하는 메서드.
        백오프(backoff) 전략을 적용하여 재시도 및 대기시간을 증가시킵니다.
        """
        try:
            total_pages = self.get_total_pages()
        except ValueError:
            logging.error(f"종목 코드 {self.stock_code} 페이지 정보를 가져올 수 없습니다.")
            return pd.DataFrame()

        df_list = []
        for page in range(1, total_pages + 1):
            retries = 0
            while retries <= max_retries:
                try:
                    df = self.fetch_page(page)
                    df_list.append(df)
                    print(f"{page}/{total_pages} 페이지 데이터 스크래핑 완료.")
                    break
                except Exception as e:
                    retries += 1
                    sleep_time = backoff_factor * (2 ** retries)
                    logging.error(f"종목 {self.stock_code}, 페이지 {page}에서 오류 발생: {e}")
                    time.sleep(sleep_time)
                    if retries > max_retries:
                        logging.error(f"종목 {self.stock_code}, 페이지 {page} 재시도 실패.")
                        break

        if df_list:
            full_df = pd.concat(df_list, ignore_index=True).dropna()
            return full_df
        else:
            return pd.DataFrame()


# DatabaseHandler 클래스 정의 (SQLAlchemy)
class DatabaseHandler:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_or_update_company(self, company_data):
        """
        회사 정보를 추가하거나 이미 존재하면 업데이트하는 메서드
        :param company_data: {'name': 회사명, 'stock_code': 종목코드, 'industry': 업종, 'main_product': 주요제품,
                             'listing_date': 상장일, 'fiscal_month': 결산월, 'ceo_name': 대표자명,
                             'website': 홈페이지, 'region': 지역}
        """
        session = self.Session()
        try:
            # 회사 정보가 이미 있는지 확인 (종목 코드로 검색)
            company = session.query(Company).filter_by(stock_code=company_data['stock_code']).first()

            if company:  # 이미 존재하면 업데이트
                company.name = company_data['name']
                company.industry = company_data['industry']
                company.main_product = company_data.get('main_product')
                company.listing_date = company_data.get('listing_date')
                company.fiscal_month = company_data.get('fiscal_month')
                company.ceo_name = company_data.get('ceo_name')
                company.website = company_data.get('website')
                company.region = company_data.get('region')
                company.updated_at = datetime.now(ZoneInfo('Asia/Seoul'))  # KST로 업데이트 시간 설정
                print(f"업데이트된 회사: {company.name} ({company.stock_code})")
            else:  # 존재하지 않으면 새로 추가
                new_company = Company(
                    name=company_data['name'],
                    stock_code=company_data['stock_code'],
                    industry=company_data['industry'],
                    main_product=company_data.get('main_product'),
                    listing_date=company_data.get('listing_date'),
                    fiscal_month=company_data.get('fiscal_month'),
                    ceo_name=company_data.get('ceo_name'),
                    website=company_data.get('website'),
                    region=company_data.get('region'),
                    updated_at=datetime.now(ZoneInfo('Asia/Seoul'))  # KST로 설정
                )
                session.add(new_company)
                print(f"추가된 회사: {new_company.name} ({new_company.stock_code})")

            session.commit()
        except Exception as e:
            session.rollback()
            print(f"에러 발생: {e}")
        finally:
            session.close()

    def update_scraping_result(self, stock_code, last_trading_date, status='COMPLETED'):
        """
        스크래핑 결과를 scraping_results 테이블에 업데이트하는 메서드.
        스크래핑 성공/실패 여부와 마지막 거래 일자를 업데이트.
        """
        session = self.Session()
        try:
            result = session.query(ScrapingResult).filter_by(stock_code=stock_code).first()

            if result:  # 이미 존재하면 업데이트
                result.scraping_status = status
                result.last_trading_date = last_trading_date
                result.updated_at = datetime.now(ZoneInfo('Asia/Seoul'))
            else:  # 존재하지 않으면 새로 추가
                new_result = ScrapingResult(
                    stock_code=stock_code,
                    last_trading_date=last_trading_date,
                    scraping_status=status,
                    updated_at=datetime.now(ZoneInfo('Asia/Seoul'))
                )
                session.add(new_result)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"에러 발생: {e}")
        finally:
            session.close()

    def get_company_stock_codes(self):
        """상장된 모든 회사의 stock_code를 가져오는 메서드"""
        session = self.Session()
        try:
            # SQL 쿼리를 text로 명시
            result = session.execute(text("SELECT stock_code FROM companies")).fetchall()
            return [row[0] for row in result]
        except SQLAlchemyError as e:
            print(f"에러 발생: {e}")
            return []
        finally:
            session.close()

    def is_scraping_completed(self, stock_code):
        """
        특정 종목의 스크래핑 상태가 'COMPLETED'인지 확인.
        :param stock_code: 종목 코드
        :return: 마지막 거래 날짜와 상태가 COMPLETED이면 True 반환
        """
        session = self.Session()
        try:
            result = session.query(ScrapingResult).filter_by(stock_code=stock_code).first()

            if result and result.scraping_status == 'COMPLETED':
                print(f"종목 코드 {stock_code}는 이미 스크래핑 완료 상태입니다. (마지막 거래일: {result.last_trading_date})")
                return True
            return False
        except Exception as e:
            print(f"스크래핑 상태 확인 중 에러 발생: {e}")
            return False
        finally:
            session.close()

    def add_or_update_stock_price(self, stock_data):
        """stock_prices 테이블에 시세 정보를 추가하거나 업데이트하는 메서드"""
        session = self.Session()
        try:
            stock_price = StockPrice(
                stock_code=stock_data['stock_code'],
                trading_date=stock_data['trading_date'],
                open=stock_data['open'],
                high=stock_data['high'],
                low=stock_data['low'],
                close=stock_data['close'],
                volume=stock_data['volume'],
                updated_at=datetime.now(ZoneInfo('Asia/Seoul'))
            )
            session.merge(stock_price)  # 기본키가 존재하면 업데이트, 없으면 추가
            session.commit()
            print(f"종목 {stock_data['stock_code']} - {stock_data['trading_date']} 시세 정보 저장 완료")
        except SQLAlchemyError as e:
            session.rollback()
            print(f"에러 발생: {e}")
        finally:
            session.close()

# CompanyScraper 클래스 정의 (상장 회사 목록 스크래핑)
class CompanyScraper:
    def __init__(self, url):
        self.url = url

    def scrape(self):
        """
        KRX에서 상장 회사 목록을 스크래핑하여 회사명과 종목코드를 반환
        :return: [{'name': '삼성전자', 'stock_code': '005930', 'industry': 업종, 'main_product': 주요 제품,
                   'listing_date': 상장일, 'fiscal_month': 결산월, 'ceo_name': 대표자명, 'website': 홈페이지, 'region': 지역}]
        """
        response = requests.get(self.url)
        response.encoding = 'euc-kr'  # 한글 인코딩을 맞춰줌

        # pandas를 사용해 데이터를 스크래핑
        tables = pd.read_html(StringIO(response.text))

        # 첫 번째 테이블 선택
        df = tables[0]

        # '종목코드'를 숫자 형식으로 변환하고, 6자리 문자열로 포맷팅
        df['종목코드'] = df['종목코드'].astype(int).map('{:06d}'.format)

        # 필요한 열만 선택 (회사명, 종목코드, 업종, 주요제품, 상장일, 결산월, 대표자명, 홈페이지, 지역)
        df = df[['회사명', '종목코드', '업종', '주요제품', '상장일', '결산월', '대표자명', '홈페이지', '지역']]

        # 날짜 형식 변환
        df['상장일'] = pd.to_datetime(df['상장일'], errors='coerce', format='%Y-%m-%d')

        # NaN 값을 None으로 변환
        df = df.where(pd.notnull(df), None)

        # 데이터프레임을 리스트로 변환
        company_list = df.to_dict('records')

        # company_list의 각 딕셔너리는 {'name': '회사명', 'stock_code': '종목코드'} 형식
        return [
            {
                'name': company['회사명'],
                'stock_code': company['종목코드'],
                'industry': company['업종'],
                'main_product': company['주요제품'],
                'listing_date': company['상장일'],
                'fiscal_month': company['결산월'],
                'ceo_name': company['대표자명'],
                'website': company['홈페이지'],
                'region': company['지역']
            }
            for company in company_list
        ]

# StockScraper 클래스 정의
class StockScraper:
    """
    주식 스크래핑을 관리하는 클래스.
    """

    def __init__(self, db_handler, stock_code):
        self.stock_code = stock_code
        self.db_handler = db_handler
        self.scraper = NaverFinanceScraper(stock_code)  # Naver 금융 스크래퍼 인스턴스

    def scrape_and_save(self):
        """시세 데이터를 스크래핑하여 DB에 저장하는 메서드"""
        print(f"종목 코드 {self.stock_code} 시세 데이터를 스크래핑 시작...")
        stock_data_df = self.scraper.get_stock_data()  # 백오프 전략 적용된 메서드 사용

        # 스크래핑된 데이터가 없으면 다음 종목으로 넘어감
        if stock_data_df.empty:
            print(f"종목 코드 {self.stock_code}에서 데이터를 찾을 수 없습니다. 다음 종목으로 넘어갑니다.")
            return  # 데이터가 없으면 종료

        # 스크래핑된 데이터의 열 이름 확인
        print(stock_data_df.columns)  # 열 이름을 확인

        # 열 이름이 다를 경우 공백 제거 및 열 이름 맞춤
        stock_data_df.columns = stock_data_df.columns.str.strip()

        # '날짜' 열이 없거나 데이터가 없는 경우 종료
        if '날짜' not in stock_data_df.columns:
            print(f"종목 코드 {self.stock_code}에서 '날짜' 열을 찾을 수 없습니다. 다음 종목으로 넘어갑니다.")
            return  # '날짜' 열이 없으면 종료

        # 필요한 데이터만 선택하고 각 row를 DB에 저장
        stock_data_df = stock_data_df[['날짜', '종가', '시가', '고가', '저가', '거래량']].rename(
            columns={'날짜': 'trading_date', '종가': 'close', '시가': 'open', '고가': 'high', '저가': 'low', '거래량': 'volume'})
        stock_data_df['trading_date'] = pd.to_datetime(stock_data_df['trading_date'], format='%Y.%m.%d')

        # 마지막 거래 날짜 저장을 위해 가장 최신 날짜를 찾음
        last_trading_date = stock_data_df['trading_date'].max().date()

        for _, row in stock_data_df.iterrows():
            stock_data = {
                'stock_code': self.stock_code,
                'trading_date': row['trading_date'].date(),
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close'],
                'volume': int(row['volume'])
            }
            self.db_handler.add_or_update_stock_price(stock_data)

        print(f"스크래핑 완료! 종목 코드 {self.stock_code}")

        # 스크래핑 완료 후, scraping_results 테이블에 마지막 거래 일자를 업데이트
        self.db_handler.update_scraping_result(self.stock_code, last_trading_date, status='COMPLETED')


def get_password(file_path=None):
    """
    주어진 파일 경로에서 비밀번호를 읽어와 URL 인코딩하여 반환하는 함수.
    :param file_path: 비밀번호가 저장된 파일 경로 (환경변수 또는 인자로 받을 수 있음)
    :return: URL 인코딩된 비밀번호 또는 None
    """
    file_path = file_path or os.getenv('PASSWORD_FILE_PATH', '/Users/lucky/Documents/quant/password.txt')

    # 파일 경로가 존재하는지 확인
    if not os.path.exists(file_path):
        print(f"Error: {file_path} 파일을 찾을 수 없습니다.")
        return None

    try:
        with open(file_path, 'r') as file:
            password = file.read().strip()
            return quote_plus(password)  # URL 인코딩 후 반환
    except Exception as e:
        print(f"Error: 비밀번호 파일을 읽는 중 오류가 발생했습니다: {e}")
        return None

# 메인 프로세스
def main():
    # 1. 비밀번호를 URL 인코딩
    password = get_password()
    if not password:
        print("비밀번호를 가져오지 못했습니다. 프로그램을 종료합니다.")
        return  # 비밀번호가 없으면 프로그램 종료

    # 2. MySQL 연결 URL 구성
    db_url = f'mysql+pymysql://investor:{password}@127.0.0.1:3306/investor'

    # 3. DatabaseHandler 인스턴스 생성
    db_handler = DatabaseHandler(db_url)

    # 4. KRX 상장 회사 목록 스크래핑
    scraper_url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
    company_scraper = CompanyScraper(scraper_url)

    # 5. 스크래핑한 상장 회사 목록을 데이터베이스에 저장 또는 업데이트
    company_data_list = company_scraper.scrape()
    for company_data in company_data_list:
        try:
            db_handler.add_or_update_company(company_data)
        except Exception as e:
            print(f"회사 {company_data['name']} 저장 중 에러 발생: {e}")
            logging.error(f"회사 {company_data['name']} 저장 중 에러 발생: {e}")

    # 6. 상장 회사 목록 조회
    company_stock_codes = db_handler.get_company_stock_codes()

    # 7. 등록된 상장 회사 목록을 순차적으로 처리하여 시세 데이터 스크래핑 및 저장
    for stock_code in company_stock_codes:
        # 스크래핑 상태 확인
        if db_handler.is_scraping_completed(stock_code):
            print(f"종목 코드 {stock_code}는 이미 스크래핑 완료 상태입니다. 스킵합니다.")
            continue  # 스크래핑 완료된 종목은 건너뛰고 다음 종목 처리

        stock_scraper = StockScraper(db_handler, stock_code)

        # 요청 간 간격을 두기 위해 랜덤하게 5~10초 대기
        time.sleep(random.uniform(5, 10))

        try:
            stock_scraper.scrape_and_save()
        except Exception as e:
            print(f"종목 코드 {stock_code} 스크래핑 중 에러 발생: {e}")
            logging.error(f"종목 코드 {stock_code} 스크래핑 중 에러 발생: {e}")

if __name__ == '__main__':
    main()
