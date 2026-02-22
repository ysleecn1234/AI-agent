'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Menu, User, MessageSquare, FolderOpen, Bot, Archive, Settings, LogOut, Search, Clock, ChevronRight } from 'lucide-react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';

interface ChatSession {
    session_id: string;
    title: string;
    last_at: string;
    first_at: string;
}

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    created_at: string;
}

export default function ChatHistoryPage() {
    const router = useRouter();
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [selectedSession, setSelectedSession] = useState<string | null>(null);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [isLoadingSessions, setIsLoadingSessions] = useState(true);
    const [isLoadingMessages, setIsLoadingMessages] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(false);

    const userName = typeof window !== 'undefined' ? localStorage.getItem('user_name') || '사용자' : '사용자';

    useEffect(() => {
        fetchSessions();
    }, []);

    const fetchSessions = async () => {
        setIsLoadingSessions(true);
        try {
            const data = await api.getChatSessions();
            setSessions(Array.isArray(data) ? data : []);
        } catch (err) {
            console.error('채팅 세션 로드 실패:', err);
            setSessions([]);
        } finally {
            setIsLoadingSessions(false);
        }
    };

    const loadMessages = async (sessionId: string) => {
        setSelectedSession(sessionId);
        setIsLoadingMessages(true);
        try {
            const data = await api.getChatSessionMessages(sessionId);
            setMessages((data.messages as ChatMessage[]) ?? []);
        } catch (err) {
            console.error('메시지 로드 실패:', err);
            setMessages([]);
        } finally {
            setIsLoadingMessages(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_name');
        localStorage.removeItem('department');
        router.push('/auth/login');
    };

    const formatDate = (iso: string) => {
        const d = new Date(iso);
        return d.toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' });
    };

    const formatTime = (iso: string) => {
        const d = new Date(iso);
        return d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
    };

    const filteredSessions = sessions.filter((s) =>
        !searchQuery || s.title.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const selectedSessionData = sessions.find((s) => s.session_id === selectedSession);

    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
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
                                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <MessageSquare className="w-5 h-5 text-blue-600" />
                                <span className="font-medium">채팅</span>
                            </button>
                            <button
                                onClick={() => { router.push('/chat/history'); setSidebarOpen(false); }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-left bg-blue-50 rounded-lg transition-colors"
                            >
                                <Clock className="w-5 h-5 text-blue-600" />
                                <span className="font-medium text-blue-600">채팅 기록</span>
                            </button>
                            <button
                                onClick={() => { router.push('/drive'); setSidebarOpen(false); }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <FolderOpen className="w-5 h-5 text-blue-600" />
                                <span className="font-medium">AI Drive</span>
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

                <h1 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <Clock className="w-5 h-5 text-blue-600" />
                    채팅 기록
                </h1>

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

            {/* Content */}
            <div className="flex flex-1 overflow-hidden">
                {/* Session List */}
                <div className="w-80 border-r border-gray-200 bg-white flex flex-col">
                    <div className="p-3 border-b border-gray-100">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                            <Input
                                placeholder="대화 검색..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-9 text-sm"
                            />
                        </div>
                    </div>
                    <div className="flex-1 overflow-y-auto">
                        {isLoadingSessions ? (
                            <div className="flex items-center justify-center py-12 text-gray-400 text-sm">로딩 중...</div>
                        ) : filteredSessions.length === 0 ? (
                            <div className="flex flex-col items-center justify-center py-12 text-gray-400 gap-2">
                                <MessageSquare className="w-8 h-8" />
                                <span className="text-sm">저장된 대화가 없습니다</span>
                            </div>
                        ) : (
                            filteredSessions.map((session) => (
                                <button
                                    key={session.session_id}
                                    onClick={() => loadMessages(session.session_id)}
                                    className={`w-full text-left px-4 py-3 border-b border-gray-100 hover:bg-blue-50 transition-colors flex items-start gap-3 ${
                                        selectedSession === session.session_id ? 'bg-blue-50 border-l-2 border-l-blue-600' : ''
                                    }`}
                                >
                                    <MessageSquare className="w-4 h-4 text-gray-400 mt-0.5 shrink-0" />
                                    <div className="flex-1 min-w-0">
                                        <p className="text-sm font-medium text-gray-800 truncate">{session.title}</p>
                                        <p className="text-xs text-gray-400 mt-0.5">{formatDate(session.last_at)}</p>
                                    </div>
                                    <ChevronRight className="w-4 h-4 text-gray-300 shrink-0 mt-0.5" />
                                </button>
                            ))
                        )}
                    </div>
                </div>

                {/* Message Detail */}
                <div className="flex-1 flex flex-col bg-gray-50 overflow-hidden">
                    {!selectedSession ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-gray-400 gap-3">
                            <Clock className="w-12 h-12" />
                            <p className="text-base font-medium">대화를 선택하세요</p>
                            <p className="text-sm">왼쪽 목록에서 과거 대화를 클릭하면 내용을 볼 수 있습니다</p>
                        </div>
                    ) : (
                        <>
                            {/* Session Header */}
                            <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-3">
                                <div>
                                    <p className="font-semibold text-gray-800 truncate max-w-xl">
                                        {selectedSessionData?.title}
                                    </p>
                                    <p className="text-xs text-gray-400">
                                        {selectedSessionData ? `${formatDate(selectedSessionData.first_at)} ${formatTime(selectedSessionData.first_at)}` : ''}
                                    </p>
                                </div>
                                <div className="ml-auto">
                                    <button
                                        onClick={() => router.push('/chat')}
                                        className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-700 font-medium"
                                    >
                                        <MessageSquare className="w-4 h-4" />
                                        새 채팅
                                    </button>
                                </div>
                            </div>

                            {/* Messages */}
                            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
                                {isLoadingMessages ? (
                                    <div className="text-center text-gray-400 py-8">로딩 중...</div>
                                ) : (
                                    messages.map((msg, i) => (
                                        <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                            <div
                                                className={`max-w-[70%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                                                    msg.role === 'user'
                                                        ? 'bg-blue-600 text-white'
                                                        : 'bg-white border border-gray-200 text-gray-800'
                                                }`}
                                            >
                                                <p className="whitespace-pre-wrap">{msg.content}</p>
                                                <p className={`text-xs mt-1 ${msg.role === 'user' ? 'text-blue-200' : 'text-gray-400'}`}>
                                                    {formatTime(msg.created_at)}
                                                </p>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
