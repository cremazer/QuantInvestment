import pandas as pd
import requests
from io import StringIO
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Date
from sqlalchemy.orm import declarative_base, sessionmaker  # 경로 수정
from urllib.parse import quote_plus
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9 이상에서 사용할 수 있는 표준 라이브러리

# SQLAlchemy Base 클래스
Base = declarative_base()

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

# 메인 프로세스
def main():
    # 비밀번호를 URL 인코딩
    password = quote_plus('Moca813152!@')

    # MySQL 연결 URL 구성
    db_url = f'mysql+pymysql://investor:{password}@127.0.0.1:3306/investor'
    db_handler = DatabaseHandler(db_url)

    # KRX 상장 회사 목록 스크래핑 URL
    scraper_url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method=download&searchType=13'
    scraper = CompanyScraper(scraper_url)

    # 상장 목록 데이터를 스크래핑
    company_data_list = scraper.scrape()

    # 데이터베이스에 저장 또는 업데이트
    for company_data in company_data_list:
        db_handler.add_or_update_company(company_data)

if __name__ == '__main__':
    main()
