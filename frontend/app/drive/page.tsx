'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Menu, User, Search, Upload, FileText, File, FileSpreadsheet, Presentation, LogOut, Settings, MessageSquare, FolderOpen, Bot, Archive, ChevronUp, ChevronDown, MoreVertical, Trash2, Download, RotateCcw, Clock } from 'lucide-react';
import { Checkbox } from '@/components/ui/checkbox';
import UploadModal from '@/components/upload-modal';
import { AppSidebar } from '@/components/app-sidebar';
import { api } from '@/lib/api';
import type { Document } from '@/types/api';

type SortColumn = 'file_type' | 'title' | 'creator_department' | 'modified_at' | 'visibility';
type SortDirection = 'asc' | 'desc';
type MainTab = 'drive' | 'archive';

const ARCHIVE_DAYS = 30;

export default function DrivePage() {
    const router = useRouter();
    const [mainTab, setMainTab] = useState<MainTab>('drive');
    const [documents, setDocuments] = useState<Document[]>([]);
    const [archivedDocuments, setArchivedDocuments] = useState<Document[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [filterTab, setFilterTab] = useState<'all' | 'public' | 'team'>('all');
    const [sortColumn, setSortColumn] = useState<SortColumn>('modified_at');
    const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
    const [uploadModalOpen, setUploadModalOpen] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [isLoadingArchive, setIsLoadingArchive] = useState(false);
    const [selectedDocs, setSelectedDocs] = useState<string[]>([]);

    const userName = typeof window !== 'undefined' ? localStorage.getItem('user_name') || '사용자' : '사용자';

    useEffect(() => {
        fetchDocuments();
    }, []);

    useEffect(() => {
        setSelectedDocs([]);
        if (mainTab === 'archive') fetchArchivedDocuments();
    }, [mainTab]);

    const fetchDocuments = async () => {
        setIsLoading(true);
        setSelectedDocs([]);
        try {
            const docs = await api.getDocuments();
            setDocuments(Array.isArray(docs) ? docs : []);
        } catch (error) {
            console.error('Error fetching documents:', error);
            setDocuments([]);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchArchivedDocuments = async () => {
        setIsLoadingArchive(true);
        setSelectedDocs([]);
        try {
            const docs = await api.getDocuments({ status: 'archived', limit: 100 });
            setArchivedDocuments(Array.isArray(docs) ? docs : []);
        } catch (error) {
            console.error('Error fetching archived documents:', error);
            setArchivedDocuments([]);
        } finally {
            setIsLoadingArchive(false);
        }
    };

    const getDaysRemaining = (modifiedAt: string) => {
        const deletedAt = new Date(modifiedAt).getTime();
        const daysSince = Math.floor((Date.now() - deletedAt) / 86400000);
        return Math.max(0, ARCHIVE_DAYS - daysSince);
    };

    const handleRestore = async (docId: string) => {
        try {
            await api.restoreDocument(docId);
            fetchArchivedDocuments();
        } catch (error) {
            alert('문서 복원에 실패했습니다.');
        }
    };

    const handlePermanentDelete = async (docId: string) => {
        if (!confirm('정말로 영구 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) return;
        try {
            await api.permanentDeleteDocument(docId);
            fetchArchivedDocuments();
        } catch (error) {
            alert('문서 삭제에 실패했습니다.');
        }
    };

    const handleSelectAll = (isDriveTab: boolean, checked: boolean) => {
        if (checked) {
            const docsToSelect = isDriveTab ? filteredDocuments : filteredArchived;
            setSelectedDocs(docsToSelect.map(d => d.doc_id));
        } else {
            setSelectedDocs([]);
        }
    };

    const handleSelectOne = (docId: string, checked: boolean) => {
        if (checked) {
            setSelectedDocs(prev => [...prev, docId]);
        } else {
            setSelectedDocs(prev => prev.filter(id => id !== docId));
        }
    };

    const handleBulkDelete = async () => {
        if (!confirm(`선택한 ${selectedDocs.length}개의 문서를 아카이브로 이동하시겠습니까?`)) return;
        try {
            const token = localStorage.getItem('access_token');
            await Promise.all(
                selectedDocs.map(docId =>
                    fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://223.130.142.76:8000'}/drive/documents/${docId}`, {
                        method: 'DELETE',
                        headers: { 'Authorization': `Bearer ${token}` },
                    })
                )
            );
            fetchDocuments();
        } catch (error) {
            console.error('Error deleting documents:', error);
            alert('일괄 삭제에 실패했습니다.');
        }
    };

    const handleBulkRestore = async () => {
        try {
            await Promise.all(selectedDocs.map(docId => api.restoreDocument(docId)));
            fetchArchivedDocuments();
        } catch (error) {
            console.error('Error restoring documents:', error);
            alert('일괄 복원에 실패했습니다.');
        }
    };

    const handleBulkPermanentDelete = async () => {
        if (!confirm(`선택한 ${selectedDocs.length}개의 문서를 정말로 영구 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`)) return;
        try {
            await Promise.all(selectedDocs.map(docId => api.permanentDeleteDocument(docId)));
            fetchArchivedDocuments();
        } catch (error) {
            console.error('Error permanently deleting documents:', error);
            alert('일괄 영구 삭제에 실패했습니다.');
        }
    };

    const handleSort = (column: SortColumn) => {
        if (sortColumn === column) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
        } else {
            setSortColumn(column);
            setSortDirection('asc');
        }
    };

    const handleDownload = async (documentId: string, documentName: string, e: React.MouseEvent) => {
        e.stopPropagation();

        try {
            // API 호출: 문서 다운로드
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://223.130.142.76:8000'}/drive/documents/${documentId}/file?download=true`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (!response.ok) {
                throw new Error('다운로드 실패');
            }

            // Blob으로 변환하여 다운로드
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = documentName;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Download failed:', error);
            alert('다운로드에 실패했습니다.');
        }
    };

    const handleDelete = async (documentId: string, e: React.MouseEvent) => {
        e.stopPropagation();

        if (!confirm('이 문서를 아카이브로 이동하시겠습니까?')) {
            return;
        }

        try {
            // API 호출: 문서 삭제 (아카이브 이동)
            // 현재 api.ts에 deleteDocument가 없으므로 fetch를 직접 호출하거나 api.ts에 추가해야 함.
            // 여기서는 api.ts에 추가했다고 가정하고 호출하거나, 일단 fetch 유지.
            // *Task 확인*: api.ts에는 getDocuments, getDocument, uploadDocument, saveChatToDrive 만 있음.
            // delete 기능을 api.ts에 추가하는 것이 낫지만, 일단 fetch로 유지하되 토큰 로직은 api.ts와 동일하게.

            // 하지만 일관성을 위해 api.request를 쓰고 싶으나 private임. 
            // 따라서 api.ts에 deleteDocument를 추가하는 것이 정석이나, 
            // 현재 api.ts 파일 수정을 최소화하려면 일단 fetch 유지하되 토큰 가져오는 방식만 통일.

            const token = localStorage.getItem('access_token');
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://223.130.142.76:8000'}/drive/documents/${documentId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!response.ok) throw new Error('Failed to delete document');

            // Refresh the document list
            fetchDocuments();
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

    const getFileIcon = (fileType: string) => {
        const t = (fileType || '').toLowerCase();
        switch (t) {
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

    const getVisibilityBadge = (visibility: string) => {
        switch (visibility) {
            case 'private':
                return <Badge variant="outline">🔒 나만</Badge>;
            case 'team':
                return <Badge variant="outline">👥 팀</Badge>;
            case 'public':
                return <Badge variant="outline">🌐 전체</Badge>;
            default:
                return <Badge variant="outline">{visibility}</Badge>;
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

    const filteredDocuments = documents
        .filter((doc) => {
            if (searchQuery) {
                // Mac OS는 파일명 한글을 NFD(분리형)로 저장하므로, NFC(조합형)로 정규화 후 비교
                const normalizedTitle = (doc.title || '').normalize('NFC').toLowerCase();
                const normalizedQuery = searchQuery.normalize('NFC').toLowerCase();
                if (!normalizedTitle.includes(normalizedQuery)) return false;
            }
            if (filterTab === 'public' && doc.visibility !== 'public') return false;
            if (filterTab === 'team' && doc.visibility !== 'team') return false;
            return true;
        })
        .sort((a, b) => {
            const aValue = a[sortColumn];
            const bValue = b[sortColumn];
            const direction = sortDirection === 'asc' ? 1 : -1;
            if (typeof aValue === 'string' && typeof bValue === 'string') {
                return aValue.localeCompare(bValue) * direction;
            }
            return 0;
        });

    const filteredArchived = archivedDocuments.filter((doc) => {
        if (!searchQuery) return true;
        const normalizedTitle = (doc.title || '').normalize('NFC').toLowerCase();
        const normalizedQuery = searchQuery.normalize('NFC').toLowerCase();
        return normalizedTitle.includes(normalizedQuery);
    });

    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
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
                                currentPath="/drive"
                            />
                        </SheetContent>
                    </Sheet>

                    {/* Logo Home Button */}
                    <div 
                        className="flex items-center gap-2 cursor-pointer hover:opacity-80 transition-opacity ml-1" 
                        onClick={() => router.push('/chat')}
                    >
                        <div className="w-7 h-7 bg-blue-600 rounded-full flex items-center justify-center">
                            <span className="text-white text-[10px] font-bold">ISOR</span>
                        </div>
                        <span className="font-semibold text-sm text-gray-800">ISOR</span>
                    </div>
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

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-7xl mx-auto space-y-6">
                    {/* Page Header */}
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <h1 className="text-3xl font-bold text-gray-900">AI Drive</h1>
                            <Tabs value={mainTab} onValueChange={(v: any) => setMainTab(v)}>
                                <TabsList>
                                    <TabsTrigger value="drive">
                                        <FolderOpen className="w-4 h-4 mr-1" />
                                        내 문서
                                    </TabsTrigger>
                                    <TabsTrigger value="archive">
                                        <Archive className="w-4 h-4 mr-1" />
                                        휴지통
                                    </TabsTrigger>
                                </TabsList>
                            </Tabs>
                        </div>
                        {mainTab === 'drive' && (
                            <Button onClick={() => setUploadModalOpen(true)} className="bg-blue-600 hover:bg-blue-700">
                                <Upload className="w-4 h-4 mr-2" />
                                업로드
                            </Button>
                        )}
                    </div>

                    {/* Search */}
                    <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-4">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                            <Input
                                type="text"
                                placeholder="문서 검색..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-10"
                            />
                        </div>

                        {mainTab === 'drive' && (
                            <Tabs value={filterTab} onValueChange={(value: any) => setFilterTab(value)}>
                                <TabsList>
                                    <TabsTrigger value="all">전체</TabsTrigger>
                                    <TabsTrigger value="public">🌐 전체 공개</TabsTrigger>
                                    <TabsTrigger value="team">👥 팀 공유</TabsTrigger>
                                </TabsList>
                            </Tabs>
                        )}
                    </div>

                    {/* Drive Tab: Documents Table */}
                    {mainTab === 'drive' && (
                        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                            {selectedDocs.length > 0 && (
                                <div className="bg-blue-50 px-4 py-3 border-b border-gray-200 flex items-center justify-between">
                                    <span className="text-sm font-medium text-blue-700">{selectedDocs.length}개 선택됨</span>
                                    <Button size="sm" variant="destructive" onClick={handleBulkDelete}>
                                        <Trash2 className="w-4 h-4 mr-2" />
                                        선택 삭제
                                    </Button>
                                </div>
                            )}
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="w-[50px] text-center">
                                            <Checkbox
                                                checked={selectedDocs.length > 0 && filteredDocuments.length > 0 && selectedDocs.length === filteredDocuments.length}
                                                onCheckedChange={(checked) => handleSelectAll(true, checked as boolean)}
                                            />
                                        </TableHead>
                                        <TableHead className="w-[50px]">
                                            <button onClick={() => handleSort('file_type')} className="flex items-center gap-1 hover:text-blue-600">
                                                유형
                                                {sortColumn === 'file_type' && (sortDirection === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />)}
                                            </button>
                                        </TableHead>
                                        <TableHead>
                                            <button onClick={() => handleSort('title')} className="flex items-center gap-1 hover:text-blue-600">
                                                파일명
                                                {sortColumn === 'title' && (sortDirection === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />)}
                                            </button>
                                        </TableHead>
                                        <TableHead>
                                            <button onClick={() => handleSort('creator_department')} className="flex items-center gap-1 hover:text-blue-600">
                                                제작자
                                                {sortColumn === 'creator_department' && (sortDirection === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />)}
                                            </button>
                                        </TableHead>
                                        <TableHead>
                                            <button onClick={() => handleSort('modified_at')} className="flex items-center gap-1 hover:text-blue-600">
                                                날짜
                                                {sortColumn === 'modified_at' && (sortDirection === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />)}
                                            </button>
                                        </TableHead>
                                        <TableHead>
                                            <button onClick={() => handleSort('visibility')} className="flex items-center gap-1 hover:text-blue-600">
                                                공개범위
                                                {sortColumn === 'visibility' && (sortDirection === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />)}
                                            </button>
                                        </TableHead>
                                        <TableHead className="w-[50px]"></TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {isLoading ? (
                                        <TableRow><TableCell colSpan={7} className="text-center py-8 text-gray-500">로딩 중...</TableCell></TableRow>
                                    ) : filteredDocuments.length === 0 ? (
                                        <TableRow><TableCell colSpan={7} className="text-center py-8 text-gray-500">문서가 없습니다</TableCell></TableRow>
                                    ) : (
                                        filteredDocuments.map((doc) => (
                                            <TableRow key={doc.doc_id} className="hover:bg-gray-50">
                                                <TableCell className="text-center" onClick={(e) => e.stopPropagation()}>
                                                    <Checkbox
                                                        checked={selectedDocs.includes(doc.doc_id)}
                                                        onCheckedChange={(checked) => handleSelectOne(doc.doc_id, checked as boolean)}
                                                    />
                                                </TableCell>
                                                <TableCell onClick={() => router.push(`/drive/documents/${doc.doc_id}`)} className="cursor-pointer">{getFileIcon(doc.file_type)}</TableCell>
                                                <TableCell onClick={() => router.push(`/drive/documents/${doc.doc_id}`)} className="font-medium cursor-pointer">{doc.title}</TableCell>
                                                <TableCell onClick={() => router.push(`/drive/documents/${doc.doc_id}`)} className="cursor-pointer">{doc.creator_department}</TableCell>
                                                <TableCell onClick={() => router.push(`/drive/documents/${doc.doc_id}`)} className="cursor-pointer">{formatDate(doc.modified_at)}</TableCell>
                                                <TableCell onClick={() => router.push(`/drive/documents/${doc.doc_id}`)} className="cursor-pointer">{getVisibilityBadge(doc.visibility)}</TableCell>
                                                <TableCell>
                                                    <DropdownMenu>
                                                        <DropdownMenuTrigger asChild>
                                                            <button className="p-2 hover:bg-gray-200 rounded-lg transition-colors">
                                                                <MoreVertical className="w-4 h-4 text-gray-600" />
                                                            </button>
                                                        </DropdownMenuTrigger>
                                                        <DropdownMenuContent align="end">
                                                            <DropdownMenuItem onClick={(e) => handleDownload(doc.doc_id, doc.title, e)}>
                                                                <Download className="w-4 h-4 mr-2" />
                                                                다운로드
                                                            </DropdownMenuItem>
                                                            <DropdownMenuSeparator />
                                                            <DropdownMenuItem onClick={(e) => handleDelete(doc.doc_id, e)} className="text-red-600 focus:text-red-600">
                                                                <Trash2 className="w-4 h-4 mr-2" />
                                                                삭제
                                                            </DropdownMenuItem>
                                                        </DropdownMenuContent>
                                                    </DropdownMenu>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    )}

                    {/* Archive Tab */}
                    {mainTab === 'archive' && (
                        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                            <div className="px-4 py-3 border-b border-gray-100 bg-amber-50">
                                <p className="text-sm text-amber-700">
                                    삭제된 문서는 <strong>{ARCHIVE_DAYS}일</strong> 후 자동으로 영구 삭제됩니다.
                                </p>
                            </div>
                            {selectedDocs.length > 0 && (
                                <div className="bg-blue-50 px-4 py-3 border-b border-gray-200 flex items-center justify-between">
                                    <span className="text-sm font-medium text-blue-700">{selectedDocs.length}개 선택됨</span>
                                    <div className="flex items-center gap-2">
                                        <Button size="sm" variant="outline" onClick={handleBulkRestore}>
                                            <RotateCcw className="w-4 h-4 mr-2" />
                                            선택 복원
                                        </Button>
                                        <Button size="sm" variant="destructive" onClick={handleBulkPermanentDelete}>
                                            <Trash2 className="w-4 h-4 mr-2" />
                                            선택 영구 삭제
                                        </Button>
                                    </div>
                                </div>
                            )}
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="w-[50px] text-center">
                                            <Checkbox
                                                checked={selectedDocs.length > 0 && filteredArchived.length > 0 && selectedDocs.length === filteredArchived.length}
                                                onCheckedChange={(checked) => handleSelectAll(false, checked as boolean)}
                                            />
                                        </TableHead>
                                        <TableHead className="w-[50px]">유형</TableHead>
                                        <TableHead>파일명</TableHead>
                                        <TableHead>삭제일</TableHead>
                                        <TableHead>남은 기간</TableHead>
                                        <TableHead className="w-[120px]">작업</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {isLoadingArchive ? (
                                        <TableRow><TableCell colSpan={6} className="text-center py-8 text-gray-500">로딩 중...</TableCell></TableRow>
                                    ) : filteredArchived.length === 0 ? (
                                        <TableRow><TableCell colSpan={6} className="text-center py-8 text-gray-500">휴지통이 비어 있습니다</TableCell></TableRow>
                                    ) : (
                                        filteredArchived.map((doc) => {
                                            const daysLeft = getDaysRemaining(doc.modified_at);
                                            return (
                                                <TableRow key={doc.doc_id} className="hover:bg-gray-50">
                                                    <TableCell className="text-center">
                                                        <Checkbox
                                                            checked={selectedDocs.includes(doc.doc_id)}
                                                            onCheckedChange={(checked) => handleSelectOne(doc.doc_id, checked as boolean)}
                                                        />
                                                    </TableCell>
                                                    <TableCell>{getFileIcon(doc.file_type)}</TableCell>
                                                    <TableCell className="font-medium">{doc.title}</TableCell>
                                                    <TableCell className="text-gray-500">{formatDate(doc.modified_at)}</TableCell>
                                                    <TableCell>
                                                        <span className={`text-sm font-medium ${daysLeft <= 3 ? 'text-red-600' : 'text-gray-600'}`}>
                                                            {daysLeft}일 후 삭제
                                                        </span>
                                                    </TableCell>
                                                    <TableCell>
                                                        <div className="flex items-center gap-2">
                                                            <button
                                                                onClick={() => handleRestore(doc.doc_id)}
                                                                className="p-1.5 hover:bg-blue-100 rounded text-blue-600 transition-colors"
                                                                title="복원"
                                                            >
                                                                <RotateCcw className="w-4 h-4" />
                                                            </button>
                                                            <button
                                                                onClick={() => handlePermanentDelete(doc.doc_id)}
                                                                className="p-1.5 hover:bg-red-100 rounded text-red-600 transition-colors"
                                                                title="영구 삭제"
                                                            >
                                                                <Trash2 className="w-4 h-4" />
                                                            </button>
                                                        </div>
                                                    </TableCell>
                                                </TableRow>
                                            );
                                        })
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    )}
                </div>
            </div>

            {/* Upload Modal */}
            <UploadModal
                isOpen={uploadModalOpen}
                onClose={() => setUploadModalOpen(false)}
                onUploadSuccess={fetchDocuments}
            />
        </div>
    );
}
