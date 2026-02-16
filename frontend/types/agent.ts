export interface Agent {
    id: string;
    name: string;
    description: string;
    icon: string;
    model: string;
    creator: string;
    department: string;
    status: 'draft' | 'published';
    tags: string[];
    updatedAt: string;
    usageCount: number;
    isPublic: boolean;
}

export const MOCK_AGENTS: Agent[] = [
    {
        id: '1',
        name: '마케팅 카피라이터',
        description: '제품 상세 페이지와 광고 문구를 작성하는 전문 에이전트입니다. 브랜드 톤앤매너를 준수합니다.',
        icon: '✍️',
        model: 'GPT-4o',
        creator: '김철수',
        department: '마케팅팀',
        status: 'published',
        tags: ['마케팅', '글쓰기', 'SNS'],
        updatedAt: '2024-01-15T09:00:00Z',
        usageCount: 1250,
        isPublic: true
    },
    {
        id: '2',
        name: '데이터 분석가',
        description: '엑셀 및 CSV 데이터를 분석하고 시각화 제안을 해주는 에이전트입니다.',
        icon: '📊',
        model: 'Claude-3.5-Sonnet',
        creator: '이영희',
        department: '데이터팀',
        status: 'published',
        tags: ['데이터', '분석', '통계'],
        updatedAt: '2024-01-20T14:30:00Z',
        usageCount: 890,
        isPublic: true
    },
    {
        id: '3',
        name: '코드 리뷰어',
        description: 'Python 및 TypeScript 코드의 버그를 찾고 리팩토링을 제안합니다.',
        icon: '💻',
        model: 'Gemini-1.5-Pro',
        creator: '박준호',
        department: '개발팀',
        status: 'draft',
        tags: ['개발', '코드리뷰', '버그잡기'],
        updatedAt: '2024-02-01T10:00:00Z',
        usageCount: 45,
        isPublic: false
    },
    {
        id: '4',
        name: 'HR 규정 챗봇',
        description: '사내 취업규칙과 복리후생에 대해 답변해주는 챗봇입니다.',
        icon: '🏢',
        model: 'GPT-4o-mini',
        creator: '인사팀',
        department: '인사팀',
        status: 'published',
        tags: ['HR', '사내규정', '복지'],
        updatedAt: '2024-01-10T11:20:00Z',
        usageCount: 3200,
        isPublic: true
    },
    {
        id: '5',
        name: '회의록 요약 비서',
        description: '길고 복잡한 회의 녹취록을 핵심 안건 위주로 요약합니다.',
        icon: '📝',
        model: 'Claude-3-Haiku',
        creator: '정민수',
        department: '영업팀',
        status: 'published',
        tags: ['업무보조', '요약', '회의'],
        updatedAt: '2024-02-05T16:45:00Z',
        usageCount: 150,
        isPublic: false
    }
];

export interface AgentDraft {
    name: string;
    description: string;
    goal: string;
    model: string;
    systemPrompt: string;
    ragEnabled: boolean;
    knowledgeBaseId?: string;
    category: string;
    visibility: 'private' | 'team' | 'public';
    messages?: Array<{ role: 'user' | 'assistant'; content: string }>;
}
