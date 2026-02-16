'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Menu, User, RotateCcw, Trash2, MessageSquare, FolderOpen, Bot, Settings, LogOut, Archive, FileText, File, FileSpreadsheet, Presentation } from 'lucide-react';

interface ArchivedDocument {
    id: string;
    name: string;
    type: string;
    deleted_at: string;
    days_remaining: number;
}

export default function ArchivePage() {
    const router = useRouter();
    const [archivedDocuments, setArchivedDocuments] = useState<ArchivedDocument[]>([]);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    const userName = typeof window !== 'undefined' ? localStorage.getItem('user_name') || '사용자' : '사용자';

    useEffect(() => {
        fetchArchivedDocuments();
    }, []);

    const fetchArchivedDocuments = async () => {
        setIsLoading(true);
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch('http://localhost:8000/drive/archive', {
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) throw new Error('Failed to fetch archived documents');

            const data = await response.json();
            setArchivedDocuments(data.documents || []);
        } catch (error) {
            console.error('Error fetching archived documents:', error);
            // Mock data for development
            setArchivedDocuments([
                {
                    id: '1',
                    name: '오래된 기획서.pdf',
                    type: 'pdf',
                    deleted_at: '2026-02-05T10:30:00',
                    days_remaining: 25,
                },
                {
                    id: '2',
                    name: '이전 회의록.docx',
                    type: 'docx',
                    deleted_at: '2026-01-20T14:20:00',
                    days_remaining: 9,
                },
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleRestore = async (id: string) => {
        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`http://localhost:8000/drive/restore/${id}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) throw new Error('Failed to restore document');

            // Refresh the list
            fetchArchivedDocuments();
        } catch (error) {
            console.error('Error restoring document:', error);
            alert('문서 복원에 실패했습니다.');
        }
    };

    const handlePermanentDelete = async (id: string) => {
        if (!confirm('정말로 영구 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) {
            return;
        }

        try {
            const token = localStorage.getItem('access_token');
            const response = await fetch(`http://localhost:8000/drive/permanent/${id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) throw new Error('Failed to delete document');

            // Refresh the list
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
                                onClick={() => { router.push('/drive'); setSidebarOpen(false); }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <FolderOpen className="w-5 h-5 text-blue-600" />
                                <span className="font-medium">AI Drive</span>
                            </button>
                            <button
                                onClick={() => { router.push('/drive/archive'); setSidebarOpen(false); }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-left bg-blue-50 rounded-lg transition-colors"
                            >
                                <Archive className="w-5 h-5 text-blue-600" />
                                <span className="font-medium text-blue-600">아카이브</span>
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

                    {/* Archive Table */}
                    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
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
