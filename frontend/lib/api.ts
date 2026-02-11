// ==========================================
// API Configuration
// ==========================================

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// API Endpoints
export const API_ENDPOINTS = {
    // Auth
    AUTH: {
        LOGIN: '/auth/login',
        REGISTER: '/auth/register',
    },

    // Drive
    DRIVE: {
        DOCUMENTS: '/drive/documents',
        UPLOAD: '/drive/upload',
        DOCUMENT_DETAIL: (id: string) => `/drive/documents/${id}`,
        DOCUMENT_CHAT: (id: string) => `/drive/documents/${id}/chat`,
        DELETE: (id: string) => `/drive/documents/${id}`,
        ARCHIVE: '/drive/archive',
        RESTORE: (id: string) => `/drive/restore/${id}`,
        PERMANENT_DELETE: (id: string) => `/drive/permanent/${id}`,
    },

    // Agent
    AGENT: {
        LIST: '/agents',
        CREATE: '/agents',
        DETAIL: (id: string) => `/agents/${id}`,
        UPDATE: (id: string) => `/agents/${id}`,
        DELETE: (id: string) => `/agents/${id}`,
        RECOMMEND: '/agents/recommend',
    },

    // Chat
    CHAT: {
        SEND: '/chat',
        HISTORY: '/chat/history',
        SAVE: '/chat/save',
    },
} as const;

// ==========================================
// API Client
// ==========================================

interface RequestOptions extends RequestInit {
    requireAuth?: boolean;
}

class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    private getAuthToken(): string | null {
        if (typeof window === 'undefined') return null;
        return localStorage.getItem('access_token');
    }

    private async request<T>(
        endpoint: string,
        options: RequestOptions = {}
    ): Promise<T> {
        const { requireAuth = true, headers = {}, ...restOptions } = options;

        const config: RequestInit = {
            ...restOptions,
            headers: {
                'Content-Type': 'application/json',
                ...headers,
            },
        };

        // Add auth token if required
        if (requireAuth) {
            const token = this.getAuthToken();
            if (token) {
                config.headers = {
                    ...config.headers,
                    Authorization: `Bearer ${token}`,
                };
            }
        }

        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, config);

            // Handle non-OK responses
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
            }

            // Handle empty responses
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                return {} as T;
            }

            return await response.json();
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    }

    // GET request
    async get<T>(endpoint: string, options?: RequestOptions): Promise<T> {
        return this.request<T>(endpoint, { ...options, method: 'GET' });
    }

    // POST request
    async post<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
        return this.request<T>(endpoint, {
            ...options,
            method: 'POST',
            body: data ? JSON.stringify(data) : undefined,
        });
    }

    // PUT request
    async put<T>(endpoint: string, data?: any, options?: RequestOptions): Promise<T> {
        return this.request<T>(endpoint, {
            ...options,
            method: 'PUT',
            body: data ? JSON.stringify(data) : undefined,
        });
    }

    // DELETE request
    async delete<T>(endpoint: string, options?: RequestOptions): Promise<T> {
        return this.request<T>(endpoint, { ...options, method: 'DELETE' });
    }

    // Upload file (multipart/form-data)
    async upload<T>(endpoint: string, formData: FormData, options?: RequestOptions): Promise<T> {
        const { requireAuth = true, headers = {}, ...restOptions } = options || {};

        const config: RequestInit = {
            ...restOptions,
            method: 'POST',
            body: formData,
            headers: {
                ...headers,
                // Don't set Content-Type for FormData, browser will set it with boundary
            },
        };

        // Add auth token if required
        if (requireAuth) {
            const token = this.getAuthToken();
            if (token) {
                config.headers = {
                    ...config.headers,
                    Authorization: `Bearer ${token}`,
                };
            }
        }

        try {
            const response = await fetch(`${this.baseUrl}${endpoint}`, config);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Upload Error:', error);
            throw error;
        }
    }
}

// Export singleton instance
export const apiClient = new ApiClient(API_BASE_URL);

// Export default
export default apiClient;
