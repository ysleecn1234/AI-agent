'use client';

import { useState, useEffect, useCallback, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { AppSidebar } from '@/components/app-sidebar';
import type { ChatSession } from '@/types/api';
import { useRouter } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Menu, User, Send, MessageSquare, FolderOpen, Bot, Settings, LogOut, Save, Sparkles, Archive, Copy, ThumbsUp, FileText, X, Clock, Plus, Upload } from 'lucide-react';
import { SaveToDriveModal, CreateAgentModal } from '@/components/chat-action-modals';
import { api } from '@/lib/api';
import type { Agent, ChatSource } from '@/types/api';

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    sources?: ChatSource[];
    web_searched?: boolean;
    web_citations?: string[];
    liked?: boolean;
}

export default function ChatPage() {
    return (
        <Suspense fallback={<div className="flex h-screen items-center justify-center">Loading...</div>}>
            <ChatContent />
        </Suspense>
    );
}

function ChatContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
    const [sessionsLoading, setSessionsLoading] = useState(true);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [selectedModel, setSelectedModel] = useState('AUTO');
    const [agentId, setAgentId] = useState<string | undefined>(undefined);
    const [driveEnabled, setDriveEnabled] = useState(false);
    const [agentEnabled, setAgentEnabled] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [saveModalOpen, setSaveModalOpen] = useState(false);
    const [agentModalOpen, setAgentModalOpen] = useState(false);
    const [selectedMessageIndex, setSelectedMessageIndex] = useState<number | null>(null);
    const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
    const [recommendedAgents, setRecommendedAgents] = useState<Agent[]>([]);
    const [isLoadingAgents, setIsLoadingAgents] = useState(false);
    const [activeAgent, setActiveAgent] = useState<Agent | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [saveProgress, setSaveProgress] = useState(0);


    const loadSessions = useCallback(async () => {
        try {
            setSessionsLoading(true);
            const data = await api.getChatSessions();
            setSessions(data);
        } catch (error) {
            console.error('Failed to load sessions:', error);
        } finally {
            setSessionsLoading(false);
        }
    }, []);

    const loadSession = useCallback(async (sessionId: string) => {
        try {
            setIsLoading(true);
            const data = await api.getChatSessionMessages(sessionId);
            setMessages(data.messages as any);
            setCurrentSessionId(sessionId);
        } catch (error) {
            console.error('Failed to load session:', error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        loadSessions();
        const sessionParam = searchParams.get('session');
        if (sessionParam) {
            loadSession(sessionParam);
        }
        // Agent Hub에서 에이전트 실행 시 자동 활성화
        const agentParam = searchParams.get('agent');
        if (agentParam) {
            setAgentId(agentParam);
            setAgentEnabled(true);
            api.getAgent(agentParam).then((agent) => {
                setActiveAgent(agent);
                if (agent.model_type) setSelectedModel(agent.model_type);
                if (agent.use_rag) setDriveEnabled(true);
            }).catch(() => { });
        }
    }, [loadSessions, searchParams, loadSession]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleNewChat = () => {
        setMessages([]);
        setCurrentSessionId(null);
        setMessage('');
        router.push('/chat', { scroll: false });
        inputRef.current?.focus();
    };

    const handleSelectSession = (sessionId: string) => {
        if (sessionId === currentSessionId) return;
        loadSession(sessionId);
        router.push(`/chat?session=${sessionId}`, { scroll: false });
    };

    const handleNavigate = (path: string) => {
        router.push(path);
    };

    const handleRenameSession = async (sessionId: string, newTitle: string) => {
        try {
            await api.renameChatSession(sessionId, newTitle);
            // Update local state immediately
            setSessions(prev => prev.map(s =>
                s.session_id === sessionId ? { ...s, title: newTitle } : s
            ));
        } catch (error) {
            console.error('Failed to rename session:', error);
        }
    };

    const handleDeleteSession = async (sessionId: string) => {
        try {
            await api.deleteChatSession(sessionId);
            // Remove from local state
            setSessions(prev => prev.filter(s => s.session_id !== sessionId));
            // If deleted session is the current one, navigate to new chat
            if (currentSessionId === sessionId) {
                handleNewChat();
            }
        } catch (error) {
            console.error('Failed to delete session:', error);
        }
    };

    const handleSend = async () => {
        if (!message.trim() || isLoading) return;

        const userMessage = message;
        setMessage('');
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setIsLoading(true);

        try {
            // API 호출 (프리미엄 모델 지원)
            const response = await api.sendMessage({
                message: userMessage,
                model_type: selectedModel,
                use_rag: driveEnabled,
                agent_id: agentId,
                context_id: currentSessionId || undefined,
            });

            if (!currentSessionId && response.session_id) {
                setCurrentSessionId(response.session_id);
                // router.push 대신 history API 사용 → searchParams 변경 없이 URL만 업데이트 (useEffect 재실행 방지)
                window.history.replaceState(null, '', `/chat?session=${response.session_id}`);
            }
            loadSessions();


            setMessages(prev => [...prev, {
                role: 'assistant',
                content: response.response,
                sources: response.sources || [],
                web_searched: response.web_searched || false,
                web_citations: response.web_citations || [],
                liked: false
            }]);
        } catch (error) {
            console.error('Error sending message:', error);
            const errorMessage = error instanceof Error ? error.message : '메시지 전송에 실패했습니다.';
            setMessages(prev => [...prev, { role: 'assistant', content: `❌ 오류가 발생했습니다: ${errorMessage}` }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCopyMessage = async (content: string, index: number) => {
        try {
            await navigator.clipboard.writeText(content);
            setCopiedIndex(index);
            setTimeout(() => setCopiedIndex(null), 2000);
        } catch (error) {
            console.error('Failed to copy:', error);
            alert('복사에 실패했습니다.');
        }
    };

    const handleLikeMessage = (index: number) => {
        setMessages(prev => prev.map((msg, idx) =>
            idx === index ? { ...msg, liked: !msg.liked } : msg
        ));
    };

    // Agent recommendation with debounce
    useEffect(() => {
        if (!agentEnabled) {
            setRecommendedAgents([]);
            return;
        }

        const timeoutId = setTimeout(async () => {
            setIsLoadingAgents(true);
            try {
                if (!message.trim()) {
                    // 입력 없을 때 상위 5개 (같은 부서 우선)
                    const dept = typeof window !== 'undefined' ? localStorage.getItem('department') || undefined : undefined;
                    const agents = await api.getAgents({ department: dept });
                    setRecommendedAgents(agents.slice(0, 5));
                } else if (message.trim().length >= 3) {
                    // 채팅 맥락 + 부서 포함 추천 (최근 10개 메시지)
                    const conversationHistory = messages
                        .slice(-10)
                        .map((m) => ({ role: m.role, content: m.content }));
                    const dept = typeof window !== 'undefined' ? localStorage.getItem('department') || undefined : undefined;
                    try {
                        const recommended = await api.recommendAgents(message, conversationHistory, dept);
                        setRecommendedAgents(recommended.slice(0, 5));
                    } catch (error) {
                        // Fallback to client-side filtering if API not available
                        console.warn('Agent recommendation API not available, using fallback');
                        const agents = await api.getAgents();
                        const filtered = agents.filter(agent =>
                            agent.name.toLowerCase().includes(message.toLowerCase()) ||
                            agent.description.toLowerCase().includes(message.toLowerCase()) ||
                            agent.category?.toLowerCase().includes(message.toLowerCase())
                        ).slice(0, 5);
                        setRecommendedAgents(filtered.length > 0 ? filtered : agents.slice(0, 5));
                    }
                } else {
                    setRecommendedAgents([]);
                }
            } catch (error) {
                console.error('Failed to fetch agents:', error);
                setRecommendedAgents([]);
            } finally {
                setIsLoadingAgents(false);
            }
        }, 500); // 500ms debounce

        return () => clearTimeout(timeoutId);
    }, [agentEnabled, message, messages]);

    const handleSelectAgent = (agent: Agent) => {
        setAgentId(agent.id);

        // 에이전트 설정에 따라 Drive 참조 자동 전환
        setDriveEnabled(!!agent.use_rag);
    };

    const handleDeselectAgent = () => {
        setAgentId(undefined);
        setSelectedModel('AUTO');
        setDriveEnabled(false);
    };

    const handleLogout = () => {
        api.clearToken();
        router.push('/auth/login');
    };

    const handleSaveToDrive = (messageIndex: number) => {
        setSelectedMessageIndex(messageIndex);
        setSaveModalOpen(true);
    };

    const handleCreateAgent = (messageIndex: number) => {
        setSelectedMessageIndex(messageIndex);
        setAgentModalOpen(true);
    };

    const handleSaveConfirm = async (data: {
        scope: 'single' | 'all';
        title: string;
        description: string;
        visibility: 'private' | 'team' | 'public';
    }) => {
        setIsSaving(true);
        setSaveProgress(10);
        try {
            const content = data.scope === 'single' && selectedMessageIndex !== null
                ? messages[selectedMessageIndex].content
                : messages.map(m => `${m.role}: ${m.content}`).join('\n\n');

            // creator_id는 user_id(UUID) 사용 — user_name(한글)이 아님
            const creatorId = typeof window !== 'undefined' ? localStorage.getItem('user_id') || 'anonymous' : 'anonymous';
            const creatorDept = typeof window !== 'undefined' ? localStorage.getItem('department') || 'general' : 'general';

            setSaveProgress(30);
            await api.saveChatToDrive({
                content,
                creator_id: creatorId,
                creator_department: creatorDept,
                title: data.title,
                description: data.description,
                visibility: data.visibility
            });
            setSaveProgress(100);
            setSaveModalOpen(false);
            // 잠깐 100% 보여주고 닫기
            setTimeout(() => { setIsSaving(false); setSaveProgress(0); }, 600);
        } catch (error) {
            console.error('Save failed:', error);
            setIsSaving(false);
            setSaveProgress(0);
            alert('저장에 실패했습니다. 잠시 후 다시 시도해 주세요.');
        }
    };

    const handleAgentConfirm = async (data: {
        scope: 'single' | 'all';
        name: string;
        description: string;
        category: string;
        visibility: 'private' | 'team' | 'public';
        use_rag?: boolean;
        input_example?: string;
        output_example?: string;
        system_prompt?: string;
        model_type?: string;
    }) => {
        try {
            // 1. 선택된 메시지 준비
            const selectedMessages = data.scope === 'single' && selectedMessageIndex !== null
                ? [messages[selectedMessageIndex]].map(m => ({ role: m.role, content: m.content }))
                : messages.map(m => ({ role: m.role, content: m.content }));

            // 2. Draft 생성 (대화 내용만 전송)
            const draftResponse = await api.createAgentDraft({
                selected_messages: selectedMessages
            });

            // 3. Step1 업데이트 (이름, 입력/출력 예시)
            await api.updateAgentStep1({
                draft_id: draftResponse.draft_id,
                name: data.name,
                description: data.description,
                input_example: data.input_example || selectedMessages[0]?.content || '',
                output_example: data.output_example || selectedMessages[1]?.content || ''
            });

            // 4. Step2 업데이트 (카테고리, 공개범위, 모델, 문서참조)
            await api.updateAgentStep2({
                draft_id: draftResponse.draft_id,
                category: data.category,
                visibility: data.visibility.toUpperCase() as 'PRIVATE' | 'TEAM' | 'PUBLIC',
                model_type: data.model_type || 'AUTO',
                use_rag: data.use_rag ?? false,
                linked_doc_ids: []
            });

            // 5. 최종 발행
            const publishResponse = await api.publishAgent({
                draft_id: draftResponse.draft_id
            });

            alert('Agent가 생성되었습니다!');
            setAgentModalOpen(false);
            router.push(`/agents`);
        } catch (error) {
            console.error('Agent creation failed:', error);
            alert('Agent 생성에 실패했습니다.');
        }
    };

    // Get content for modals
    const getModalContent = () => {
        if (selectedMessageIndex === null) return '';
        return messages[selectedMessageIndex]?.content || '';
    };

    const userName = typeof window !== 'undefined' ? localStorage.getItem('user_name') || '사용자' : '사용자';

    return (

        <div className="flex h-screen bg-white">
            {/* 업로드 진행 토스트 */}
            {isSaving && (
                <div className="fixed top-4 right-4 z-50 bg-white border border-gray-200 rounded-xl shadow-lg px-5 py-4 w-72">
                    <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                            <Upload className="w-4 h-4 text-blue-600 animate-pulse" />
                        </div>
                        <div>
                            <p className="text-sm font-semibold text-gray-900">드라이브에 저장 중</p>
                            <p className="text-xs text-gray-500">임베딩 생성 및 업로드 중입니다...</p>
                        </div>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                        <div
                            className="h-2 bg-blue-600 rounded-full transition-all duration-700 ease-in-out"
                            style={{ width: `${saveProgress}%` }}
                        />
                    </div>
                    <p className="text-right text-xs text-blue-600 mt-1 font-medium">{saveProgress}%</p>
                </div>
            )}
            {/* 전체 화면 사이드바 기능용 Sheet, 그리고 메인 컨텐츠 영역 */}
            <div className="flex-1 flex flex-col min-w-0 bg-gray-50">

                {/* Header */}
                <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
                    {/* Sidebar Trigger */}
                    <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
                        <SheetTrigger asChild>
                            <button className="p-2 hover:bg-gray-100 rounded-lg">
                                <Menu className="w-6 h-6 text-gray-700" />
                            </button>
                        </SheetTrigger>
                        <SheetContent side="left" className="p-0 w-[280px]">
                            <AppSidebar
                                sessions={sessions}
                                currentSessionId={currentSessionId}
                                onSelectSession={handleSelectSession}
                                onNewChat={handleNewChat}
                                onNavigate={handleNavigate}
                                onRenameSession={handleRenameSession}
                                onDeleteSession={handleDeleteSession}
                                isLoadingSessions={sessionsLoading}
                                isMobile
                                onClose={() => setSidebarOpen(false)}
                                currentPath="/chat"
                            />
                        </SheetContent>
                    </Sheet>

                    {/* User Menu */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <button className="p-2 hover:bg-gray-100 rounded-lg">
                                <User className="w-6 h-6 text-gray-700" />
                            </button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-56">
                            <DropdownMenuLabel>
                                <div className="flex flex-col">
                                    <span className="font-medium">{userName}</span>
                                    <span className="text-sm text-gray-500">{typeof window !== 'undefined' ? localStorage.getItem('department') || '' : ''}</span>
                                </div>
                            </DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => router.push('/settings')}>
                                <Settings className="w-4 h-4 mr-2" />
                                설정
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                                <LogOut className="w-4 h-4 mr-2" />
                                로그아웃
                            </DropdownMenuItem>
                        </DropdownMenuContent>
                    </DropdownMenu>
                </header>

                {/* Chat Messages Area */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {messages.length === 0 ? (
                        <div className="flex items-center justify-center h-full">
                            {agentId ? (() => {
                                const agent = activeAgent || recommendedAgents.find(a => a.id === agentId);
                                return (
                                    <div className="text-center">
                                        <div className="w-20 h-20 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                                            <span className="text-white text-xl font-bold">ISOR</span>
                                        </div>
                                        <h2 className="text-2xl font-bold text-gray-800 mb-2">
                                            {agent?.name || '에이전트'}
                                        </h2>
                                        <p className="text-gray-600 max-w-md">
                                            {agent?.description || '에이전트가 활성화되었습니다'}
                                        </p>
                                        <p className="text-gray-400 text-sm mt-3">
                                            무엇을 도와드릴까요?
                                        </p>
                                    </div>
                                );
                            })() : (
                                <div className="text-center">
                                    <div className="w-20 h-20 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <span className="text-white text-3xl font-bold">ISOR</span>
                                    </div>
                                    <h2 className="text-2xl font-bold text-gray-800 mb-2">
                                        무엇을 도와드릴까요?
                                    </h2>
                                    <p className="text-gray-600">
                                        질문을 입력하시면 AI가 답변해드립니다
                                    </p>
                                </div>
                            )}
                        </div>
                    ) : (
                        messages.map((msg, idx) => (
                            <div
                                key={idx}
                                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                            >
                                <div className="max-w-[70%] space-y-2">
                                    <div
                                        className={`rounded-lg px-4 py-3 ${msg.role === 'user'
                                            ? 'bg-blue-600 text-white'
                                            : 'bg-white text-gray-800 border border-gray-200'
                                            }`}
                                    >
                                        {msg.role === 'assistant' ? (
                                            <div className="prose prose-sm max-w-none 
                                            prose-headings:font-semibold prose-headings:mb-2 prose-headings:mt-3
                                            prose-p:my-1.5 prose-p:leading-relaxed
                                            prose-ul:my-1.5 prose-ul:list-disc prose-ul:pl-5
                                            prose-ol:my-1.5 prose-ol:list-decimal prose-ol:pl-5
                                            prose-li:my-0.5
                                            prose-strong:font-semibold
                                            prose-code:bg-gray-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:font-mono
                                            prose-pre:bg-gray-900 prose-pre:text-gray-100 prose-pre:p-3 prose-pre:rounded prose-pre:my-2 prose-pre:overflow-x-auto
                                            prose-blockquote:border-l-2 prose-blockquote:border-gray-300 prose-blockquote:pl-3 prose-blockquote:italic prose-blockquote:text-gray-700
                                            prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline">
                                                <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                                            </div>
                                        ) : (
                                            <p className="whitespace-pre-wrap">{msg.content}</p>
                                        )}
                                    </div>

                                    {/* Web Search Citations (AI messages only) */}
                                    {msg.role === 'assistant' && msg.web_searched && msg.web_citations && msg.web_citations.length > 0 && (
                                        <div className="bg-green-50 border border-green-200 rounded-lg p-3 space-y-2">
                                            <div className="flex items-center gap-2 text-xs font-medium text-green-900">
                                                <span>🌐</span>
                                                <span>웹 검색 참조 ({msg.web_citations.length})</span>
                                            </div>
                                            <div className="space-y-1">
                                                {msg.web_citations.map((url, cIdx) => (
                                                    <div key={cIdx} className="text-xs">
                                                        <a
                                                            href={url}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="text-green-600 hover:underline truncate block"
                                                        >
                                                            {(() => {
                                                                try {
                                                                    const hostname = new URL(url).hostname.replace('www.', '');
                                                                    return hostname;
                                                                } catch {
                                                                    return url;
                                                                }
                                                            })()}
                                                        </a>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Web Search Badge (no citations) */}
                                    {msg.role === 'assistant' && msg.web_searched && (!msg.web_citations || msg.web_citations.length === 0) && (
                                        <div className="flex items-center gap-1.5 text-xs text-green-700 bg-green-50 border border-green-200 rounded-md px-2.5 py-1.5 w-fit">
                                            <span>🌐</span>
                                            <span>웹 검색 결과 반영</span>
                                        </div>
                                    )}

                                    {/* RAG Sources (AI messages only) */}
                                    {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 space-y-2">
                                            <div className="flex items-center gap-2 text-xs font-medium text-blue-900">
                                                <FileText className="w-3 h-3" />
                                                <span>참조 문서 ({msg.sources.length})</span>
                                            </div>
                                            <div className="space-y-1">
                                                {msg.sources.map((source, sIdx) => (
                                                    <div key={sIdx} className="flex items-center justify-between text-xs">
                                                        <button
                                                            onClick={() => router.push(`/drive/documents/${source.id}`)}
                                                            className="text-blue-600 hover:underline truncate flex-1 text-left"
                                                        >
                                                            {source.title}
                                                        </button>
                                                        <span className="text-gray-500 ml-2">
                                                            {Math.round(source.score * 100)}%
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Action Buttons (AI messages only) */}
                                    {msg.role === 'assistant' && (
                                        <div className="flex gap-2 flex-wrap">
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => handleCopyMessage(msg.content, idx)}
                                                className="text-xs h-7 px-2"
                                            >
                                                {copiedIndex === idx ? (
                                                    <>
                                                        <Copy className="w-3 h-3 mr-1" />
                                                        복사됨!
                                                    </>
                                                ) : (
                                                    <>
                                                        <Copy className="w-3 h-3 mr-1" />
                                                        복사
                                                    </>
                                                )}
                                            </Button>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => handleLikeMessage(idx)}
                                                className={`text-xs h-7 px-2 ${msg.liked ? 'text-blue-600' : ''}`}
                                            >
                                                <ThumbsUp className={`w-3 h-3 mr-1 ${msg.liked ? 'fill-blue-600' : ''}`} />
                                                {msg.liked ? '좋아요' : '좋아요'}
                                            </Button>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleSaveToDrive(idx)}
                                                className="text-xs h-7"
                                            >
                                                <Save className="w-3 h-3 mr-1" />
                                                저장
                                            </Button>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                onClick={() => handleCreateAgent(idx)}
                                                className="text-xs h-7"
                                            >
                                                <Sparkles className="w-3 h-3 mr-1" />
                                                Agent 생성
                                            </Button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))
                    )}
                    <div ref={messagesEndRef} />
                    {isLoading && (
                        <div className="flex justify-start">
                            <div className="bg-white border border-gray-200 rounded-lg px-4 py-3">
                                <div className="flex gap-2">
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* Input Area */}
                <div className="bg-white border-t border-gray-200 p-4 space-y-3">



                    {/* Agent Recommendations */}
                    {agentEnabled && recommendedAgents.length > 0 && (
                        <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-medium text-gray-700">
                                    {message.trim() ? '추천 Agent' : 'TOP Agent'}
                                </span>
                                {isLoadingAgents && (
                                    <div className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                                )}
                            </div>
                            <div className="flex flex-wrap gap-2">
                                {recommendedAgents.map((agent) => (
                                    <button
                                        key={agent.id}
                                        onClick={() => handleSelectAgent(agent)}
                                        className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${agentId === agent.id
                                            ? 'bg-blue-600 text-white border-blue-600'
                                            : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400 hover:bg-blue-50'
                                            }`}
                                    >
                                        {agent.name}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Message Input */}
                    <div className="relative">
                        <Textarea
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSend();
                                }
                            }}
                            placeholder="메시지를 입력하세요..."
                            className="min-h-[60px] pr-12 resize-none"
                            ref={inputRef}
                        />
                        <Button
                            onClick={handleSend}
                            disabled={!message.trim() || isLoading}
                            size="icon"
                            className="absolute right-2 bottom-2 bg-blue-600 hover:bg-blue-700"
                        >
                            <Send className="w-4 h-4" />
                        </Button>
                    </div>

                    {/* Bottom Controls */}
                    <div className="flex items-center gap-4 text-sm flex-wrap">
                        {/* Model Selector */}
                        {agentId ? (
                            <div className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 border border-gray-300 rounded-md text-gray-600 text-sm w-[220px]">
                                <span>🔒</span>
                                <span className="truncate">
                                    {(() => {
                                        const agent = recommendedAgents.find(a => a.id === agentId);
                                        const modelName = agent?.model_type || 'AUTO';
                                        const displayNames: Record<string, string> = {
                                            'AUTO': 'Auto (자동)',
                                            'gemini/gemini-2.5-flash-lite': 'Gemini 2.5 Flash Lite',
                                            'gemini/gemini-2.5-flash': 'Gemini 2.5 Flash',
                                            'gemini/gemini-3-flash-preview': 'Gemini 3 Flash',
                                            'gemini/gemini-3.1-pro-preview': 'Gemini 3.1 Pro',
                                            'gpt-5-nano': 'GPT-5 Nano',
                                            'gpt-5-mini': 'GPT-5 Mini',
                                            'gpt-5.2': 'GPT-5.2',
                                            'gpt-5.2-pro': 'GPT-5.2 Pro',
                                            'claude-haiku-4.5': 'Claude Haiku 4.5',
                                            'claude-sonnet-4-6': 'Claude Sonnet 4.6',
                                            'claude-opus-4-6': 'Claude Opus 4.6',
                                            'perplexity/sonar': 'Perplexity Sonar',
                                            'perplexity/sonar-pro': 'Perplexity Sonar Pro',
                                        };
                                        return displayNames[modelName] || modelName;
                                    })()}
                                </span>
                            </div>
                        ) : (
                            <Select value={selectedModel} onValueChange={setSelectedModel}>
                                <SelectTrigger className="w-[220px]">
                                    <SelectValue placeholder="모델 선택" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="AUTO">⚡ Auto (자동 선택)</SelectItem>
                                    <SelectItem value="GPT_5_2">GPT 5.2 (Thinking)</SelectItem>
                                    <SelectItem value="GEMINI_3_PRO">Gemini 3.1 Pro</SelectItem>
                                    <SelectItem value="PERPLEXITY">Perplexity Sonar Pro</SelectItem>
                                    <SelectItem value="OPUS_4_6">Claude Opus 4.6</SelectItem>
                                </SelectContent>
                            </Select>
                        )}

                        {/* Agent Activation Checkbox */}
                        <div className="flex items-center gap-2">
                            <Checkbox
                                id="agent-enabled"
                                checked={agentEnabled}
                                onCheckedChange={(checked) => {
                                    setAgentEnabled(checked as boolean);
                                    if (!checked) {
                                        handleDeselectAgent();
                                    }
                                }}
                            />
                            <label
                                htmlFor="agent-enabled"
                                className="text-gray-700 cursor-pointer select-none"
                            >
                                Agent 활성화
                            </label>
                        </div>

                        {/* Drive Reference Switch */}
                        <div className="flex items-center gap-2">
                            <div
                                onClick={() => setDriveEnabled(!driveEnabled)}
                                className={`relative w-11 h-6 rounded-full cursor-pointer transition-colors ${driveEnabled ? 'bg-blue-600' : 'bg-gray-300'
                                    }`}
                            >
                                <div
                                    className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${driveEnabled ? 'translate-x-5' : 'translate-x-0'
                                        }`}
                                />
                            </div>
                            <label className="text-gray-700 cursor-pointer select-none" onClick={() => setDriveEnabled(!driveEnabled)}>
                                Drive 참조
                            </label>
                        </div>
                    </div>
                </div>

                {/* Modals */}
                <SaveToDriveModal
                    isOpen={saveModalOpen}
                    onClose={() => setSaveModalOpen(false)}
                    onSave={handleSaveConfirm}
                    content={getModalContent()}
                />
                <CreateAgentModal
                    isOpen={agentModalOpen}
                    onClose={() => setAgentModalOpen(false)}
                    onCreate={handleAgentConfirm}
                    content={getModalContent()}
                    fullMessages={messages.map(m => ({ role: m.role, content: m.content }))}
                />
            </div>
        </div>
    );
}
