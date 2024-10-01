from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd
from urllib.parse import quote_plus
import os


# DatabaseHandler 클래스 정의
class DatabaseHandler:
    def __init__(self, db_url):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)

    def get_stock_code_by_company_name(self, company_name):
        """
        상장 회사 이름으로 종목 코드를 조회하는 메서드
        :param company_name: 조회할 회사 이름 (문자열)
        :return: 종목 코드 (문자열) 또는 None
        """
        session = self.Session()
        try:
            query = text("""
                SELECT stock_code FROM companies
                WHERE name = :company_name
            """)
            result = session.execute(query, {'company_name': company_name}).fetchone()

            if result:
                return result[0]  # stock_code 반환
            else:
                print(f"회사 이름 '{company_name}'에 해당하는 종목 코드를 찾을 수 없습니다.")
                return None
        except SQLAlchemyError as e:
            print(f"데이터 조회 중 에러 발생: {e}")
            return None
        finally:
            session.close()

    def get_daily_price(self, stock_code, start_date, end_date):
        """
        종목코드, 시작일자, 종료일자를 매개변수로 하여
        해당 기간 동안의 일별 시세 데이터를 DataFrame으로 반환하는 메서드.

        :param stock_code: 조회할 종목 코드 (문자열)
        :param start_date: 조회 시작 일자 (YYYY-MM-DD 형식)
        :param end_date: 조회 종료 일자 (YYYY-MM-DD 형식)
        :return: pandas DataFrame (columns: ['trading_date', 'open', 'high', 'low', 'close', 'volume'])
        """
        session = self.Session()
        try:
            query = text("""
                SELECT trading_date, open, high, low, close, volume
                FROM stock_prices
                WHERE stock_code = :stock_code
                AND trading_date BETWEEN :start_date AND :end_date
                ORDER BY trading_date ASC
            """)

            result = session.execute(query, {
                'stock_code': stock_code,
                'start_date': start_date,
                'end_date': end_date
            })

            # 결과를 pandas DataFrame으로 변환
            df = pd.DataFrame(result.fetchall(), columns=['trading_date', 'open', 'high', 'low', 'close', 'volume'])

            # trading_date를 datetime 형식으로 변환
            df['trading_date'] = pd.to_datetime(df['trading_date'])

            return df

        except SQLAlchemyError as e:
            print(f"데이터 조회 중 에러 발생: {e}")
            return pd.DataFrame()  # 에러 발생 시 빈 DataFrame 반환

        finally:
            session.close()


def get_db_url():
    """
    환경 변수에서 DB URL을 가져오는 함수
    :return: SQLAlchemy 연결 URL 문자열
    """
    return os.getenv('DATABASE_URL', 'mysql+pymysql://user:password@localhost/investor')


# StockPriceFetcher 클래스 정의 (고객 인터페이스 제공)
class StockPriceFetcher:
    def __init__(self, db_handler):
        self.db_handler = db_handler

    def get_price_by_company(self, company_name, start_date, end_date):
        """
        회사 이름으로 해당 종목의 일별 시세 데이터를 조회하여 반환
        :param company_name: 조회할 회사 이름 (문자열)
        :param start_date: 조회 시작 일자 (YYYY-MM-DD 형식)
        :param end_date: 조회 종료 일자 (YYYY-MM-DD 형식)
        :return: pandas DataFrame (일별 시세 데이터)
        """
        # 1. 회사 이름으로 종목 코드 조회
        stock_code = self.db_handler.get_stock_code_by_company_name(company_name)

        if stock_code:
            # 2. 종목 코드로 일별 시세 데이터 조회
            return self.db_handler.get_daily_price(stock_code, start_date, end_date)
        else:
            return pd.DataFrame()  # 종목 코드가 없으면 빈 DataFrame 반환

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

# 메인 실행 로직
if __name__ == "__main__":
    # 예시: 삼성전자 종목의 2024년 1월 1일부터 9월 30일까지의 일별 시세 데이터 조회
    company_name = '삼성전자'
    start_date = '2024-09-12'
    end_date = '2024-09-30'

    # 1. 비밀번호를 URL 인코딩
    password = get_password()
    if not password:
        print("비밀번호를 가져오지 못했습니다. 프로그램을 종료합니다.")
        # 비밀번호가 없으면 프로그램 종료
        exit()


    # 2. MySQL 연결 URL 구성
    db_url = f'mysql+pymysql://investor:{password}@127.0.0.1:3306/investor'

    # 3. DatabaseHandler 인스턴스 생성
    db_handler = DatabaseHandler(db_url)

    # 4. StockPriceFetcher 인스턴스 생성
    fetcher = StockPriceFetcher(db_handler)

    df = fetcher.get_price_by_company(company_name, start_date, end_date)

    if not df.empty:
        print(df)
    else:
        print(f"{company_name}에 대한 시세 데이터를 찾을 수 없습니다.")
