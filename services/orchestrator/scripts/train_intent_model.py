"""
ISOR Router - TF-IDF + SVM 의도 분류기 학습
"""
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import classification_report
import joblib
import os

# 데이터 로드
DATA_PATH = os.path.join(os.path.dirname(__file__), "../data/intent_training_data_v2.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "../data")

df = pd.read_csv(DATA_PATH)
print(f"데이터: {len(df)}개, 분포:\n{df['label'].value_counts()}\n")

# Train/Test 분할
X_train, X_test, y_train, y_test = train_test_split(
    df['text'], df['label'], test_size=0.2, random_state=42, stratify=df['label']
)

# TF-IDF (char_wb: 한국어 어미 변형에 강건)
vectorizer = TfidfVectorizer(
    analyzer='char_wb',
    ngram_range=(2, 4),
    max_features=5000,
    sublinear_tf=True,
)
X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# SVM 학습
svm = SVC(kernel='linear', C=1.0, probability=True, random_state=42)
svm.fit(X_train_tfidf, y_train)

# 5-Fold 교차 검증
cv_scores = cross_val_score(svm, vectorizer.transform(df['text']), df['label'], cv=5)
print(f"5-Fold CV: {cv_scores.mean():.4f} (±{cv_scores.std():.4f})")

# 테스트셋 평가
y_pred = svm.predict(X_test_tfidf)
print(classification_report(y_test, y_pred))

# 모델 저장
joblib.dump(vectorizer, os.path.join(MODEL_DIR, "tfidf_vectorizer.pkl"))
joblib.dump(svm, os.path.join(MODEL_DIR, "svm_classifier.pkl"))
print("모델 저장 완료")
