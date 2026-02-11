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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
    public async getDocuments(): Promise<Document[]> {
        return this.request<Document[]>('/drive/documents');
    }

    public async getDocument(id: string): Promise<DocumentDetail> {
        return this.request<DocumentDetail>(`/drive/documents/${id}`);
    }

    public async uploadDocument(file: File, visibility: 'private' | 'team' | 'public'): Promise<Document> {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('visibility', visibility);

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

    // Agent
    public async getAgents(): Promise<Agent[]> {
        return this.request<Agent[]>('/agents');
    }

    public async getAgent(id: string): Promise<AgentDetail> {
        return this.request<AgentDetail>(`/agents/${id}`);
    }

    public async createAgentDraft(data: CreateAgentRequest): Promise<Agent> {
        return this.request<Agent>('/agents/draft', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }
}

export const api = ApiClient.getInstance();
