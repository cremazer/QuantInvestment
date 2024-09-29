from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus

# 비밀번호를 URL 인코딩
password = quote_plus('Moca813152!@')

# URL을 새로 구성
db_url = f'mysql+pymysql://investor:{password}@127.0.0.1:3306/investor'

try:
    # create_engine을 사용해 엔진 생성
    engine = create_engine(db_url)

    # 연결 테스트 (커넥션 생성)
    with engine.connect() as connection:
        print("SQLAlchemy를 통한 MySQL 연결 성공!")
except SQLAlchemyError as e:
    print(f"SQLAlchemy를 통한 MySQL 연결 실패: {e}")
