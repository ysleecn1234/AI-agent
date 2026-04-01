import pandas as pd
import joblib
import os
import sys
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score

# Add application directory to path if needed for relative imports to work when run directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from services.orchestrator.db.tables import MisclassificationLog

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_PATH = os.path.join(DATA_DIR, "intent_training_data_v2.csv")

def trigger_retrain(db):
    """
    1. 미사용 오분류 데이터 가져오기
    2. 기존 CSV에 추가
    3. 재학습 실행
    4. pkl 저장
    5. Router 모델 reload
    6. 사용된 로그 is_used=True로 마킹
    """

    # Step 1: 미사용 오분류 데이터 조회
    unused_logs = db.query(MisclassificationLog).filter(
        MisclassificationLog.is_used == False
    ).all()

    if len(unused_logs) < 100:
        return  # 안전장치

    # Step 2: 기존 학습 데이터 + 오분류 교정 데이터 합치기
    df_existing = pd.read_csv(CSV_PATH)

    new_rows = []
    for log in unused_logs:
        new_rows.append({
            "text": log.user_input,
            "label": log.correct_label  # 사용자가 지정한 올바른 라벨
        })
    df_new = pd.DataFrame(new_rows)
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)

    # 중복 제거 (동일 텍스트는 최신 라벨 우선)
    df_combined = df_combined.drop_duplicates(subset=["text"], keep="last")

    # Step 3: 재학습
    vectorizer = TfidfVectorizer(
        analyzer='char_wb',
        ngram_range=(2, 4),
        max_features=5000,
        sublinear_tf=True,
    )
    X_tfidf = vectorizer.fit_transform(df_combined['text'])

    svm = SVC(kernel='linear', C=1.0, probability=True, random_state=42)
    svm.fit(X_tfidf, df_combined['label'])

    # Step 4: 검증 (5-Fold CV)
    cv_scores = cross_val_score(svm, X_tfidf, df_combined['label'], cv=5)
    accuracy = cv_scores.mean()
    print(f"[Auto-Retrain] 재학습 완료: {len(df_combined)}건, 정확도: {accuracy:.4f}")

    # 정확도가 기존보다 떨어지면 중단 (안전장치)
    if accuracy < 0.85:
        print(f"[Auto-Retrain] 정확도 {accuracy:.4f} < 0.85 → 재학습 취소")
        return

    # Step 5: pkl 저장 + CSV 업데이트
    joblib.dump(vectorizer, os.path.join(DATA_DIR, "tfidf_vectorizer.pkl"))
    joblib.dump(svm, os.path.join(DATA_DIR, "svm_classifier.pkl"))
    df_combined.to_csv(CSV_PATH, index=False)

    # Step 6: Router 메모리 reload
    from application.usecases.orchestrator.service import orchestrator
    orchestrator.pipeline.router.reload_model()

    # Step 7: 사용된 로그 마킹
    for log in unused_logs:
        log.is_used = True
    db.commit()

    print(f"[Auto-Retrain] 전체 완료. 모델 즉시 반영됨.")
