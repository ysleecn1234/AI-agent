# LLM API 키 설정 가이드

**작성일:** 2026-02-08  
**대상:** Feature-Y 브랜치 사용자

---

## 🔑 API 키 설정 위치

### 1. `.env` 파일 생성

**위치:** 프로젝트 루트 디렉토리
```
AI-agent/
├── .env          ← 여기에 생성!
├── .env.template ← 템플릿 파일
├── core/
├── app/
└── ...
```

**생성 방법:**
```bash
# Windows (PowerShell)
Copy-Item .env.template -Destination .env

# Linux/Mac
cp .env.template .env
```

---

## 📝 API 키 입력 방법

### `.env` 파일 내용

```env
# ============================================
# LLM API Keys
# ============================================

# OpenAI (GPT-5, GPT-4o)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Anthropic (Claude 4.5)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Google (Gemini 3)
GOOGLE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# DeepSeek (DeepSeek-R1)
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ============================================
# Database & Storage
# ============================================

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_agent_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# Milvus
MILVUS_HOST=localhost
MILVUS_PORT=19530

# ============================================
# JWT & Security
# ============================================

JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 🎯 각 모델별 API 키 발급 방법

### 1. OpenAI (GPT-5)
**발급 사이트:** https://platform.openai.com/api-keys

1. OpenAI 계정 로그인
2. "API keys" 메뉴 클릭
3. "Create new secret key" 클릭
4. 키 복사 → `.env`의 `OPENAI_API_KEY`에 붙여넣기

**형식:** `sk-proj-...`

---

### 2. Anthropic (Claude 4.5)
**발급 사이트:** https://console.anthropic.com/settings/keys

1. Anthropic Console 로그인
2. "API Keys" 메뉴 클릭
3. "Create Key" 클릭
4. 키 복사 → `.env`의 `ANTHROPIC_API_KEY`에 붙여넣기

**형식:** `sk-ant-...`

---

### 3. Google (Gemini 3)
**발급 사이트:** https://makersuite.google.com/app/apikey

1. Google AI Studio 접속
2. "Get API key" 클릭
3. 프로젝트 선택 또는 생성
4. 키 복사 → `.env`의 `GOOGLE_API_KEY`에 붙여넣기

**형식:** `AIzaSy...`

---

### 4. DeepSeek (DeepSeek-R1)
**발급 사이트:** https://platform.deepseek.com/api_keys

1. DeepSeek 계정 로그인
2. "API Keys" 메뉴 클릭
3. "Create API Key" 클릭
4. 키 복사 → `.env`의 `DEEPSEEK_API_KEY`에 붙여넣기

**형식:** `sk-...`

---

## 🔧 코드에서 API 키가 사용되는 방식

### 자동 인식 (litellm)

**핵심:** `.env` 파일에 API 키를 설정하면 `litellm`이 **자동으로 인식**합니다!

```python
# core/pipeline.py

import litellm

# ✅ API 키를 직접 전달할 필요 없음!
# litellm이 환경변수에서 자동으로 읽어옴
response = litellm.completion(
    model="gpt-5",  # OPENAI_API_KEY 자동 사용
    messages=[{"role": "user", "content": "Hello"}]
)

response = litellm.completion(
    model="claude-sonnet-4-5-20250514",  # ANTHROPIC_API_KEY 자동 사용
    messages=[{"role": "user", "content": "Hello"}]
)

response = litellm.completion(
    model="gemini/gemini-3-flash",  # GOOGLE_API_KEY 자동 사용
    messages=[{"role": "user", "content": "Hello"}]
)

response = litellm.completion(
    model="deepseek/deepseek-r1",  # DEEPSEEK_API_KEY 자동 사용
    messages=[{"role": "user", "content": "Hello"}]
)
```

---

## 📍 API 키가 사용되는 코드 위치

### 1. Router (Gemini 3 Flash)
**파일:** `core/pipeline.py` Line 41-299
```python
class Router:
    def __init__(self):
        self.model = "gemini/gemini-3-flash"  # GOOGLE_API_KEY 사용
```

### 2. Reasoner (GPT-5, Gemini 3)
**파일:** `core/pipeline.py` Line 470-586
```python
model_mapping = {
    ComplexityLevel.SIMPLE.value: "gemini/gemini-3-flash",  # GOOGLE_API_KEY
    ComplexityLevel.COMPLEX.value: "gpt-5",                 # OPENAI_API_KEY
    ComplexityLevel.BULK.value: "gemini/gemini-3-pro"       # GOOGLE_API_KEY
}
```

### 3. Synthesizer (Claude 4.5)
**파일:** `core/pipeline.py` Line 589-651
```python
result = litellm.completion(
    model="claude-sonnet-4-5-20250514",  # ANTHROPIC_API_KEY 사용
    messages=[{"role": "user", "content": prompt}]
)
```

### 4. Guardrail (DeepSeek-R1)
**파일:** `core/pipeline.py` Line 696-817
```python
result = litellm.completion(
    model="deepseek/deepseek-r1",  # DEEPSEEK_API_KEY 사용
    messages=[{"role": "user", "content": prompt}]
)
```

---

## ✅ 설정 확인 방법

### 1. 환경변수 로드 확인
```python
# 테스트 스크립트
import os
from dotenv import load_dotenv

load_dotenv()

print("OpenAI:", "✅" if os.getenv("OPENAI_API_KEY") else "❌")
print("Anthropic:", "✅" if os.getenv("ANTHROPIC_API_KEY") else "❌")
print("Google:", "✅" if os.getenv("GOOGLE_API_KEY") else "❌")
print("DeepSeek:", "✅" if os.getenv("DEEPSEEK_API_KEY") else "❌")
```

### 2. Pipeline 테스트
```python
from core.pipeline import Pipeline

# Pipeline 초기화 (API 키 자동 로드)
pipeline = Pipeline(use_rag=False)

# 간단한 테스트
result = pipeline.process("Hello, test!")
print(result)
```

---

## ⚠️ 주의사항

### 1. `.env` 파일 보안
```bash
# .gitignore에 이미 추가되어 있음
.env
```

**절대 GitHub에 커밋하지 마세요!**

### 2. API 키 형식 확인
- OpenAI: `sk-proj-...` (최신 형식)
- Anthropic: `sk-ant-...`
- Google: `AIzaSy...`
- DeepSeek: `sk-...`

### 3. 환경변수 우선순위
1. `.env` 파일
2. 시스템 환경변수
3. 코드 내 직접 설정 (권장하지 않음)

---

## 🚀 빠른 시작

### 1단계: `.env` 파일 생성
```bash
cp .env.template .env
```

### 2단계: API 키 입력
```env
OPENAI_API_KEY=sk-proj-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_API_KEY=AIzaSy-your-key-here
DEEPSEEK_API_KEY=sk-your-key-here
```

### 3단계: 서버 실행
```bash
# 가상환경 활성화
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 서버 실행
uvicorn app.main:app --reload
```

### 4단계: 테스트
```bash
# 채팅 API 테스트
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'
```

---

## 💡 문제 해결

### API 키가 인식되지 않을 때
1. `.env` 파일이 프로젝트 루트에 있는지 확인
2. 환경변수 이름 확인 (대소문자 구분)
3. 서버 재시작

### 특정 모델만 실패할 때
1. 해당 API 키 형식 확인
2. API 키 유효성 확인 (발급 사이트에서)
3. 요금 한도 확인

---

## 📚 관련 문서

- [LLM API 통합 가이드](../docs/llm_api_integration.md)
- [Pipeline 구조](../core/README.md)
- [환경 설정](./.env.template)
