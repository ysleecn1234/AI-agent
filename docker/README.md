# 🐳 Docker 인프라 구성 가이드

이 문서는 AI Agent 플랫폼을 실행하기 위한 **Docker 인프라 아키텍처**와 **설정 파일(`docker-compose.yml`)**에 대한 상세 가이드입니다.
프로젝트 구동에 필요한 모든 서비스 컨테이너의 역할을 설명합니다.

---

## 1. 🏗️ 시스템 아키텍처 개요

본 프로젝트는 **4개의 핵심 서비스 컨테이너**로 구성되어 있습니다.

| 카테고리 | 서비스 명 | 역할 및 용도 | 기술 스택 |
| :--- | :--- | :--- | :--- |
| **App** | `backend` | **메인 웹 서버**. API 요청 처리 및 AI 로직 실행. | FastAPI (Python) |
| **DB** | `postgres` | **메인 데이터베이스**. 사용자, 에이전트, 로그 데이터 저장. | PostgreSQL 15 |
| **Cache** | `redis` | **캐시 저장소**. 로그인 세션 관리, 임시 데이터 처리. | Redis 7 |
| **AI** | `milvus` | **벡터 데이터베이스**. RAG 검색을 위한 문서 임베딩 저장소. | Milvus Standalone |

---

## 2. 📝 Docker-Compose 상세 분석

`docker/docker-compose.yml` 파일에 정의된 각 서비스의 상세 스펙과 설정입니다.

### 2.1 Backend (`in7-backend`)
*   **Port:** `8000:8000` (Localhost 8000번 포트로 접속 가능)
*   **Volume:** `..:/app`
    *   **프로젝트 루트 폴더 전체**를 컨테이너 내부 `/app`에 동기화합니다.
    *   따라서 `app/` 뿐만 아니라형제 폴더인 `core/`, `services/`의 코드도 컨테이너가 읽을 수 있습니다.
    *   코드 수정 시, 재빌드 없이 서버가 자동으로 변경 사항을 감지(Hot Reload)할 수 있습니다.
*   **Environment:** DB 및 Redis, Milvus 접속 정보를 환경 변수로 주입받습니다.

### 2.2 PostgreSQL (`in7-postgres`)
*   **Port:** `5432:5432`
*   **Volume:** `postgres_data:/var/lib/postgresql/data`
    *   컨테이너가 종료되거나 삭제되어도 DB 데이터는 영구 보존됩니다.
*   **Default Info:**
    *   User: `in7user`
    *   PW: `in7password`
    *   DB: `ai_hub`

### 2.3 Redis (`in7-redis`)
*   **Port:** `6379:6379`
*   **Volume:** `redis_data:/data` (데이터 영속성 보장)
*   **역할:** 고성능 인메모리 저장소로, 세션 및 작업 큐 관리에 사용됩니다.

### 2.4 Milvus Stack (`milvus-standalone`)
벡터 검색 엔진인 Milvus는 단독으로 실행되지 않으며 아래 의존성 컨테이너가 함께 실행됩니다.

*   **Milvus:** (`19530`, `9091`) 벡터 데이터를 처리하고 검색 쿼리를 수행합니다.
*   **Etcd:** Milvus 내부의 메타데이터(컬렉션 정보 등)를 관리합니다.
*   **MinIO:** (`9000`, `9001`) Milvus가 벡터 데이터를 파일 형태로 저장하는 객체 저장소(S3 호환)입니다.

---

## 3. 🚀 실행 및 배포 방법

프로젝트 루트 디렉토리의 배포 스크립트를 통해 원클릭으로 실행할 수 있습니다.

```bash
# 프로젝트 루트에서 실행
./deploy.sh
```

### `deploy.sh`가 하는 일
1.  **Git Pull:** 원격 저장소의 최신 코드 업데이트
2.  **Build:** `docker/docker-compose.yml`을 기반으로 이미지 빌드
3.  **Up:** 컨테이너 실행 및 백그라운드 구동 (`-d` 모드)

> **상태 확인 명령어:** `docker ps` 또는 `docker-compose -f docker/docker-compose.yml ps`
