import {
    LoginRequest,
    AuthResponse,
    RegisterRequest,
    ChatRequest,
    ChatResponse,
    Document,
    DocumentDetail,
    CreateAgentRequest,
    Agent,
    AgentDetail,
    ChatSaveRequest,
    AgentSaveRequest
} from '@/types/api';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://223.130.142.76:8000';

class ApiClient {
    private static instance: ApiClient;
    private token: string | null = null;

    private constructor() {
        if (typeof window !== 'undefined') {
            this.token = localStorage.getItem('access_token');
        }
    }

    public static getInstance(): ApiClient {
        if (!ApiClient.instance) {
            ApiClient.instance = new ApiClient();
        }
        return ApiClient.instance;
    }

    public setToken(token: string) {
        this.token = token;
        if (typeof window !== 'undefined') {
            localStorage.setItem('access_token', token);
            // middleware에서 인증 체크를 위해 쿠키에도 저장
            document.cookie = `access_token=${token}; path=/; max-age=${60 * 60 * 24 * 7}; SameSite=Lax`;
        }
    }

    public clearToken() {
        this.token = null;
        if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
            // 쿠키도 함께 제거
            document.cookie = 'access_token=; path=/; max-age=0; SameSite=Lax';
        }
    }

    private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
        // 매번 최신 토큰 읽기 (로그인 후 토큰 반영)
        if (typeof window !== 'undefined') {
            this.token = localStorage.getItem('access_token');
        }

        const headers: HeadersInit = {
            'Content-Type': 'application/json',
            ...(this.token ? { 'Authorization': `Bearer ${this.token}` } : {}),
            ...options.headers,
        };

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers,
        });

        if (!response.ok) {
            // 401 Unauthorized: 토큰 만료 또는 유효하지 않음
            if (response.status === 401) {
                this.clearToken();
                if (typeof window !== 'undefined') {
                    // 로그인 페이지로 리다이렉트 (현재 페이지 저장)
                    const currentPath = window.location.pathname;
                    if (currentPath !== '/auth/login' && currentPath !== '/auth/register') {
                        window.location.href = '/auth/login';
                    }
                }
            }

            const error = await response.json().catch(() => ({ message: 'Unknown error' }));
            throw new Error(error.message || `API Error: ${response.status}`);
        }

        return response.json();
    }

    // Auth
    public async login(data: LoginRequest): Promise<AuthResponse> {
        const response = await this.request<AuthResponse>('/auth/login', {
            method: 'POST',
            body: JSON.stringify(data),
        });

        // setToken을 통해 localStorage + 쿠키 동시 저장
        this.setToken(response.access_token);
        return response;
    }

    public async register(data: RegisterRequest): Promise<AuthResponse> {
        return this.request<AuthResponse>('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    // Chat
    public async sendMessage(data: ChatRequest): Promise<ChatResponse> {
        return this.request<ChatResponse>('/chat', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    public async getChatSessions(): Promise<{ session_id: string; title: string; last_at: string; first_at: string }[]> {
        return this.request('/chat/sessions');
    }

    public async getChatSessionMessages(sessionId: string): Promise<{ session_id: string; messages: { role: string; content: string; created_at: string }[] }> {
        return this.request(`/chat/sessions/${sessionId}`);
    }

    public async renameChatSession(sessionId: string, title: string): Promise<void> {
        return this.request(`/chat/sessions/${sessionId}/title`, {
            method: 'PUT',
            body: JSON.stringify({ title }),
        });
    }

    public async deleteChatSession(sessionId: string): Promise<void> {
        return this.request(`/chat/sessions/${sessionId}`, {
            method: 'DELETE',
        });
    }

    // Drive
    public async getDocuments(params?: { status?: string; limit?: number }): Promise<Document[]> {
        const q = new URLSearchParams();
        if (params?.status) q.set('status', params.status);
        if (params?.limit != null) q.set('limit', String(params.limit));
        const query = q.toString() ? `?${q.toString()}` : '';
        const response = await this.request<any>(`/drive/documents${query}`);
        return Array.isArray(response) ? response : (response.documents || []);
    }

    public async restoreDocument(docId: string): Promise<void> {
        return this.request<void>(`/drive/documents/${docId}/restore`, { method: 'POST' });
    }

    public async permanentDeleteDocument(docId: string): Promise<void> {
        return this.request<void>(`/drive/documents/${docId}/permanent`, { method: 'DELETE' });
    }

    public async getDocument(id: string): Promise<DocumentDetail> {
        return this.request<DocumentDetail>(`/drive/documents/${id}`);
    }

    public async uploadDocument(
        file: File,
        visibility: 'team' | 'public',
        onProgress?: (percent: number) => void
    ): Promise<Document> {
        // 매번 최신 토큰 읽기
        if (typeof window !== 'undefined') {
            this.token = localStorage.getItem('access_token');
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('visibility', visibility);

        // 백엔드 필수 필드 추가
        const creatorId = typeof window !== 'undefined' ? localStorage.getItem('user_id') || '' : '';
        const department = typeof window !== 'undefined' ? localStorage.getItem('department') || '개발팀' : '개발팀';

        formData.append('creator_id', creatorId);
        formData.append('creator_department', department);
        formData.append('description', '');
        formData.append('tags', '');

        // XMLHttpRequest로 업로드 진행률 추적
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', `${API_BASE_URL}/drive/documents/upload`);

            if (this.token) {
                xhr.setRequestHeader('Authorization', `Bearer ${this.token}`);
            }

            xhr.upload.onprogress = (e) => {
                if (e.lengthComputable && onProgress) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    onProgress(percent);
                }
            };

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(JSON.parse(xhr.responseText));
                } else {
                    // 서버 에러 메시지 추출 (FastAPI의 {"detail": "..."} 형식)
                    let message = `Upload failed: ${xhr.statusText}`;
                    try {
                        const body = JSON.parse(xhr.responseText);
                        if (body.detail) message = body.detail;
                    } catch { }
                    reject(new Error(message));
                }
            };

            xhr.onerror = () => reject(new Error('네트워크 오류'));
            xhr.send(formData);
        });
    }

    public async saveChatToDrive(data: ChatSaveRequest): Promise<any> {
        return this.request('/drive/documents/chat-save', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    public async deleteDocument(id: string): Promise<void> {
        return this.request<void>(`/drive/documents/${id}`, {
            method: 'DELETE',
        });
    }

    public async updateDocumentMetadata(
        id: string,
        data: {
            user_id: string;
            title?: string;
            description?: string;
            visibility?: 'private' | 'team' | 'public';
            tags?: string[];
        }
    ): Promise<any> {
        return this.request(`/drive/documents/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    // Agent
    public async getAgents(params?: { department?: string }): Promise<Agent[]> {
        const q = new URLSearchParams();
        if (params?.department) q.set('department', params.department);
        const query = q.toString() ? `?${q.toString()}` : '';
        return this.request<Agent[]>(`/agents/${query}`);
    }

    public async getAgent(id: string): Promise<AgentDetail> {
        return this.request<AgentDetail>(`/agents/${id}`);
    }

    public async createAgentDraft(data: CreateAgentRequest): Promise<{ status: string; draft_id: string; filled?: { name?: string; description?: string; category?: string; input_example?: string; output_example?: string; system_prompt?: string }; message: string }> {
        return this.request<{ status: string; draft_id: string; filled?: { name?: string; description?: string; category?: string; input_example?: string; output_example?: string; system_prompt?: string }; message: string }>('/agents/draft', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    public async updateAgentStep1(data: any): Promise<{ status: string }> {
        return this.request<{ status: string }>('/agents/draft/step1', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    public async updateAgentStep2(data: any): Promise<{ status: string }> {
        return this.request<{ status: string }>('/agents/draft/step2', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    public async publishAgent(data: { draft_id: string }): Promise<{ status: string; agent_id: string }> {
        return this.request<{ status: string; agent_id: string }>('/agents/publish', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    public async deleteAgent(id: string): Promise<void> {
        return this.request<void>(`/agents/${id}`, {
            method: 'DELETE',
        });
    }

    /**
     * 채팅 내용·대화 맥락 기반 에이전트 추천.
     * conversationHistory 있으면 POST로 전달해 맥락 반영 추천.
     */
    public async recommendAgents(
        query: string,
        conversationHistory?: Array<{ role: string; content: string }>,
        department?: string
    ): Promise<Agent[]> {
        const payload = {
            query,
            conversation_history: conversationHistory ?? undefined,
            department: department ?? undefined,
        };
        const res = await this.request<{ status: string; recommendations: Agent[] }>(
            '/agents/recommend',
            { method: 'POST', body: JSON.stringify(payload) }
        );
        return res.recommendations ?? [];
    }

    // Generate metadata
    public async generateDocumentMetadata(content: string): Promise<{ title: string; description: string }> {
        return this.request<{ title: string; description: string }>('/generate/document-metadata', {
            method: 'POST',
            body: JSON.stringify({ content }),
        });
    }

    public async generateAgentMetadata(content: string): Promise<{
        name: string;
        description: string;
        category: string
    }> {
        return this.request<{ name: string; description: string; category: string }>('/generate/agent-metadata', {
            method: 'POST',
            body: JSON.stringify({ content }),
        });
    }

    // Settings
    public async getSettings(): Promise<any> {
        return this.request<any>('/settings');
    }

    public async updateSettings(data: any): Promise<any> {
        return this.request<any>('/settings', {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    }
}

export const api = ApiClient.getInstance();
