import pymysql

try:
    connection = pymysql.connect(
        host='127.0.0.1',
        user='investor',
        password='Moca813152!@',
        database='investor',
        port=3306
    )
    print("MySQL 연결 성공!")
    connection.close()
except pymysql.MySQLError as e:
    print(f"MySQL 연결 실패: {e}")
