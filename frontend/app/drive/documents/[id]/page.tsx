'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Menu, User, Send, ArrowLeft, MessageSquare, FolderOpen, Bot, Settings, LogOut, Archive } from 'lucide-react';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

interface DocumentData {
    id: string;
    name: string;
    type: string;
    content: string;
    url?: string;
}

export default function DocumentDetailPage() {
    const router = useRouter();
    const params = useParams();
    const documentId = params.id as string;

    const [document, setDocument] = useState<DocumentData | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [message, setMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(false);

    const userName = typeof window !== 'undefined' ? localStorage.getItem('user_name') || '사용자' : '사용자';

    useEffect(() => {
        fetchDocument();
    }, [documentId]);

    const fetchDocument = async () => {
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`http://localhost:8000/drive/documents/${documentId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) throw new Error('Failed to fetch document');

            const data = await response.json();
            setDocument(data);
        } catch (error) {
            console.error('Error fetching document:', error);
            // Mock data for development
            setDocument({
                id: documentId,
                name: '프로젝트 기획서.pdf',
                type: 'pdf',
                content: '이 문서는 프로젝트 기획서입니다.\n\n주요 내용:\n1. 프로젝트 개요\n2. 목표 및 범위\n3. 일정 계획\n4. 예산 계획',
            });
        }
    };

    const handleSendMessage = async () => {
        if (!message.trim() || isLoading) return;

        const userMessage = message;
        setMessage('');
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setIsLoading(true);

        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`http://localhost:8000/drive/documents/${documentId}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({ question: userMessage }),  // Changed from 'message' to 'question'
            });

            if (!response.ok) throw new Error('Failed to send message');

            const data = await response.json();
            setMessages(prev => [...prev, { role: 'assistant', content: data.answer }]);  // Changed from 'response' to 'answer'
        } catch (error) {
            console.error('Error sending message:', error);
            // Mock response for development
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: '이 문서에 대한 질문에 답변드리겠습니다. 현재 백엔드 API가 연결되지 않아 Mock 응답입니다.'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_name');
        localStorage.removeItem('department');
        router.push('/auth/login');
    };

    if (!document) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">문서를 불러오는 중...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    {/* Back Button */}
                    <button
                        onClick={() => router.push('/drive')}
                        className="p-2 hover:bg-gray-100 rounded-lg"
                    >
                        <ArrowLeft className="w-6 h-6 text-gray-700" />
                    </button>

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
                                        <span className="text-white text-lg font-bold">IN7</span>
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
                                    onClick={() => { router.push('/drive'); setSidebarOpen(false); }}
                                    className="w-full flex items-center gap-3 px-4 py-3 text-left bg-blue-50 rounded-lg transition-colors"
                                >
                                    <FolderOpen className="w-5 h-5 text-blue-600" />
                                    <span className="font-medium text-blue-600">AI Drive</span>
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

                    {/* Document Title */}
                    <h1 className="text-lg font-semibold text-gray-900">{document.name}</h1>
                </div>

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

            {/* Split View */}
            <div className="flex-1 flex overflow-hidden">
                {/* Left: Document Viewer (50%) */}
                <div className="w-1/2 border-r border-gray-200 bg-white overflow-y-auto p-6">
                    <div className="max-w-3xl mx-auto">
                        <div className="prose prose-sm max-w-none">
                            {document.type === 'pdf' && document.url ? (
                                <iframe
                                    src={document.url}
                                    className="w-full h-[800px] border border-gray-200 rounded-lg"
                                    title={document.name}
                                />
                            ) : (
                                <pre className="whitespace-pre-wrap font-sans text-gray-800">
                                    {document.content}
                                </pre>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right: AI Chat (50%) */}
                <div className="w-1/2 flex flex-col bg-gray-50">
                    {/* Chat Header */}
                    <div className="bg-white border-b border-gray-200 px-6 py-4">
                        <h2 className="text-lg font-semibold text-gray-900">문서 Q&A</h2>
                        <p className="text-sm text-gray-600">이 문서에 대해 질문하세요</p>
                    </div>

                    {/* Chat Messages */}
                    <div className="flex-1 overflow-y-auto p-6 space-y-4">
                        {messages.length === 0 ? (
                            <div className="flex items-center justify-center h-full">
                                <div className="text-center">
                                    <MessageSquare className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                                    <p className="text-gray-600">문서에 대해 질문해보세요</p>
                                </div>
                            </div>
                        ) : (
                            messages.map((msg, idx) => (
                                <div
                                    key={idx}
                                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                >
                                    <div
                                        className={`max-w-[80%] rounded-lg px-4 py-3 ${msg.role === 'user'
                                            ? 'bg-blue-600 text-white'
                                            : 'bg-white text-gray-800 border border-gray-200'
                                            }`}
                                    >
                                        <p className="whitespace-pre-wrap">{msg.content}</p>
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

                    {/* Chat Input */}
                    <div className="bg-white border-t border-gray-200 p-4">
                        <div className="relative">
                            <Textarea
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        handleSendMessage();
                                    }
                                }}
                                placeholder="문서에 대해 질문하세요..."
                                className="min-h-[60px] pr-12 resize-none"
                            />
                            <Button
                                onClick={handleSendMessage}
                                disabled={!message.trim() || isLoading}
                                size="icon"
                                className="absolute right-2 bottom-2 bg-blue-600 hover:bg-blue-700"
                            >
                                <Send className="w-4 h-4" />
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
