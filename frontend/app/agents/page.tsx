'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
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
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Agent, MOCK_AGENTS } from '@/types/agent';

export default function AgentsPage() {
    const router = useRouter();
    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState('all');
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const userId = 'user_id_placeholder'; // TODO: Replace with actual user ID

    // Filter agents based on tab and search query
    const filteredAgents = MOCK_AGENTS.filter(agent => {
        const matchesSearch = agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            agent.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
            agent.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));

        if (!matchesSearch) return false;

        if (activeTab === 'my') return agent.creator === '김철수'; // Mock condition
        if (activeTab === 'team') return agent.department === '마케팅팀'; // Mock condition
        if (activeTab === 'public') return agent.isPublic;

        return true;
    });

    const handleRunAgent = (agentId: string) => {
        // Navigate to chat with this agent selected
        router.push(`/chat?agent=${agentId}`);
    };

    const handleCreateAgent = () => {
        router.push('/agents/create');
    };

    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    {/* Sidebar Trigger (Visible on all screens) */}
                    <div>
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
                                            <span className="text-white text-lg font-bold">IN7</span>
                                        </div>
                                        <span>AI 플랫폼</span>
                                    </SheetTitle>
                                </SheetHeader>
                                <nav className="mt-8 space-y-2">
                                    <button onClick={() => router.push('/chat')} className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-100 rounded-lg">
                                        <MessageSquare className="w-5 h-5 text-blue-600" /> <span>채팅</span>
                                    </button>
                                    <button onClick={() => router.push('/drive')} className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-100 rounded-lg">
                                        <FolderOpen className="w-5 h-5 text-blue-600" /> <span>AI Drive</span>
                                    </button>
                                    <button onClick={() => router.push('/drive/archive')} className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-100 rounded-lg">
                                        <Archive className="w-5 h-5 text-blue-600" /> <span>아카이브</span>
                                    </button>
                                    <button className="w-full flex items-center gap-3 px-4 py-3 text-left bg-blue-50 rounded-lg text-blue-600">
                                        <Bot className="w-5 h-5" /> <span className="font-medium">Agent Hub</span>
                                    </button>
                                    <button onClick={() => router.push('/settings')} className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-100 rounded-lg">
                                        <Settings className="w-5 h-5 text-blue-600" /> <span>설정</span>
                                    </button>
                                </nav>
                            </SheetContent>
                        </Sheet>
                    </div>

                    <h1 className="text-2xl font-bold text-gray-900">Agent Hub</h1>
                </div>

                <Button onClick={handleCreateAgent} className="bg-blue-600 hover:bg-blue-700 text-white gap-2">
                    <Plus className="w-4 h-4" />
                    새 에이전트 만들기
                </Button>
            </header>

            {/* Main Content */}
            <main className="flex-1 overflow-auto p-6">
                <div className="max-w-7xl mx-auto space-y-6">

                    {/* Search and Filters */}
                    <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
                        <div className="relative w-full sm:w-96">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                            <Input
                                placeholder="에이전트 검색 (이름, 태그, 설명)"
                                className="pl-10"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                        </div>

                        <div className="flex gap-2 w-full sm:w-auto">
                            <Select defaultValue="newest">
                                <SelectTrigger className="w-[140px]">
                                    <SelectValue placeholder="정렬" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="newest">최신순</SelectItem>
                                    <SelectItem value="popular">인기순</SelectItem>
                                    <SelectItem value="name">이름순</SelectItem>
                                </SelectContent>
                            </Select>
                            <Button variant="outline" size="icon">
                                <Filter className="w-4 h-4 text-gray-600" />
                            </Button>
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
                            {filteredAgents.length === 0 ? (
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
                                                    <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center text-2xl">
                                                        {agent.icon}
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
                                                            <DropdownMenuItem className="text-red-600">
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
                                                <div className="flex flex-wrap gap-2 mb-3">
                                                    {agent.tags.slice(0, 3).map(tag => (
                                                        <Badge key={tag} variant="secondary" className="text-xs">
                                                            #{tag}
                                                        </Badge>
                                                    ))}
                                                    {agent.tags.length > 3 && (
                                                        <Badge variant="secondary" className="text-xs">+{agent.tags.length - 3}</Badge>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-2 text-xs text-gray-500 mt-auto">
                                                    <span className="font-medium text-gray-700">{agent.creator}</span>
                                                    <span>•</span>
                                                    <span>{agent.model}</span>
                                                </div>
                                            </CardContent>
                                            <CardFooter className="pt-3 border-t bg-gray-50/50 flex justify-between items-center text-xs text-gray-500">
                                                <div className="flex items-center gap-1">
                                                    <Play className="w-3 h-3" /> {agent.usageCount}회 실행됨
                                                </div>
                                                <Button size="sm" variant="ghost" className="text-blue-600 hover:text-blue-700 p-0 h-auto" onClick={() => handleRunAgent(agent.id)}>
                                                    실행하기 →
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
