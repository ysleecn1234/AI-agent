'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Menu, User, Send, MessageSquare, FolderOpen, Bot, Settings, LogOut, Save, Sparkles } from 'lucide-react';
import { SaveToDriveModal, CreateAgentModal } from '@/components/chat-action-modals';
import { api } from '@/lib/api';

export default function ChatPage() {
    const router = useRouter();
    const [message, setMessage] = useState('');
    const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([]);
    const [selectedModel, setSelectedModel] = useState('AUTO');
    const [agentId, setAgentId] = useState<string | undefined>(undefined);
    const [driveEnabled, setDriveEnabled] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [saveModalOpen, setSaveModalOpen] = useState(false);
    const [agentModalOpen, setAgentModalOpen] = useState(false);
    const [selectedMessageIndex, setSelectedMessageIndex] = useState<number | null>(null);

    const handleSend = async () => {
        if (!message.trim() || isLoading) return;

        const userMessage = message;
        setMessage('');
        setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
        setIsLoading(true);

        try {
            // API 호출
            const response = await api.sendMessage({
                message: userMessage,
                model_type: selectedModel === 'auto' ? 'AUTO' : selectedModel.toUpperCase(),
                use_rag: driveEnabled,
                agent_id: agentId,
            });

            setMessages(prev => [...prev, { role: 'assistant', content: response.response }]);
        } catch (error) {
            console.error('Error sending message:', error);
            const errorMessage = error instanceof Error ? error.message : '메시지 전송에 실패했습니다.';
            setMessages(prev => [...prev, { role: 'assistant', content: `❌ 오류가 발생했습니다: ${errorMessage}` }]);
        } finally {
            setIsLoading(false);
        }
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

    const handleSaveConfirm = async (scope: 'single' | 'all') => {
        try {
            const content = scope === 'single' && selectedMessageIndex !== null
                ? messages[selectedMessageIndex].content
                : messages.map(m => `${m.role}: ${m.content}`).join('\n\n');

            // API 연동: 드라이브 저장
            const creatorId = typeof window !== 'undefined' ? localStorage.getItem('user_name') || 'anonymous' : 'anonymous';
            const creatorDept = typeof window !== 'undefined' ? localStorage.getItem('department') || 'general' : 'general';

            await api.saveChatToDrive({
                content,
                creator_id: creatorId,
                creator_department: creatorDept,
                title: `${new Date().toLocaleString()} 채팅 저장`,
                visibility: 'private'
            });

            alert('드라이브에 저장되었습니다!');
            setSaveModalOpen(false);
        } catch (error) {
            console.error('Save failed:', error);
            alert('저장에 실패했습니다.');
        }
    };

    const handleAgentConfirm = async (scope: 'single' | 'all') => {
        try {
            const content = scope === 'single' && selectedMessageIndex !== null
                ? messages[selectedMessageIndex].content
                : messages.map(m => `${m.role}: ${m.content}`).join('\n\n');

            // API 연동: 에이전트 초안 생성
            const draft = await api.createAgentDraft({
                name: 'New Agent',
                description: 'Generated from chat',
                category: 'general',
                visibility: 'private',
                system_prompt: `Based on this content:\n\n${content}`
            });

            alert('에이전트 초안이 생성되었습니다!');
            setAgentModalOpen(false);
            router.push(`/agents/create?draftId=${draft.id}`); // 생성된 초안 ID와 함께 이동
        } catch (error) {
            console.error('Agent creation failed:', error);
            alert('에이전트 생성에 실패했습니다.');
        }
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
                                <span className="text-white text-3xl font-bold">IN7</span>
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
                                    <p className="whitespace-pre-wrap">{msg.content}</p>
                                </div>

                                {/* Action Buttons (AI messages only) */}
                                {msg.role === 'assistant' && (
                                    <div className="flex gap-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleSaveToDrive(idx)}
                                            className="text-xs"
                                        >
                                            <Save className="w-3 h-3 mr-1" />
                                            드라이브에 저장
                                        </Button>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleCreateAgent(idx)}
                                            className="text-xs"
                                        >
                                            <Sparkles className="w-3 h-3 mr-1" />
                                            에이전트 생성
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
                <div className="flex items-center gap-4 text-sm">
                    {/* Model Selector */}
                    <Select value={selectedModel} onValueChange={setSelectedModel}>
                        <SelectTrigger className="w-[180px]">
                            <SelectValue placeholder="모델 선택" />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="auto">Auto (자동 선택)</SelectItem>
                            <SelectItem value="gpt-5">GPT-5</SelectItem>
                            <SelectItem value="gpt-5-mini">GPT-5-mini</SelectItem>
                            <SelectItem value="claude-sonnet">Claude Sonnet 4.5</SelectItem>
                            <SelectItem value="gemini-pro">Gemini 2.0 Pro</SelectItem>
                            <SelectItem value="gemini-flash">Gemini 2.0 Flash</SelectItem>
                            <SelectItem value="deepseek">DeepSeek-R1</SelectItem>
                        </SelectContent>
                    </Select>

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
                        <label className="text-gray-700 cursor-pointer" onClick={() => setDriveEnabled(!driveEnabled)}>
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
            />
            <CreateAgentModal
                isOpen={agentModalOpen}
                onClose={() => setAgentModalOpen(false)}
                onCreate={handleAgentConfirm}
            />
        </div>
    );
}
