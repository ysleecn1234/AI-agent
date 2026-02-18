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
        }
    }

    public clearToken() {
        this.token = null;
        if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
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

        if (typeof window !== 'undefined') {
            localStorage.setItem('access_token', response.access_token);
            // Optional: Store other user info if needed for API client internal use
            // But main app logic should handle storage for UI 
        }
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

    public async uploadDocument(file: File, visibility: 'private' | 'team' | 'public'): Promise<Document> {
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

        // Content-Type header must be removed to let browser set boundary for FormData
        const headers: any = { ...(this.token ? { 'Authorization': `Bearer ${this.token}` } : {}) };

        const response = await fetch(`${API_BASE_URL}/drive/documents/upload`, {
            method: 'POST',
            headers,
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }

        return response.json();
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
    public async getAgents(): Promise<Agent[]> {
        return this.request<Agent[]>('/agents');
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
        conversationHistory?: Array<{ role: string; content: string }>
    ): Promise<Agent[]> {
        const payload = { query, conversation_history: conversationHistory ?? undefined };
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
}

export const api = ApiClient.getInstance();
