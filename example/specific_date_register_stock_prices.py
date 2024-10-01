from sqlalchemy import create_engine, text, Column, CHAR, DECIMAL, Date, BigInteger, DateTime, String, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo  # Python 3.9 이상에서 사용할 수 있는 표준 라이브러리
import time
import random
import requests
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

    def scrape_for_specific_date(self, target_date, db_handler):
        """
        특정 일자의 데이터를 스크래핑하여 일치하는 데이터를 저장하는 메서드.
        :param target_date: 조회하고자 하는 일자 (문자열 형식: 'YYYY-MM-DD')
        :param db_handler: 데이터를 저장하기 위한 DatabaseHandler 인스턴스
        """
        print(f"종목 코드 {self.stock_code}, {target_date} 날짜 데이터를 스크래핑 중...")
        try:
            # 첫 번째 페이지 스크래핑
            stock_data_df = self.fetch_page(1)

            # 열 이름을 정리
            stock_data_df.columns = stock_data_df.columns.str.strip()

            # '날짜' 열이 없거나 데이터가 없는 경우 종료
            if '날짜' not in stock_data_df.columns:
                print(f"종목 코드 {self.stock_code}에서 '날짜' 열을 찾을 수 없습니다.")
                return

            # 날짜 필드를 pandas의 datetime 형식으로 변환
            stock_data_df['날짜'] = pd.to_datetime(stock_data_df['날짜'], format='%Y.%m.%d')

            # 타겟 날짜를 datetime 형식으로 변환
            target_date_dt = pd.to_datetime(target_date, format='%Y-%m-%d')

            # 타겟 날짜와 일치하는 데이터 필터링
            filtered_data = stock_data_df[stock_data_df['날짜'] == target_date_dt]

            if filtered_data.empty:
                print(f"종목 코드 {self.stock_code}, {target_date} 날짜에 해당하는 데이터를 찾을 수 없습니다.")
                return

            # 필요한 데이터만 선택하고 열 이름을 변경
            filtered_data = filtered_data[['날짜', '종가', '시가', '고가', '저가', '거래량']].rename(
                columns={'날짜': 'trading_date', '종가': 'close', '시가': 'open', '고가': 'high', '저가': 'low', '거래량': 'volume'})

            # 데이터를 저장
            for _, row in filtered_data.iterrows():
                stock_data = {
                    'stock_code': self.stock_code,
                    'trading_date': row['trading_date'].date(),
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': int(row['volume'])
                }
                db_handler.add_or_update_stock_price(stock_data)

            print(f"종목 코드 {self.stock_code}, {target_date} 날짜 데이터 저장 완료!")

        except Exception as e:
            print(f"종목 코드 {self.stock_code}에서 스크래핑 중 오류 발생: {e}")

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

    def reset_scraping_status_for_old_entries(self, trading_date):
        """
        마지막 거래일자가 지정한 거래일자보다 작고, 스크래핑 상태가 COMPLETED인 항목의 상태를 READY로 변경.
        :param trading_date: 기준이 되는 거래 일자 (YYYY-MM-DD 형식)
        """
        session = self.Session()
        try:
            check_date = datetime.strptime(trading_date, '%Y-%m-%d').date()

            # 지정한 거래일자보다 이전이고, 상태가 COMPLETED인 항목들을 조회하여 READY로 업데이트
            session.query(ScrapingResult).filter(
                ScrapingResult.last_trading_date < check_date,
                ScrapingResult.scraping_status == 'COMPLETED'
            ).update(
                {"scraping_status": "READY", "updated_at": datetime.now(ZoneInfo('Asia/Seoul'))},
                synchronize_session=False
            )

            session.commit()
            print(f"지정한 거래일자 {trading_date} 이전의 COMPLETED 상태 항목을 READY로 업데이트했습니다.")
        except Exception as e:
            session.rollback()
            print(f"스크래핑 상태 업데이트 중 에러 발생: {e}")
        finally:
            session.close()

    def is_stock_code_registered(self, stock_code):
        """
        특정 종목 코드가 scraping_results 테이블에 등록되어 있는지 확인하는 함수.

        :param stock_code: 종목 코드
        :return: 스크래핑 상태가 등록되어 있으면 True, 아니면 False
        """
        session = self.Session()
        try:
            result = session.query(ScrapingResult).filter_by(stock_code=stock_code).first()
            return result is not None
        except Exception as e:
            print(f"스크래핑 상태 확인 중 에러 발생: {e}")
            return False
        finally:
            session.close()

    def is_scraping_completed_for_date_and_after(self, stock_code, trading_date):
        """
        특정 종목의 특정 거래일자와 그 이후 날짜에 대해 스크래핑 상태가 'COMPLETED'인지 확인.

        :param stock_code: 종목 코드
        :param trading_date: 거래 일자 (YYYY-MM-DD 형식)
        :return: 거래일자와 이후 날짜의 상태가 모두 'COMPLETED'이면 True 반환, 아니면 False
        """
        session = self.Session()
        try:
            check_trading_date = datetime.strptime(trading_date, '%Y-%m-%d').date()  # 특정 거래일자
            # stock_code와 거래일자 이후의 날짜들을 필터링
            result = session.query(ScrapingResult).filter(
                ScrapingResult.stock_code == stock_code,
                ScrapingResult.last_trading_date >= check_trading_date
            ).all()

            # 결과가 없으면 해당 일자 이후로는 스크래핑이 안된 것임
            if not result:
                print(f"종목 코드 {stock_code}는 {check_trading_date} 이후로 스크래핑된 기록이 없습니다.")
                return False

            # 모든 결과가 'COMPLETED' 상태인지 확인
            for record in result:
                if record.scraping_status != 'COMPLETED':
                    print(f"종목 코드 {stock_code}, 거래일 {record.last_trading_date}는 완료되지 않았습니다.")
                    return False

            # 모두 'COMPLETED' 상태인 경우
            print(f"종목 코드 {stock_code}, 거래일 {check_trading_date} 이후는 모두 스크래핑 완료 상태입니다.")
            return True
        except Exception as e:
            print(f"스크래핑 상태 확인 중 에러 발생: {e}")
            return False
        finally:
            session.close()

    def has_recent_weekly_data(self, stock_code, trading_date):
        """
        특정 종목 코드에 대해 최근 일주일 간 시세 데이터가 있는지 확인하는 함수.

        :param stock_code: 종목 코드
        :param trading_date: 기준 거래 일자 (문자열 형식: 'YYYY-MM-DD')
        :return: 최근 일주일 간 데이터가 있으면 True, 없으면 False
        """
        session = self.Session()
        try:
            # 기준 일자로부터 7일 이전의 날짜 계산
            check_date = datetime.strptime(trading_date, '%Y-%m-%d').date() - pd.Timedelta(days=7)

            # 해당 기간 동안 시세 데이터가 있는지 확인
            result = session.query(StockPrice).filter(
                StockPrice.stock_code == stock_code,
                StockPrice.trading_date >= check_date
            ).first()

            if result:
                return True
            else:
                return False
        except Exception as e:
            print(f"시세 데이터 확인 중 에러 발생: {e}")
            return False
        finally:
            session.close()

    def terminate_scraping(self, stock_code):
        """
        특정 종목 코드의 스크래핑 상태를 TERMINATED로 업데이트하는 함수.

        :param stock_code: 종목 코드
        """
        session = self.Session()
        try:
            result = session.query(ScrapingResult).filter_by(stock_code=stock_code).first()

            if result:
                result.scraping_status = 'TERMINATED'
                result.updated_at = datetime.now(ZoneInfo('Asia/Seoul'))
                session.commit()
                print(f"종목 코드 {stock_code}의 스크래핑 상태가 'TERMINATED'로 업데이트되었습니다.")
            else:
                print(f"종목 코드 {stock_code}에 대한 스크래핑 결과가 존재하지 않습니다.")
        except Exception as e:
            session.rollback()
            print(f"종목 코드 {stock_code}의 스크래핑 상태를 업데이트하는 중 에러 발생: {e}")
        finally:
            session.close()

    def has_trading_data_for_date(self, stock_code, trading_date):
        """
        특정 종목 코드에 대해 특정 거래 일자에 시세 데이터가 있는지 확인하는 함수.

        :param stock_code: 종목 코드
        :param trading_date: 거래 일자 (문자열 형식: 'YYYY-MM-DD')
        :return: 해당 일자에 데이터가 있으면 True, 없으면 False
        """
        session = self.Session()
        try:
            # 해당 거래 일자의 데이터가 있는지 확인
            result = session.query(StockPrice).filter(
                StockPrice.stock_code == stock_code,
                StockPrice.trading_date == trading_date
            ).first()

            return result is not None
        except Exception as e:
            print(f"거래 일자 확인 중 에러 발생: {e}")
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

    def add_or_update_stock_prices(self, stock_records):
        """
        여러 개의 시세 정보를 일괄 추가하거나 업데이트하는 메서드
        :param stock_records: [{ 'stock_code': ..., 'trading_date': ..., 'open': ..., 'high': ..., 'low': ..., 'close': ..., 'volume': ... }, ...]
        """
        session = self.Session()
        try:
            for stock_data in stock_records:
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
            print(f"{len(stock_records)}개의 시세 데이터가 성공적으로 저장되었습니다.")
        except SQLAlchemyError as e:
            session.rollback()
            print(f"시세 데이터를 저장하는 중 에러 발생: {e}")
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

    def scrape_and_save_for_date(self, trading_date):
        """특정 일자의 시세 데이터를 스크래핑하여 DB에 저장하는 메서드"""
        print(f"종목 코드 {self.stock_code}의 {trading_date} 데이터를 스크래핑 시작...")

        try:
            # 스크래핑할 목표 날짜
            target_date = datetime.strptime(trading_date, '%Y-%m-%d').date()

            # 첫 번째 페이지의 데이터를 가져옴
            stock_data_df = self.scraper.fetch_page(1)

            # 스크래핑된 데이터가 없으면 종료
            if stock_data_df.empty or '날짜' not in stock_data_df.columns:
                print(f"종목 코드 {self.stock_code}에서 데이터를 찾을 수 없습니다.")
                return

            # 스크래핑된 데이터의 열 이름 맞춤 및 날짜 필터링
            stock_data_df.columns = stock_data_df.columns.str.strip()
            stock_data_df['trading_date'] = pd.to_datetime(stock_data_df['날짜'], format='%Y.%m.%d').dt.date

            # 목표 날짜와 일치하는 데이터를 찾음
            matching_data = stock_data_df[stock_data_df['trading_date'] == target_date]

            # 해당 날짜의 데이터가 없으면 종료
            if matching_data.empty:
                print(f"{trading_date}에 해당하는 데이터가 없습니다.")
                return

            # 필요한 데이터만 선택
            stock_data_df = matching_data[['trading_date', '종가', '시가', '고가', '저가', '거래량']].rename(
                columns={'종가': 'close', '시가': 'open', '고가': 'high', '저가': 'low', '거래량': 'volume'})

            # 데이터를 일괄 처리로 저장
            stock_records = [
                {
                    'stock_code': self.stock_code,
                    'trading_date': row['trading_date'],
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close'],
                    'volume': int(row['volume'])
                }
                for _, row in stock_data_df.iterrows()
            ]

            # 데이터베이스에 저장 (일괄 처리)
            self.db_handler.add_or_update_stock_prices(stock_records)

            logging.info(f"스크래핑 완료! 종목 코드 {self.stock_code}, 날짜 {target_date}")

            # 스크래핑 완료 후, scraping_results 테이블에 마지막 거래 일자를 업데이트
            self.db_handler.update_scraping_result(self.stock_code, target_date, status='COMPLETED')

        except Exception as e:
            print(f"스크래핑 중 에러 발생: {e}")

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
    # 스크래핑할 종목 코드와 특정 일자 설정
    trading_date = '2024-09-30'  # 스크래핑할 특정 일자

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

    # 7. 스크래핑 결과를 준비 상태로 업데이트
    db_handler.reset_scraping_status_for_old_entries(trading_date)

    # 8. 등록된 상장 회사 목록을 순차적으로 처리하여 시세 데이터 스크래핑 및 저장
    for stock_code in company_stock_codes:
        try:
            # 1. 스크래핑 상태에 등록되어 있는지 확인
            is_registered = db_handler.is_stock_code_registered(stock_code)

            # 2. 스크래핑 상태에 등록되지 않은 경우 새로 스크래핑 처리
            if not is_registered:
                print(f"종목 코드 {stock_code}는 스크래핑 상태에 등록되지 않았습니다. 새로 스크래핑을 시작합니다.")
                stock_scraper = StockScraper(db_handler, stock_code)
                stock_scraper.scrape_and_save_for_date(trading_date)
                continue  # 새로운 종목은 바로 스크래핑 후 다음으로 넘어감

            # 3. 특정 일자 이후로 스크래핑이 완료된 경우 건너뛰기
            is_completed = db_handler.is_scraping_completed_for_date_and_after(stock_code, trading_date)
            if is_completed:
                print(f"종목 코드 {stock_code}는 {trading_date} 이후로 이미 스크래핑 완료 상태입니다. 스킵합니다.")
                logging.info(f"종목 코드 {stock_code} 스크래핑 완료 상태, {trading_date} 이후 건너뜀.")
                continue

            # 4. 최근 7일 간의 시세 데이터 확인
            has_recent_data = db_handler.has_recent_weekly_data(stock_code, trading_date)

            if not has_recent_data:
                # 최근 7일간 데이터가 없으면 스크래핑 상태를 종료 처리하고 다음 종목으로 넘어감
                print(f"종목 코드 {stock_code}는 최근 7일간의 데이터가 없습니다. 스크래핑 상태를 종료 처리합니다.")
                db_handler.terminate_scraping(stock_code)
                continue

            # 5. 특정 일자의 데이터가 없는 경우 스크래핑 처리
            if db_handler.has_trading_data_for_date(stock_code, trading_date):
                print(f"종목 코드 {stock_code}는 {trading_date}에 이미 거래 데이터가 있습니다. 다음으로 넘어갑니다.")
                continue

            # 6. 특정 일자의 데이터가 없는 경우 스크래핑 처리
            stock_scraper = StockScraper(db_handler, stock_code)

            # 요청 간 간격을 두기 위해 랜덤하게 1~2초 대기
            time.sleep(random.uniform(1, 2))

            stock_scraper.scrape_and_save_for_date(trading_date)

        except Exception as e:
            print(f"종목 코드 {stock_code} 스크래핑 중 에러 발생: {e}")
            logging.error(f"종목 코드 {stock_code}, 거래일자 {trading_date} 스크래핑 중 에러 발생: {e}")


if __name__ == '__main__':
    main()
