import random
import string
from application.database import engine, Base, SessionLocal, InvitationCode

def main():
    print("[1] DB 테이블 구성 현행화 중 (InvitationCode 테이블 생성)...")
    Base.metadata.create_all(bind=engine)
    print("✓ 완료!")

    db = SessionLocal()
    try:
        # 기존 코드 개수 확인
        count = db.query(InvitationCode).count()
        if count >= 100:
            print(f"이미 DB에 {count}개의 코드가 존재합니다. 추가 생성을 건너뜁니다.")
        else:
            print(f"[2] 100개의 지정된 초대 코드 DB 삽입 중...")
            
            # 발급할 100개의 고정된 1회용 코드 리스트
            HARDCODED_CODES = [
                'CGA1YMJQ', 'YHOUT8DW', 'AKCRIQMZ', 'CU23DC7U', 'OXFEJX24', 'W6MWKPRY', 'MFRZMEOS', '1VJSERDO', 'H8PAKN0U', 'W4D4TCJM', 
                'FVMQQEDG', 'WFJ7ER26', '10OIDN81', '6ND0ATQO', '68WTI2Q5', '1Q56CCL6', 'A3RPV6BR', '6RXM0JQ2', 'OTOTWVTC', 'Q8GL7NU5', 
                'JBOQ0D4U', '59W4FR04', 'SBCDZ7WV', 'WUFIK4AT', '2TWNXCYS', 'UTU2BM0P', 'IU1LVAKX', 'X9A858R4', 'YH6MQAOX', 'TUTE9NU5', 
                'P1RWK274', '4TRXDWN9', 'SN6G2UKW', 'I7ZUN527', 'U0TK5JWW', '7Z4M9MKH', 'LVCOVTU6', 'NR367VHB', '9PO6IXCJ', '1NUD5UN2', 
                '9ZQRJ5AW', 'KU6K2661', 'VKWXBGLM', 'Z1CCHIB6', 'QFIR6XSA', 'LT2IKWK2', 'EIU75GXY', 'H5DQ6ALS', '5SU4YLB0', '4AN888CR', 
                '98QQ8743', '1K3VLRQ8', 'DWV2GBWR', 'RK179KXT', 'LTYK2VT7', '0BPKPKFA', '7NI0JRSY', 'VM99Y6XW', 'NX9XUAZD', 'KAM8NQTB', 
                'X07P2Q1I', 'K30GX825', 'RMPGPNG7', '9UIPCJDJ', 'ANH1LG6A', 'AGXQTQP0', 'TLBG639N', 'NT9DIQUF', '2D0SGY7F', 'IRQ9R9B4', 
                'D8B91750', 'SOBMLC6O', 'K4RX4IG9', '1BBK6981', 'YMI359X0', 'C5VFA0V8', 'VI4IWNXH', 'AUEKZD9T', 'VV1RI9VN', 'MILM1JVX', 
                'RUOGNQCP', 'AYPDCXBG', '7XU5UHP3', 'WI18N4RD', 'FI7VSX5P', 'FS3FA5XM', '42Y2HEU3', 'IZOVWGD5', 'SBMNVJSV', 'SAY2Y8F8', 
                '7AZDZI31', 'V74S4QS3', 'TY6S4T37', 'VM1ZGKIQ', '4SLTRH2D', 'DYEA3LE1', 'ZUJ2TJTY', '3F1VH8BI', '4XJNCSMI', 'UQ28CWGL'
            ]
            
            new_codes = []
            for fixed_code in HARDCODED_CODES:
                new_code = InvitationCode(code=fixed_code)
                new_codes.append(new_code)
            
            db.bulk_save_objects(new_codes)
            db.commit()
            print(f"✓ 성공: {len(new_codes)}개의 초대 코드가 DB에 안전하게 저장되었습니다.")
        
        # 3. DB에 담긴 상태 확인 (샘플 10개 출력)
        print("\n===============================")
        print("💡 DB 내 초대 코드 샘플 내역 💡")
        print("===============================")
        sample_codes = db.query(InvitationCode).limit(10).all()
        for idx, c in enumerate(sample_codes, 1):
            status = "❌ 사용됨 (재사용 불가)" if c.is_used else "✅ 사용 가능"
            print(f"{idx:02d}. [ {c.code} ] | 상태: {status}")
        print("===============================\n")

    except Exception as e:
        db.rollback()
        print(f"오류 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
