import re

filepath = '/Users/isshosaint/AI-agent/frontend/app/chat/page.tsx'
with open(filepath, 'r', encoding='utf-8') as f:
    code = f.read()

# Replace the imports
imports_to_add = """import { useCallback, useRef } from 'react';
import { useSearchParams } from 'next/navigation';
import { AppSidebar } from '@/components/app-sidebar';
import type { ChatSession } from '@/types/api';
"""
code = code.replace("import { useState, useEffect } from 'react';", "import { useState, useEffect, useCallback, useRef } from 'react';\nimport { useSearchParams } from 'next/navigation';\nimport { AppSidebar } from '@/components/app-sidebar';\nimport type { ChatSession } from '@/types/api';")

# Add the new state variables inside ChatPage
state_add_pattern = r"(const \[message, setMessage\] = useState\(''\);)"
new_state = """    const searchParams = useSearchParams();
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
    const [sessionsLoading, setSessionsLoading] = useState(true);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);
    \\1"""
code = re.sub(state_add_pattern, new_state, code)

# Add loadSessions, loadSession, and useEffect right before handleSend
hooks_code = """
    const loadSessions = useCallback(async () => {
        try {
            setSessionsLoading(true);
            const data = await api.getChatSessions();
            setSessions(data);
        } catch (error) {
            console.error('Failed to load sessions:', error);
        } finally {
            setSessionsLoading(false);
        }
    }, []);

    const loadSession = useCallback(async (sessionId: string) => {
        try {
            setIsLoading(true);
            const data = await api.getChatSessionMessages(sessionId);
            setMessages(data.messages as any);
            setCurrentSessionId(sessionId);
        } catch (error) {
            console.error('Failed to load session:', error);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        loadSessions();
        const sessionParam = searchParams.get('session');
        if (sessionParam) {
            loadSession(sessionParam);
        }
    }, [loadSessions, searchParams, loadSession]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleNewChat = () => {
        setMessages([]);
        setCurrentSessionId(null);
        setMessage('');
        router.push('/chat', { scroll: false });
        inputRef.current?.focus();
    };

    const handleSelectSession = (sessionId: string) => {
        if (sessionId === currentSessionId) return;
        loadSession(sessionId);
        router.push(`/chat?session=${sessionId}`, { scroll: false });
    };

    const handleNavigate = (path: string) => {
        router.push(path);
    };
"""
code = code.replace("const handleSend = async () => {", hooks_code + "\n    const handleSend = async () => {")

# Update handleSend to pass context_id
code = code.replace("agent_id: agentId,", "agent_id: agentId,\n                context_id: currentSessionId || undefined,")
code = code.replace("setSessionId(response.session_id);", """
            if (!currentSessionId && response.session_id) {
                setCurrentSessionId(response.session_id);
                router.push(`/chat?session=${response.session_id}`, { scroll: false });
            }
            loadSessions();
""")

# Fix the JSX structure
layout_start = """
        <div className="flex h-screen bg-white">
            {/* 데스크톱 사이드바 (항상 표시) */}
            <div className="hidden md:flex w-[260px] shrink-0">
                <AppSidebar
                    sessions={sessions}
                    currentSessionId={currentSessionId}
                    onSelectSession={handleSelectSession}
                    onNewChat={handleNewChat}
                    onNavigate={handleNavigate}
                    isLoadingSessions={sessionsLoading}
                    currentPath="/chat"
                />
            </div>
            
            {/* 모바일 사이드바 기능용 Sheet, 그리고 메인 컨텐츠 영역 */}
            <div className="flex-1 flex flex-col min-w-0 bg-gray-50">
"""

code = code.replace("""<div className="flex flex-col h-screen bg-gray-50">""", layout_start)

# Update Mobile Sidebar
sheet_content_target = """<SheetContent side="left" className="w-[300px] sm:w-[400px]">
                        <SheetHeader>
                            <SheetTitle className="flex items-center gap-2">
                                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center shrink-0">
                                    <span className="text-white text-base font-bold tracking-tight">ISOR</span>
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
                                onClick={() => { router.push('/chat/history'); setSidebarOpen(false); }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <Clock className="w-5 h-5 text-blue-600" />
                                <span className="font-medium">채팅 기록</span>
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
                    </SheetContent>"""

new_sheet_content = """<SheetContent side="left" className="p-0 w-[280px]">
                        <AppSidebar
                            sessions={sessions}
                            currentSessionId={currentSessionId}
                            onSelectSession={handleSelectSession}
                            onNewChat={handleNewChat}
                            onNavigate={handleNavigate}
                            isLoadingSessions={sessionsLoading}
                            isMobile
                            onClose={() => setSidebarOpen(false)}
                            currentPath="/chat"
                        />
                    </SheetContent>"""

code = code.replace(sheet_content_target, new_sheet_content)

# Inject current session name in header
# <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
header_old = """<header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">"""
header_new = """<header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
                <div className="hidden md:flex flex-1 items-center font-semibold text-gray-700">
                    {currentSessionId ? sessions.find(s=>s.session_id === currentSessionId)?.title || '대화 중' : '새 채팅'}
                </div>"""
code = code.replace(header_old, header_new)

# Add mobile "대화 중" title to header for mobile view
# Find where SheetTrigger is, it is for Mobile now.
mobile_trigger_old = """<button className="p-2 hover:bg-gray-100 rounded-lg">
                            <Menu className="w-6 h-6 text-gray-700" />
                        </button>"""
mobile_trigger_new = """<button className="p-2 hover:bg-gray-100 rounded-lg md:hidden">
                            <Menu className="w-6 h-6 text-gray-700" />
                        </button>
                        <div className="md:hidden flex-1 text-center font-medium text-gray-700">
                            {currentSessionId ? '대화 중' : 'ISOR AI'}
                        </div>
                        <button
                            onClick={handleNewChat}
                            className="p-2 hover:bg-gray-100 rounded-lg md:hidden"
                        >
                            <Plus className="w-5 h-5 text-gray-700" />
                        </button>"""
code = code.replace(mobile_trigger_old, mobile_trigger_new)

# Add ref to input textarea:
code = code.replace("""className="min-h-[60px] pr-12 resize-none\"""", """className="min-h-[60px] pr-12 resize-none"
                        ref={inputRef}""")

# Add div ref at the end of messages map
old_end_msgs = """{isLoading && ("""
new_end_msgs = """<div ref={messagesEndRef} />\n                {isLoading && ("""
code = code.replace(old_end_msgs, new_end_msgs)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(code)

print("Refactor complete.")
