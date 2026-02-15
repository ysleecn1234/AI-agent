'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Badge } from '@/components/ui/badge';
import { Menu, User, Send, MessageSquare, FolderOpen, Bot, Settings, LogOut, Save, Sparkles, Archive, Copy, ThumbsUp, FileText, X } from 'lucide-react';
import { SaveToDriveModal, CreateAgentModal } from '@/components/chat-action-modals';
import { api } from '@/lib/api';
import type { Agent, ChatSource } from '@/types/api';

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    sources?: ChatSource[];
    liked?: boolean;
}

export default function ChatPage() {
    const router = useRouter();
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
    const [sessionId, setSessionId] = useState<string | null>(null);

    // 에이전트 실시간 추천 (디바운스)
    useEffect(() => {
        if (!message.trim() || message.length < 3) {
            setRecommendedAgents([]);
            return;
        }

        const timer = setTimeout(async () => {
            setIsLoadingAgents(true);
            try {
                const agents = await api.recommendAgents(message);
                setRecommendedAgents(agents);
            } catch (error) {
                console.error('Failed to fetch recommended agents:', error);
                setRecommendedAgents([]);
            } finally {
                setIsLoadingAgents(false);
            }
        }, 500); // 500ms 디바운스

        return () => clearTimeout(timer);
    }, [message]);

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
                context_id: sessionId || undefined,
            });

            // session_id 저장 (대화 이어가기)
            setSessionId(response.session_id);

            setMessages(prev => [...prev, { 
                role: 'assistant', 
                content: response.response,
                sources: response.sources || [],
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
                    // Show top 5 agents when no input
                    const agents = await api.getAgents();
                    setRecommendedAgents(agents.slice(0, 5));
                } else {
                    // Use backend recommendation API
                    try {
                        const recommended = await api.recommendAgents(message);
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
                }
            } catch (error) {
                console.error('Failed to fetch agents:', error);
                setRecommendedAgents([]);
            } finally {
                setIsLoadingAgents(false);
            }
        }, 500); // 500ms debounce

        return () => clearTimeout(timeoutId);
    }, [agentEnabled, message]);

    const handleSelectAgent = (agent: Agent) => {
        setAgentId(agent.id);
    };

    const handleDeselectAgent = () => {
        setAgentId(undefined);
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
        try {
            const content = data.scope === 'single' && selectedMessageIndex !== null
                ? messages[selectedMessageIndex].content
                : messages.map(m => `${m.role}: ${m.content}`).join('\n\n');

            // API 연동: 드라이브 저장
            const creatorId = typeof window !== 'undefined' ? localStorage.getItem('user_name') || 'anonymous' : 'anonymous';
            const creatorDept = typeof window !== 'undefined' ? localStorage.getItem('department') || 'general' : 'general';

            await api.saveChatToDrive({
                content,
                creator_id: creatorId,
                creator_department: creatorDept,
                title: data.title,
                description: data.description,
                visibility: data.visibility
            });

            alert('드라이브에 저장되었습니다!');
            setSaveModalOpen(false);
        } catch (error) {
            console.error('Save failed:', error);
            alert('저장에 실패했습니다.');
        }
    };

    const handleAgentConfirm = async (data: {
        scope: 'single' | 'all';
        name: string;
        description: string;
        category: string;
        visibility: 'private' | 'team' | 'public';
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

            // 3. Step1 업데이트 (이름, 설명 등)
            await api.updateAgentStep1({
                draft_id: draftResponse.draft_id,
                name: data.name,
                description: data.description,
                input_example: selectedMessages[0]?.content || '',
                output_example: selectedMessages[1]?.content || ''
            });

            // 4. Step2 업데이트 (카테고리, 공개범위 등)
            await api.updateAgentStep2({
                draft_id: draftResponse.draft_id,
                category: data.category,
                visibility: data.visibility,
                model_type: 'gpt-4o-mini',
                use_rag: false,
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
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
                {/* Sidebar Trigger */}
                <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
                    <SheetTrigger asChild>
                        <button className="p-2 hover:bg-gray-100 rounded-lg">
                            <Menu className="w-6 h-6 text-gray-700" />
                        </button>
                    </SheetTrigger>
                    <SheetContent side="left" className="w-[300px] sm:w-[400px]">
                        <SheetHeader>
                            <SheetTitle className="flex items-center gap-2">
                                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                                    <span className="text-white text-lg font-bold">ISOR</span>
                                </div>
                                <span>AI 플랫폼</span>
                            </SheetTitle>
                        </SheetHeader>
                        <nav className="mt-8 space-y-2">
                            <button
                                onClick={() => { router.push('/chat'); setSidebarOpen(false); }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-left bg-blue-50 rounded-lg transition-colors"
                            >
                                <MessageSquare className="w-5 h-5 text-blue-600" />
                                <span className="font-medium text-blue-600">채팅</span>
                            </button>
                            <button
                                onClick={() => { router.push('/drive'); setSidebarOpen(false); }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <FolderOpen className="w-5 h-5 text-blue-600" />
                                <span className="font-medium">AI Drive</span>
                            </button>
                            <button
                                onClick={() => { router.push('/drive/archive'); setSidebarOpen(false); }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <Archive className="w-5 h-5 text-blue-600" />
                                <span className="font-medium">아카이브</span>
                            </button>
                            <button
                                onClick={() => { router.push('/agents'); setSidebarOpen(false); }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <Bot className="w-5 h-5 text-blue-600" />
                                <span className="font-medium">Agent Hub</span>
                            </button>
                            <button
                                onClick={() => { router.push('/settings'); setSidebarOpen(false); }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <Settings className="w-5 h-5 text-blue-600" />
                                <span className="font-medium">설정</span>
                            </button>
                        </nav>
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
                                            <ReactMarkdown>{msg.content}</ReactMarkdown>
                                        </div>
                                    ) : (
                                        <p className="whitespace-pre-wrap">{msg.content}</p>
                                    )}
                                </div>

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
                {/* Selected Agent Badge */}
                {agentId && (
                    <div className="flex items-center gap-2 p-2 bg-blue-50 border border-blue-200 rounded-lg">
                        <Bot className="w-4 h-4 text-blue-600" />
                        <span className="text-sm text-blue-900 flex-1">
                            {recommendedAgents.find(a => a.id === agentId)?.name || 'Agent 선택됨'}
                        </span>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleDeselectAgent}
                            className="h-6 w-6 p-0"
                        >
                            <X className="w-3 h-3" />
                        </Button>
                    </div>
                )}

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
                                    className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${
                                        agentId === agent.id
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
                    <Select value={selectedModel} onValueChange={setSelectedModel}>
                        <SelectTrigger className="w-[220px]">
                            <SelectValue placeholder="모델 선택" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="AUTO">⚡ Auto (자동 선택)</SelectItem>
                            <SelectItem value="GPT_5_2">💎 GPT 5.2 (Thinking)</SelectItem>
                            <SelectItem value="GEMINI_3_PRO">💎 Gemini 3 Pro</SelectItem>
                            <SelectItem value="PERPLEXITY">💎 Perplexity Sonar Pro</SelectItem>
                            <SelectItem value="OPUS_4_6">💎 Claude Opus 4.6</SelectItem>
                            <SelectItem value="gpt-4o-mini">GPT-4o-mini</SelectItem>
                            <SelectItem value="claude-sonnet">Claude Sonnet 3.5</SelectItem>
                            <SelectItem value="gemini-flash">Gemini 1.5 Flash</SelectItem>
                        </SelectContent>
                    </Select>

                    {/* Agent Activation Checkbox */}
                    <div className="flex items-center gap-2">
                        <Checkbox
                            id="agent-enabled"
                            checked={agentEnabled}
                            onCheckedChange={(checked) => setAgentEnabled(checked as boolean)}
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
            />
        </div>
    );
}
