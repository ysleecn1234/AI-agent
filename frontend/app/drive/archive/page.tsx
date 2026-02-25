'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Menu, User, Search, FileText, File, FileSpreadsheet, Presentation, LogOut, Settings, MessageSquare, FolderOpen, Bot, ArrowLeft, RotateCcw, Trash2, Clock, Archive } from 'lucide-react';
import { AppSidebar } from '@/components/app-sidebar';
import Link from 'next/link';
import { api } from '@/lib/api';
import type { Document, ArchivedDocument } from '@/types/api';

const ARCHIVE_DAYS = 30;

function toArchivedDocument(doc: Document): ArchivedDocument {
    const deletedAt = doc.modified_at ? new Date(doc.modified_at).getTime() : Date.now();
    const daysSince = Math.floor((Date.now() - deletedAt) / 86400000);
    const days_remaining = Math.max(0, ARCHIVE_DAYS - daysSince);
    return {
        id: doc.doc_id,
        name: doc.title,
        type: doc.file_type || 'file',
        deleted_at: doc.modified_at || new Date().toISOString(),
        days_remaining,
    };
}

export default function ArchivePage() {
    const router = useRouter();
    const [archivedDocuments, setArchivedDocuments] = useState<ArchivedDocument[]>([]);
    const [chatSavedDocuments, setChatSavedDocuments] = useState<Document[]>([]);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [isLoadingChat, setIsLoadingChat] = useState(true);

    const userName = typeof window !== 'undefined' ? localStorage.getItem('user_name') || '사용자' : '사용자';

    useEffect(() => {
        fetchArchivedDocuments();
    }, []);

    useEffect(() => {
        fetchChatSavedDocuments();
    }, []);

    const fetchArchivedDocuments = async () => {
        setIsLoading(true);
        try {
            const docs = await api.getDocuments({ status: 'archived', limit: 100 });
            setArchivedDocuments(docs.map(toArchivedDocument));
        } catch (error) {
            console.error('Error fetching archived documents:', error);
            setArchivedDocuments([]);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchChatSavedDocuments = async () => {
        setIsLoadingChat(true);
        try {
            const docs = await api.getDocuments({ status: 'active', limit: 200 });
            setChatSavedDocuments(docs.filter((d) => (d.file_type || '').toLowerCase() === 'chat'));
        } catch (error) {
            console.error('Error fetching chat-saved documents:', error);
            setChatSavedDocuments([]);
        } finally {
            setIsLoadingChat(false);
        }
    };

    const handleRestore = async (id: string) => {
        try {
            await api.restoreDocument(id);
            fetchArchivedDocuments();
        } catch (error) {
            console.error('Error restoring document:', error);
            alert('문서 복원에 실패했습니다.');
        }
    };

    const handlePermanentDelete = async (id: string) => {
        if (!confirm('정말로 영구 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) return;
        try {
            await api.permanentDeleteDocument(id);
            fetchArchivedDocuments();
        } catch (error) {
            console.error('Error deleting document:', error);
            alert('문서 삭제에 실패했습니다.');
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_name');
        localStorage.removeItem('department');
        router.push('/auth/login');
    };

    const getFileIcon = (type: string) => {
        switch (type.toLowerCase()) {
            case 'pdf':
                return <FileText className="w-5 h-5 text-red-500" />;
            case 'docx':
                return <File className="w-5 h-5 text-blue-500" />;
            case 'xlsx':
                return <FileSpreadsheet className="w-5 h-5 text-green-500" />;
            case 'pptx':
                return <Presentation className="w-5 h-5 text-orange-500" />;
            default:
                return <FileText className="w-5 h-5 text-gray-500" />;
        }
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
        });
    };

    const getDaysRemainingColor = (days: number) => {
        if (days <= 7) return 'text-red-600 font-semibold';
        if (days <= 14) return 'text-orange-600';
        return 'text-gray-600';
    };

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
                    <SheetContent side="left" className="p-0 w-[280px]">
                        <AppSidebar
                            onNavigate={(path) => router.push(path)}
                            isMobile
                            onClose={() => setSidebarOpen(false)}
                            currentPath="/drive/archive"
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

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-7xl mx-auto space-y-6">
                    {/* Page Header */}
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">아카이브</h1>
                            <p className="text-gray-600 mt-1">삭제된 문서는 30일 후 자동으로 영구 삭제됩니다</p>
                        </div>
                    </div>

                    {/* 채팅 저장 목록 (과거 채팅셋) */}
                    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                        <div className="px-4 py-3 border-b border-gray-200">
                            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                                <MessageSquare className="w-5 h-5 text-blue-600" />
                                채팅 저장 목록
                            </h2>
                            <p className="text-sm text-gray-500 mt-0.5">채팅에서 Drive로 저장한 대화 목록입니다</p>
                        </div>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>제목</TableHead>
                                    <TableHead>부서</TableHead>
                                    <TableHead>수정일</TableHead>
                                    <TableHead className="text-right">이동</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {isLoadingChat ? (
                                    <TableRow>
                                        <TableCell colSpan={4} className="text-center py-6 text-gray-500">로딩 중...</TableCell>
                                    </TableRow>
                                ) : chatSavedDocuments.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={4} className="text-center py-6 text-gray-500">저장된 채팅이 없습니다</TableCell>
                                    </TableRow>
                                ) : (
                                    chatSavedDocuments.map((doc) => (
                                        <TableRow key={doc.doc_id}>
                                            <TableCell className="font-medium">{doc.title}</TableCell>
                                            <TableCell>{doc.creator_department}</TableCell>
                                            <TableCell>{doc.modified_at ? new Date(doc.modified_at).toLocaleDateString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit' }) : '-'}</TableCell>
                                            <TableCell className="text-right">
                                                <Link href={`/drive/documents/${doc.doc_id}`}>
                                                    <Button variant="outline" size="sm">보기</Button>
                                                </Link>
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    </div>

                    {/* Drive 아카이브 (삭제된 문서) */}
                    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                        <div className="px-4 py-3 border-b border-gray-200">
                            <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                                <Archive className="w-5 h-5 text-blue-600" />
                                삭제된 문서
                            </h2>
                        </div>
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead className="w-[50px]">유형</TableHead>
                                    <TableHead>파일명</TableHead>
                                    <TableHead>삭제일</TableHead>
                                    <TableHead>남은 기간</TableHead>
                                    <TableHead className="text-right">작업</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {isLoading ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                                            로딩 중...
                                        </TableCell>
                                    </TableRow>
                                ) : archivedDocuments.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                                            아카이브된 문서가 없습니다
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    archivedDocuments.map((doc) => (
                                        <TableRow key={doc.id}>
                                            <TableCell>{getFileIcon(doc.type)}</TableCell>
                                            <TableCell className="font-medium">{doc.name}</TableCell>
                                            <TableCell>{formatDate(doc.deleted_at)}</TableCell>
                                            <TableCell>
                                                <span className={getDaysRemainingColor(doc.days_remaining)}>
                                                    {doc.days_remaining}일
                                                </span>
                                            </TableCell>
                                            <TableCell className="text-right">
                                                <div className="flex justify-end gap-2">
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => handleRestore(doc.id)}
                                                    >
                                                        <RotateCcw className="w-4 h-4 mr-1" />
                                                        복원
                                                    </Button>
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={() => handlePermanentDelete(doc.id)}
                                                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                                    >
                                                        <Trash2 className="w-4 h-4 mr-1" />
                                                        영구삭제
                                                    </Button>
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </div>
            </div>
        </div>
    );
}
