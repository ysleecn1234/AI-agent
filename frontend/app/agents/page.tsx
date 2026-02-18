'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import {
    Search,
    Plus,
    MoreVertical,
    Play,
    Edit,
    Trash2,
    Users,
    User,
    Globe,
    Filter,
    Menu,
    MessageSquare,
    FolderOpen,
    Archive,
    Bot,
    Settings,
    LogOut
} from 'lucide-react';
import { api } from '@/lib/api';
import type { Agent } from '@/types/api';

export default function AgentsPage() {
    const router = useRouter();
    const [agents, setAgents] = useState<Agent[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState('all');
    const [categoryFilter, setCategoryFilter] = useState('all');
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);

    const userName = typeof window !== 'undefined' ? localStorage.getItem('user_name') || '사용자' : '사용자';
    const userDept = typeof window !== 'undefined' ? localStorage.getItem('department') || '' : '';

    useEffect(() => {
        fetchAgents();
    }, []);

    const fetchAgents = async () => {
        setIsLoading(true);
        try {
            const data = await api.getAgents();
            setAgents(data);
        } catch (error) {
            console.error('Error fetching agents:', error);
            // Mock data fallback for development
            setAgents([]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteAgent = async (agentId: string, e: React.MouseEvent) => {
        e.stopPropagation();

        if (!confirm('이 에이전트를 삭제하시겠습니까?')) {
            return;
        }

        try {
            await api.deleteAgent(agentId);
            alert('에이전트가 삭제되었습니다.');
            fetchAgents();
        } catch (error) {
            console.error('Error deleting agent:', error);
            alert('에이전트 삭제에 실패했습니다.');
        }
    };

    // Filter agents based on tab, search query, and category
    const filteredAgents = agents.filter(agent => {
        const matchesSearch = agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            agent.description.toLowerCase().includes(searchQuery.toLowerCase());

        if (!matchesSearch) return false;

        // Tab filter
        if (activeTab === 'my') return agent.creator === userName;
        if (activeTab === 'team') return (agent.visibility || '').toLowerCase() === 'team';
        if (activeTab === 'public') return (agent.visibility || '').toLowerCase() === 'public';

        // Category filter
        if (categoryFilter !== 'all' && agent.category !== categoryFilter) return false;

        return true;
    });

    const handleRunAgent = (agentId: string) => {
        router.push(`/chat?agent=${agentId}`);
    };

    const handleCreateAgent = () => {
        router.push('/agents/create');
    };

    const handleLogout = () => {
        api.clearToken();
        router.push('/auth/login');
    };

    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    {/* Sidebar Trigger */}
                    <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
                        <SheetTrigger asChild>
                            <Button variant="ghost" size="icon">
                                <Menu className="w-6 h-6 text-gray-700" />
                            </Button>
                        </SheetTrigger>
                        <SheetContent side="left" className="w-[300px]">
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
                                    className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-100 rounded-lg transition-colors"
                                >
                                    <Archive className="w-5 h-5 text-blue-600" />
                                    <span className="font-medium">아카이브</span>
                                </button>
                                <button
                                    onClick={() => { router.push('/agents'); setSidebarOpen(false); }}
                                    className="w-full flex items-center gap-3 px-4 py-3 text-left bg-blue-50 rounded-lg transition-colors"
                                >
                                    <Bot className="w-5 h-5 text-blue-600" />
                                    <span className="font-medium text-blue-600">Agent Hub</span>
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

                    <h1 className="text-2xl font-bold text-gray-900">Agent Hub</h1>
                </div>

                <div className="flex items-center gap-3">
                    <Button onClick={handleCreateAgent} className="bg-blue-600 hover:bg-blue-700 text-white gap-2">
                        <Plus className="w-4 h-4" />
                        새 에이전트 만들기
                    </Button>

                    {/* User Menu */}
                    <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                                <User className="w-6 h-6 text-gray-700" />
                            </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end" className="w-56">
                            <DropdownMenuLabel>
                                <div className="flex flex-col">
                                    <span className="font-medium">{userName}</span>
                                    <span className="text-sm text-gray-500">{userDept}</span>
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

            {/* Main Content */}
            <main className="flex-1 overflow-auto p-6">
                <div className="max-w-7xl mx-auto space-y-6">

                    {/* Search and Filters */}
                    <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
                        <div className="relative w-full sm:w-96">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                            <Input
                                placeholder="에이전트 검색 (이름, 설명)"
                                className="pl-10"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                        </div>

                        <div className="flex gap-2 w-full sm:w-auto">
                            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                                <SelectTrigger className="w-[160px]">
                                    <SelectValue placeholder="카테고리" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">전체 카테고리</SelectItem>
                                    <SelectItem value="생산성">생산성</SelectItem>
                                    <SelectItem value="마케팅">마케팅</SelectItem>
                                    <SelectItem value="개발">개발</SelectItem>
                                    <SelectItem value="기획">기획</SelectItem>
                                    <SelectItem value="영업">영업</SelectItem>
                                    <SelectItem value="인사">인사</SelectItem>
                                    <SelectItem value="재무">재무</SelectItem>
                                    <SelectItem value="기타">기타</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    {/* Tabs */}
                    <Tabs defaultValue="all" value={activeTab} onValueChange={setActiveTab} className="w-full">
                        <TabsList className="mb-6">
                            <TabsTrigger value="all" className="flex items-center gap-2">
                                <Globe className="w-4 h-4" /> 전체
                            </TabsTrigger>
                            <TabsTrigger value="my" className="flex items-center gap-2">
                                <User className="w-4 h-4" /> 내 에이전트
                            </TabsTrigger>
                            <TabsTrigger value="team" className="flex items-center gap-2">
                                <Users className="w-4 h-4" /> 팀 에이전트
                            </TabsTrigger>
                        </TabsList>

                        <TabsContent value={activeTab} className="mt-0">
                            {isLoading ? (
                                <div className="text-center py-20">
                                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                                    <p className="text-gray-600">에이전트를 불러오는 중...</p>
                                </div>
                            ) : filteredAgents.length === 0 ? (
                                <div className="text-center py-20 bg-white rounded-lg border border-gray-200 border-dashed">
                                    <Bot className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                                    <h3 className="text-lg font-medium text-gray-900">검색 결과가 없습니다</h3>
                                    <p className="text-gray-500 mt-2">다른 검색어로 시도해보거나 새로운 에이전트를 만들어보세요.</p>
                                    <Button onClick={handleCreateAgent} variant="outline" className="mt-4">
                                        새 에이전트 만들기
                                    </Button>
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                                    {filteredAgents.map((agent) => (
                                        <Card key={agent.id} className="flex flex-col hover:shadow-md transition-shadow">
                                            <CardHeader className="pb-3">
                                                <div className="flex justify-between items-start">
                                                    <div className="flex items-center gap-2">
                                                        <Badge variant="outline" className="text-xs">
                                                            {agent.category}
                                                        </Badge>
                                                    </div>
                                                    <DropdownMenu>
                                                        <DropdownMenuTrigger asChild>
                                                            <Button variant="ghost" size="icon" className="-mr-2 -mt-2">
                                                                <MoreVertical className="w-4 h-4 text-gray-500" />
                                                            </Button>
                                                        </DropdownMenuTrigger>
                                                        <DropdownMenuContent align="end">
                                                            <DropdownMenuItem onClick={() => handleRunAgent(agent.id)}>
                                                                <Play className="w-4 h-4 mr-2" /> 실행
                                                            </DropdownMenuItem>
                                                            <DropdownMenuItem onClick={() => router.push(`/agents/edit/${agent.id}`)}>
                                                                <Edit className="w-4 h-4 mr-2" /> 수정
                                                            </DropdownMenuItem>
                                                            <DropdownMenuItem 
                                                                onClick={(e) => handleDeleteAgent(agent.id, e)}
                                                                className="text-red-600 focus:text-red-600"
                                                            >
                                                                <Trash2 className="w-4 h-4 mr-2" /> 삭제
                                                            </DropdownMenuItem>
                                                        </DropdownMenuContent>
                                                    </DropdownMenu>
                                                </div>
                                                <CardTitle className="mt-3 text-lg">{agent.name}</CardTitle>
                                                <CardDescription className="line-clamp-2 min-h-[40px]">
                                                    {agent.description}
                                                </CardDescription>
                                            </CardHeader>
                                            <CardContent className="flex-1">
                                                <div className="flex items-center gap-2 text-xs text-gray-500">
                                                    <span className="font-medium text-gray-700">{agent.creator}</span>
                                                    <span>•</span>
                                                    <Badge variant="secondary" className="text-xs">
                                                        {(agent.visibility || '').toLowerCase() === 'public' ? '🌐 전체' : (agent.visibility || '').toLowerCase() === 'team' ? '👥 팀' : '🔒 나만'}
                                                    </Badge>
                                                </div>
                                            </CardContent>
                                            <CardFooter className="pt-3 border-t bg-gray-50/50">
                                                <Button 
                                                    size="sm" 
                                                    variant="default"
                                                    className="w-full bg-blue-600 hover:bg-blue-700" 
                                                    onClick={() => handleRunAgent(agent.id)}
                                                >
                                                    <Play className="w-3 h-3 mr-1" />
                                                    실행하기
                                                </Button>
                                            </CardFooter>
                                        </Card>
                                    ))}
                                </div>
                            )}
                        </TabsContent>
                    </Tabs>
                </div>
            </main>
        </div>
    );
}
