CREATE TABLE companies
(
    id         INT AUTO_INCREMENT PRIMARY KEY NOT NULL COMMENT 'ID',
    name       VARCHAR(100)                   NOT NULL COMMENT '회사명',
    stock_code CHAR(6)                        NOT NULL COMMENT '종목코드',
    updated_at DATETIME COMMENT '최종 업데이트 날짜'
) COMMENT '회사 정보';
