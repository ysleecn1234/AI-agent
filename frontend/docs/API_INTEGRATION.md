# API Integration Guide

이 문서는 프론트엔드에서 백엔드 API를 호출하는 방법을 설명합니다.

## 📁 파일 구조

```
frontend/
├── .env.local              # 환경 변수 (API URL)
├── types/
│   └── api.ts             # TypeScript 타입 정의
├── lib/
│   ├── api.ts             # API 클라이언트 (저수준)
│   └── services.ts        # API 서비스 (고수준)
└── app/
    └── (페이지들)
```

## 🔧 설정

### 1. 환경 변수 (`.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_ENV=development
```

## 📝 사용 방법

### 기본 패턴

```typescript
import { authService, driveService, agentService, chatService } from '@/lib/services';

// 1. API 호출
try {
    const result = await authService.login({ email, password });
    // 성공 처리
} catch (error) {
    // 에러 처리
    console.error(error);
}
```

## 🔐 인증 (Auth)

### 로그인

```typescript
import { authService } from '@/lib/services';

const handleLogin = async () => {
    try {
        const response = await authService.login({
            email: 'user@example.com',
            password: 'password123'
        });
        
        // 토큰 저장 (자동으로 localStorage에 저장됨)
        localStorage.setItem('access_token', response.access_token);
        localStorage.setItem('user_name', response.user_name);
        localStorage.setItem('department', response.department);
        
        // 페이지 이동
        router.push('/chat');
    } catch (error) {
        alert('로그인 실패');
    }
};
```

### 회원가입

```typescript
const handleRegister = async () => {
    try {
        const response = await authService.register({
            email: 'user@example.com',
            password: 'password123',
            name: '홍길동',
            department: '개발팀'
        });
        
        // 자동 로그인 처리
        localStorage.setItem('access_token', response.access_token);
        router.push('/chat');
    } catch (error) {
        alert('회원가입 실패');
    }
};
```

### 로그아웃

```typescript
const handleLogout = () => {
    authService.logout();
    router.push('/auth/login');
};
```

## 📁 AI Drive

### 문서 목록 조회

```typescript
import { driveService } from '@/lib/services';

const fetchDocuments = async () => {
    try {
        const { documents } = await driveService.getDocuments();
        setDocuments(documents);
    } catch (error) {
        console.error('문서 조회 실패:', error);
    }
};
```

### 파일 업로드

```typescript
const handleUpload = async (file: File, visibility: 'private' | 'team' | 'public') => {
    try {
        const result = await driveService.uploadDocument(file, visibility);
        alert(result.message);
        fetchDocuments(); // 목록 새로고침
    } catch (error) {
        alert('업로드 실패');
    }
};
```

### 문서 상세 조회

```typescript
const fetchDocumentDetail = async (id: string) => {
    try {
        const document = await driveService.getDocumentDetail(id);
        setDocument(document);
    } catch (error) {
        console.error('문서 조회 실패:', error);
    }
};
```

### 문서 채팅

```typescript
const handleSendMessage = async (documentId: string, message: string) => {
    try {
        const response = await driveService.chatWithDocument(documentId, message);
        setMessages([...messages, { role: 'assistant', content: response.response }]);
    } catch (error) {
        console.error('채팅 실패:', error);
    }
};
```

### 문서 삭제 (아카이브로 이동)

```typescript
const handleDelete = async (id: string) => {
    if (!confirm('이 문서를 아카이브로 이동하시겠습니까?')) return;
    
    try {
        await driveService.deleteDocument(id);
        fetchDocuments(); // 목록 새로고침
    } catch (error) {
        alert('삭제 실패');
    }
};
```

### 아카이브 목록 조회

```typescript
const fetchArchivedDocuments = async () => {
    try {
        const { documents } = await driveService.getArchivedDocuments();
        setArchivedDocuments(documents);
    } catch (error) {
        console.error('아카이브 조회 실패:', error);
    }
};
```

### 문서 복원

```typescript
const handleRestore = async (id: string) => {
    try {
        await driveService.restoreDocument(id);
        fetchArchivedDocuments(); // 목록 새로고침
    } catch (error) {
        alert('복원 실패');
    }
};
```

### 문서 영구 삭제

```typescript
const handlePermanentDelete = async (id: string) => {
    if (!confirm('정말로 영구 삭제하시겠습니까?')) return;
    
    try {
        await driveService.permanentDeleteDocument(id);
        fetchArchivedDocuments(); // 목록 새로고침
    } catch (error) {
        alert('영구 삭제 실패');
    }
};
```

## 🤖 Agent Hub

### 에이전트 목록 조회

```typescript
import { agentService } from '@/lib/services';

const fetchAgents = async () => {
    try {
        const { agents } = await agentService.getAgents();
        setAgents(agents);
    } catch (error) {
        console.error('에이전트 조회 실패:', error);
    }
};
```

### 에이전트 생성

```typescript
const handleCreateAgent = async () => {
    try {
        const result = await agentService.createAgent({
            name: '마케팅 에이전트',
            description: '마케팅 전략 수립을 도와주는 에이전트',
            category: 'marketing',
            visibility: 'team',
            system_prompt: '당신은 마케팅 전문가입니다...'
        });
        
        alert(result.message);
        router.push(`/agents/${result.id}`);
    } catch (error) {
        alert('에이전트 생성 실패');
    }
};
```

### 에이전트 삭제

```typescript
const handleDeleteAgent = async (id: string) => {
    if (!confirm('이 에이전트를 삭제하시겠습니까?')) return;
    
    try {
        await agentService.deleteAgent(id);
        fetchAgents(); // 목록 새로고침
    } catch (error) {
        alert('삭제 실패');
    }
};
```

### 에이전트 추천

```typescript
const handleRecommendAgents = async (message: string) => {
    try {
        const { agents } = await agentService.recommendAgents(message);
        setRecommendedAgents(agents);
    } catch (error) {
        console.error('추천 실패:', error);
    }
};
```

## 💬 Chat

### 메시지 전송

```typescript
import { chatService } from '@/lib/services';

const handleSendMessage = async (message: string) => {
    try {
        const response = await chatService.sendMessage({
            message,
            model: 'auto', // 또는 특정 모델
            agent_id: selectedAgentId, // 선택적
            document_ids: selectedDocumentIds, // 선택적
        });
        
        setMessages([
            ...messages,
            { role: 'user', content: message },
            { role: 'assistant', content: response.response }
        ]);
    } catch (error) {
        console.error('메시지 전송 실패:', error);
    }
};
```

### 채팅 저장

```typescript
const handleSaveChat = async () => {
    try {
        const result = await chatService.saveChat({
            title: '프로젝트 기획 논의',
            messages: messages
        });
        
        alert('채팅이 저장되었습니다');
    } catch (error) {
        alert('저장 실패');
    }
};
```

## 🔄 Mock 데이터 → 실제 API 전환

기존 코드에서 Mock 데이터를 사용하던 부분을 실제 API로 전환하는 방법:

### Before (Mock)

```typescript
const fetchDocuments = async () => {
    // Mock 데이터
    setDocuments([
        { id: '1', name: '문서1.pdf', ... },
        { id: '2', name: '문서2.docx', ... }
    ]);
};
```

### After (Real API)

```typescript
import { driveService } from '@/lib/services';

const fetchDocuments = async () => {
    try {
        const { documents } = await driveService.getDocuments();
        setDocuments(documents);
    } catch (error) {
        console.error('문서 조회 실패:', error);
        // 에러 시 Mock 데이터로 폴백 (선택적)
        setDocuments([
            { id: '1', name: '문서1.pdf', ... },
            { id: '2', name: '문서2.docx', ... }
        ]);
    }
};
```

## 🐛 에러 처리

모든 API 호출은 try-catch로 감싸서 에러를 처리하세요:

```typescript
try {
    const result = await driveService.getDocuments();
    // 성공 처리
} catch (error) {
    if (error instanceof Error) {
        console.error('에러 메시지:', error.message);
        alert(error.message);
    }
}
```

## 🔑 인증 토큰

- API 클라이언트가 자동으로 `localStorage`에서 토큰을 가져와서 요청에 포함합니다
- `requireAuth: false` 옵션으로 인증 없이 호출 가능 (로그인/회원가입)

```typescript
// 인증 필요 (기본값)
await driveService.getDocuments();

// 인증 불필요
await authService.login({ email, password });
```

## 📌 주의사항

1. **환경 변수**: `.env.local` 파일은 Git에 커밋하지 마세요 (`.gitignore`에 포함)
2. **에러 처리**: 모든 API 호출은 try-catch로 감싸세요
3. **토큰 관리**: 로그인 성공 시 토큰을 localStorage에 저장하세요
4. **타입 안전성**: TypeScript 타입을 활용하여 타입 안전성을 확보하세요
