import { apiClient, API_ENDPOINTS } from './api';
import type {
    LoginRequest,
    RegisterRequest,
    AuthResponse,
    Document,
    DocumentDetail,
    ArchivedDocument,
    DocumentChatRequest,
    DocumentChatResponse,
    Agent,
    AgentDetail,
    CreateAgentRequest,
    ChatRequest,
    ChatResponse,
} from '@/types/api';

// ==========================================
// Auth Service
// ==========================================

export const authService = {
    async login(data: LoginRequest): Promise<AuthResponse> {
        return apiClient.post<AuthResponse>(API_ENDPOINTS.AUTH.LOGIN, data, { requireAuth: false });
    },

    async register(data: RegisterRequest): Promise<AuthResponse> {
        return apiClient.post<AuthResponse>(API_ENDPOINTS.AUTH.REGISTER, data, { requireAuth: false });
    },

    logout() {
        if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_name');
            localStorage.removeItem('department');
        }
    },
};

// ==========================================
// Drive Service
// ==========================================

export const driveService = {
    async getDocuments(): Promise<{ documents: Document[] }> {
        return apiClient.get<{ documents: Document[] }>(API_ENDPOINTS.DRIVE.DOCUMENTS);
    },

    async uploadDocument(file: File, visibility: 'private' | 'team' | 'public'): Promise<{ id: string; name: string; message: string }> {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('visibility', visibility);

        return apiClient.upload(API_ENDPOINTS.DRIVE.UPLOAD, formData);
    },

    async getDocumentDetail(id: string): Promise<DocumentDetail> {
        return apiClient.get<DocumentDetail>(API_ENDPOINTS.DRIVE.DOCUMENT_DETAIL(id));
    },

    async chatWithDocument(id: string, question: string): Promise<DocumentChatResponse> {
        return apiClient.post<DocumentChatResponse>(
            API_ENDPOINTS.DRIVE.DOCUMENT_CHAT(id),
            { question } as DocumentChatRequest
        );
    },

    async deleteDocument(id: string): Promise<{ message: string }> {
        return apiClient.delete<{ message: string }>(API_ENDPOINTS.DRIVE.DELETE(id));
    },

    async getArchivedDocuments(): Promise<{ documents: ArchivedDocument[] }> {
        return apiClient.get<{ documents: ArchivedDocument[] }>(API_ENDPOINTS.DRIVE.ARCHIVE);
    },

    async restoreDocument(id: string): Promise<{ message: string }> {
        return apiClient.post<{ message: string }>(API_ENDPOINTS.DRIVE.RESTORE(id));
    },

    async permanentDeleteDocument(id: string): Promise<{ message: string }> {
        return apiClient.delete<{ message: string }>(API_ENDPOINTS.DRIVE.PERMANENT_DELETE(id));
    },

    async saveChatToDrive(content: string, title?: string): Promise<{ success: boolean; doc_id: string; message: string }> {
        const user_id = typeof window !== 'undefined' ? localStorage.getItem('user_id') || '' : '';
        const department = typeof window !== 'undefined' ? localStorage.getItem('department') || '' : '';

        return apiClient.post('/drive/documents/chat-save', {
            content,
            title,
            creator_id: user_id,
            creator_department: department,
            visibility: 'team'
        });
    },

    async saveAgentResultToDrive(content: string, agentName: string, title?: string): Promise<{ success: boolean; doc_id: string; message: string }> {
        const user_id = typeof window !== 'undefined' ? localStorage.getItem('user_id') || '' : '';
        const department = typeof window !== 'undefined' ? localStorage.getItem('department') || '' : '';

        return apiClient.post('/drive/documents/agent-save', {
            content,
            title,
            creator_id: user_id,
            creator_department: department,
            agent_name: agentName,
            visibility: 'team'
        });
    },
};

// ==========================================
// Agent Service
// ==========================================

export const agentService = {
    async getAgents(): Promise<{ agents: Agent[] }> {
        return apiClient.get<{ agents: Agent[] }>(API_ENDPOINTS.AGENT.LIST);
    },

    async createAgent(data: CreateAgentRequest): Promise<{ id: string; message: string }> {
        return apiClient.post<{ id: string; message: string }>(API_ENDPOINTS.AGENT.CREATE, data);
    },

    async getAgentDetail(id: string): Promise<AgentDetail> {
        return apiClient.get<AgentDetail>(API_ENDPOINTS.AGENT.DETAIL(id));
    },

    async updateAgent(id: string, data: Partial<CreateAgentRequest>): Promise<{ message: string }> {
        return apiClient.put<{ message: string }>(API_ENDPOINTS.AGENT.UPDATE(id), data);
    },

    async deleteAgent(id: string): Promise<{ message: string }> {
        return apiClient.delete<{ message: string }>(API_ENDPOINTS.AGENT.DELETE(id));
    },

    async recommendAgents(message: string): Promise<{ agents: Agent[] }> {
        return apiClient.post<{ agents: Agent[] }>(API_ENDPOINTS.AGENT.RECOMMEND, { message });
    },
};

// ==========================================
// Chat Service
// ==========================================

export const chatService = {
    async sendMessage(data: ChatRequest): Promise<ChatResponse> {
        return apiClient.post<ChatResponse>(API_ENDPOINTS.CHAT.SEND, data);
    },

    async getChatHistory(): Promise<{ chats: any[] }> {
        return apiClient.get<{ chats: any[] }>(API_ENDPOINTS.CHAT.HISTORY);
    },

    async saveChat(data: { title: string; messages: any[] }): Promise<{ id: string; message: string }> {
        return apiClient.post<{ id: string; message: string }>(API_ENDPOINTS.CHAT.SAVE, data);
    },
};
