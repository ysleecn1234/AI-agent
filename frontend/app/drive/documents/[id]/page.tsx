'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Menu, User, Search, Play, FileText, Send, File, FileSpreadsheet, Presentation, LogOut, Settings, MessageSquare, FolderOpen, Bot, ArrowLeft, Edit, Download, Trash2, Maximize2, Minimize2, ZoomIn, ZoomOut, Check, X, Clock } from 'lucide-react';
import { AppSidebar } from '@/components/app-sidebar';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { api } from '@/lib/api';

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

// 백엔드 DocumentDetail 스펙
interface DocumentData {
    doc_id: string;
    title: string;
    description: string;
    creator_id: string;
    creator_department: string;
    created_at: string;
    modified_at: string;
    visibility: string;
    status: string;
    file_size: number;
    file_type: string;
    version: number;
    is_latest: boolean;
    tags: string[];
    filename: string;
    source_type: string;
    chunk_count: number;
}

export default function DocumentDetailPage() {
    const router = useRouter();
    const params = useParams();
    const documentId = (params?.id as string) ?? '';

    const [document, setDocument] = useState<DocumentData | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [message, setMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [editModalOpen, setEditModalOpen] = useState(false);
    const [editTitle, setEditTitle] = useState('');
    const [editDescription, setEditDescription] = useState('');
    const [editVisibility, setEditVisibility] = useState<'private' | 'team' | 'public'>('team');
    const [editTags, setEditTags] = useState('');
    const [fileUrl, setFileUrl] = useState<string | null>(null);

    const userName = typeof window !== 'undefined' ? localStorage.getItem('user_name') || '사용자' : '사용자';
    const userId = typeof window !== 'undefined' ? localStorage.getItem('user_name') || '' : '';

    useEffect(() => {
        if (!documentId) return;
        fetchDocument();
        fetchFilePreview();
    }, [documentId]);

    const fetchFilePreview = async () => {
        if (!documentId) return;
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://223.130.142.76:8000'}/drive/documents/${documentId}/file`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) throw new Error('Failed to fetch file');

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            setFileUrl(url);
        } catch (error) {
            console.error('Error fetching file preview:', error);
            setFileUrl(null);
        }
    };

    const fetchDocument = async () => {
        if (!documentId) return;
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://223.130.142.76:8000'}/drive/documents/${documentId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) throw new Error('Failed to fetch document');

            const data = await response.json();
            setDocument(data);
        } catch (error) {
            console.error('Error fetching document:', error);
            setDocument(null);
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
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://223.130.142.76:8000'}/drive/documents/${documentId}/chat`, {
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

    const handleOpenEditModal = () => {
        if (document) {
            setEditTitle(document.title);
            setEditDescription(document.description || '');
            setEditVisibility((document.visibility || 'team') as 'private' | 'team' | 'public');
            setEditTags((document.tags || []).join(', '));
            setEditModalOpen(true);
        }
    };

    const handleSaveMetadata = async () => {
        if (!document) return;

        try {
            const tagArray = editTags
                .split(',')
                .map(t => t.trim())
                .filter(t => t.length > 0);

            await api.updateDocumentMetadata(document.doc_id, {
                user_id: userId,
                title: editTitle,
                description: editDescription,
                visibility: editVisibility,
                tags: tagArray,
            });

            alert('문서 정보가 수정되었습니다!');
            setEditModalOpen(false);
            fetchDocument(); // 새로고침
        } catch (error) {
            console.error('Error updating metadata:', error);
            alert('문서 정보 수정에 실패했습니다.');
        }
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

    if (!documentId) {
        return (
            <div className="flex flex-col h-screen bg-gray-50 items-center justify-center">
                <p className="text-gray-500">문서 ID가 없습니다.</p>
                <Button variant="outline" onClick={() => router.push('/drive')} className="mt-4">Drive로 돌아가기</Button>
            </div>
        );
    }

    if (!document) {
        return (
            <div className="flex flex-col h-screen bg-gray-50 items-center justify-center">
                <p className="text-gray-500">문서를 불러오는 중...</p>
                <Button variant="outline" onClick={() => router.push('/drive')} className="mt-4">Drive로 돌아가기</Button>
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
                        <SheetContent side="left" className="p-0 w-[280px]">
                            <AppSidebar
                                onNavigate={(path) => router.push(path)}
                                isMobile
                                onClose={() => setSidebarOpen(false)}
                                currentPath={`/drive/documents/${documentId}`}
                            />
                        </SheetContent>
                    </Sheet>

                    {/* Document Title */}
                    <h1 className="text-lg font-semibold text-gray-900">{document.title}</h1>
                </div>

                <div className="flex items-center gap-2">
                    {/* Edit Button */}
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleOpenEditModal}
                        className="gap-2"
                    >
                        <Edit className="w-4 h-4" />
                        수정
                    </Button>

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
                </div>
            </header>

            {/* Split View */}
            <div className="flex-1 flex overflow-hidden">
                {/* Left: Document Viewer (50%) */}
                <div className="w-1/2 border-r border-gray-200 bg-white overflow-y-auto p-6">
                    <div className="max-w-3xl mx-auto">
                        <div className="prose prose-sm max-w-none">
                            {fileUrl ? (
                                <iframe
                                    src={fileUrl}
                                    className="w-full h-[800px] border border-gray-200 rounded-lg"
                                    title={document.title}
                                />
                            ) : (
                                <div className="flex items-center justify-center h-[800px] border border-gray-200 rounded-lg bg-gray-50">
                                    <p className="text-gray-500">문서를 불러오는 중...</p>
                                </div>
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
                                        {msg.role === 'user' ? (
                                            <p className="whitespace-pre-wrap">{msg.content}</p>
                                        ) : (
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

            {/* Edit Metadata Modal */}
            <Dialog open={editModalOpen} onOpenChange={setEditModalOpen}>
                <DialogContent className="sm:max-w-[500px]">
                    <DialogHeader>
                        <DialogTitle>문서 정보 수정</DialogTitle>
                        <DialogDescription>
                            문서의 제목, 설명, 공개범위, 태그를 수정합니다
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4 py-4">
                        {/* Title */}
                        <div>
                            <Label htmlFor="edit-title">제목</Label>
                            <Input
                                id="edit-title"
                                value={editTitle}
                                onChange={(e) => setEditTitle(e.target.value)}
                                placeholder="문서 제목"
                            />
                        </div>

                        {/* Description */}
                        <div>
                            <Label htmlFor="edit-description">설명</Label>
                            <Textarea
                                id="edit-description"
                                value={editDescription}
                                onChange={(e) => setEditDescription(e.target.value)}
                                placeholder="문서 설명 (선택)"
                                className="min-h-[80px]"
                            />
                        </div>

                        {/* Visibility */}
                        <div>
                            <Label htmlFor="edit-visibility">공개 범위</Label>
                            <Select value={editVisibility} onValueChange={(value: any) => setEditVisibility(value)}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>

                                    <SelectItem value="team">👥 팀 공유</SelectItem>
                                    <SelectItem value="public">🌐 전체 공개</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* Tags */}
                        <div>
                            <Label htmlFor="edit-tags">태그</Label>
                            <Input
                                id="edit-tags"
                                value={editTags}
                                onChange={(e) => setEditTags(e.target.value)}
                                placeholder="쉼표(,)로 구분하여 입력"
                            />
                            <p className="text-xs text-gray-500 mt-1">
                                예: 기획서, 마케팅, 2026
                            </p>
                        </div>
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setEditModalOpen(false)}>
                            취소
                        </Button>
                        <Button
                            onClick={handleSaveMetadata}
                            className="bg-blue-600 hover:bg-blue-700"
                        >
                            저장
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
        </div>
    );
}
