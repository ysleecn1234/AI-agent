// ==========================================
// API Types
// ==========================================

// Auth
export interface LoginRequest {
    email: string;
    password: string;
}

export interface RegisterRequest {
    email: string;
    password: string;
    name: string;
    department: string;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
    user_name: string;
    department: string;
}

export interface User {
    id: string;
    email: string;
    name: string;
    department: string;
}

// Drive
export interface Document {
    id: string;
    name: string;
    type: string;
    creator: string;
    created_at: string;
    visibility: 'private' | 'team' | 'public';
    size: number;
}

export interface DocumentDetail extends Document {
    content?: string;
    url?: string;
}

export interface ArchivedDocument {
    id: string;
    name: string;
    type: string;
    deleted_at: string;
    days_remaining: number;
}

export interface UploadDocumentRequest {
    file: File;
    visibility: 'private' | 'team' | 'public';
}

export interface UpdateDocumentMetadataRequest {
    user_id: string;
    title?: string;
    description?: string;
    visibility?: 'private' | 'team' | 'public';
    tags?: string[];
}

export interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp?: string;
}

export interface DocumentChatRequest {
    question: string;
    user_id?: string;
}

export interface DocumentChatResponse {
    success: boolean;
    doc_id: string;
    question: string;
    answer: string;
    sources: any[];
    processing_time_ms: number;
}

// Drive Save Requests
export interface ChatSaveRequest {
    content: string;
    title?: string;
    creator_id: string;
    creator_department: string;
    description?: string;
    visibility?: string;
}

export interface AgentSaveRequest {
    content: string;
    title?: string;
    creator_id: string;
    creator_department: string;
    agent_name: string;
    description?: string;
    visibility?: string;
}

// Agent
export interface Agent {
    id: string;
    name: string;
    description: string;
    category: string;
    creator: string;
    created_at: string;
    visibility: 'private' | 'team' | 'public';
    is_active: boolean;
}

export interface AgentDetail extends Agent {
    system_prompt?: string;
    tools?: string[];
    examples?: string[];
}

export interface CreateAgentRequest {
    name: string;
    description: string;
    category: string;
    visibility: 'private' | 'team' | 'public';
    system_prompt?: string;
    selected_messages?: Array<{ role: string; content: string }>;
}

// Chat
export interface ChatRequest {
    message: string;
    model_type?: string;      // "AUTO" | "GPT-5" | "CLAUDE" | "GEMINI" | "DEEPSEEK"
    use_rag?: boolean;        // Drive 참조 활성화
    agent_id?: string;        // 특정 에이전트 사용
    context_id?: string;      // 대화 컨텍스트 ID
}

export interface ChatSource {
    id: string;
    title: string;
    score: number;
}

export interface ChatResponse {
    response: string;
    used_model: string;
    session_id: string;
    sources?: ChatSource[];
}

// API Response Wrapper
export interface ApiResponse<T> {
    data?: T;
    error?: string;
    message?: string;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
}
