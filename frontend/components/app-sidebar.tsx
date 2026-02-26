'use client';

import { useState, useEffect, useRef } from 'react';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
    DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';
import {
    MessageSquare, FolderOpen, Bot, Settings, Plus,
    LogOut, Clock, MoreHorizontal, Pencil, Trash2
} from 'lucide-react';
import type { ChatSession } from '@/types/api';
import { api } from '@/lib/api';

interface AppSidebarProps {
    sessions?: ChatSession[];
    currentSessionId?: string | null;
    onSelectSession?: (sessionId: string) => void;
    onNewChat?: () => void;
    onNavigate: (path: string) => void;
    onRenameSession?: (sessionId: string, newTitle: string) => void;
    onDeleteSession?: (sessionId: string) => void;
    isLoadingSessions?: boolean;
    isMobile?: boolean;
    onClose?: () => void;
    currentPath: string;
}

export function AppSidebar({
    sessions: propSessions,
    currentSessionId = null,
    onSelectSession: propOnSelectSession,
    onNewChat: propOnNewChat,
    onNavigate,
    onRenameSession,
    onDeleteSession,
    isLoadingSessions: propIsLoadingSessions,
    isMobile = false,
    onClose,
    currentPath
}: AppSidebarProps) {
    const [fetchedSessions, setFetchedSessions] = useState<ChatSession[]>([]);
    const [isFetching, setIsFetching] = useState(false);
    const [hoveredSessionId, setHoveredSessionId] = useState<string | null>(null);
    const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
    const [editingTitle, setEditingTitle] = useState('');
    const [menuOpenSessionId, setMenuOpenSessionId] = useState<string | null>(null);
    const editInputRef = useRef<HTMLInputElement>(null);

    const isControlled = propSessions !== undefined;
    const sessions = isControlled ? propSessions : fetchedSessions;
    const isLoadingSessions = isControlled ? propIsLoadingSessions : isFetching;

    useEffect(() => {
        if (!isControlled) {
            const loadSessions = async () => {
                setIsFetching(true);
                try {
                    const data = await api.getChatSessions();
                    setFetchedSessions(data);
                } catch (error) {
                    console.error('Failed to load sessions in sidebar:', error);
                } finally {
                    setIsFetching(false);
                }
            };
            loadSessions();
        }
    }, [isControlled]);

    // Focus input when editing starts
    useEffect(() => {
        if (editingSessionId && editInputRef.current) {
            editInputRef.current.focus();
            editInputRef.current.select();
        }
    }, [editingSessionId]);

    const handleClick = (action: () => void) => {
        action();
        if (isMobile && onClose) onClose();
    };

    const handleSelectSession = (sessionId: string) => {
        if (propOnSelectSession) {
            propOnSelectSession(sessionId);
        } else {
            onNavigate(`/chat?session=${sessionId}`);
        }
    };

    const handleNewChat = () => {
        if (propOnNewChat) {
            propOnNewChat();
        } else {
            onNavigate('/chat');
        }
    };

    const handleStartRename = (session: ChatSession) => {
        setEditingSessionId(session.session_id);
        setEditingTitle(session.title);
    };

    const handleConfirmRename = async () => {
        if (!editingSessionId || !editingTitle.trim()) {
            setEditingSessionId(null);
            return;
        }

        try {
            if (onRenameSession) {
                onRenameSession(editingSessionId, editingTitle.trim());
            } else {
                await api.renameChatSession(editingSessionId, editingTitle.trim());
                // If uncontrolled, refresh sessions
                if (!isControlled) {
                    const data = await api.getChatSessions();
                    setFetchedSessions(data);
                }
            }
        } catch (error) {
            console.error('Failed to rename session:', error);
        } finally {
            setEditingSessionId(null);
        }
    };

    const handleDeleteSession = async (sessionId: string) => {
        if (!confirm('이 채팅을 삭제하시겠습니까?')) return;

        try {
            if (onDeleteSession) {
                onDeleteSession(sessionId);
            } else {
                await api.deleteChatSession(sessionId);
                // If uncontrolled, refresh sessions
                if (!isControlled) {
                    const data = await api.getChatSessions();
                    setFetchedSessions(data);
                }
                // If the deleted session is the current one, navigate to new chat
                if (currentSessionId === sessionId) {
                    handleNewChat();
                }
            }
        } catch (error) {
            console.error('Failed to delete session:', error);
        }
    };

    const handleRenameKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleConfirmRename();
        } else if (e.key === 'Escape') {
            setEditingSessionId(null);
        }
    };

    return (
        <div className="flex flex-col h-full bg-gray-50 border-r border-gray-200">
            {/* 로고 + 새 채팅 버튼 */}
            <div className="p-4 border-b border-gray-200">
                <div className="flex items-center gap-2 mb-4">
                    <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center shrink-0">
                        <span className="text-white text-xs font-bold">ISOR</span>
                    </div>
                    <span className="font-semibold text-gray-900">AI 플랫폼</span>
                </div>
            </div>

            {/* 네비게이션 메뉴 */}
            <nav className="px-3 py-3 space-y-1 border-b border-gray-100">
                <button
                    onClick={() => handleClick(handleNewChat)}
                    className={`w-full flex items-center gap-3 px-3 py-2 text-left text-sm font-medium rounded-lg transition-colors ${(currentPath === '/chat' || currentPath.startsWith('/chat')) && !currentSessionId
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-700 hover:bg-gray-100'
                        }`}
                >
                    <MessageSquare className="w-4 h-4" />
                    새 채팅
                </button>
                <button
                    onClick={() => handleClick(() => onNavigate('/drive'))}
                    className={`w-full flex items-center gap-3 px-3 py-2 text-left text-sm font-medium rounded-lg transition-colors ${currentPath.startsWith('/drive')
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-700 hover:bg-gray-100'
                        }`}
                >
                    <FolderOpen className="w-4 h-4" />
                    AI Drive
                </button>
                <button
                    onClick={() => handleClick(() => onNavigate('/agents'))}
                    className={`w-full flex items-center gap-3 px-3 py-2 text-left text-sm font-medium rounded-lg transition-colors ${currentPath.startsWith('/agents')
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-700 hover:bg-gray-100'
                        }`}
                >
                    <Bot className="w-4 h-4" />
                    Agent Hub
                </button>
                <button
                    onClick={() => handleClick(() => onNavigate('/settings'))}
                    className={`w-full flex items-center gap-3 px-3 py-2 text-left text-sm font-medium rounded-lg transition-colors ${currentPath.startsWith('/settings')
                        ? 'bg-blue-50 text-blue-700'
                        : 'text-gray-700 hover:bg-gray-100'
                        }`}
                >
                    <Settings className="w-4 h-4" />
                    설정
                </button>
            </nav>

            {/* 내 채팅 기록 */}
            <div className="px-4 pt-4 pb-2 border-t border-gray-100">
                <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" /> 내 채팅
                </span>
            </div>

            <ScrollArea className="flex-1 px-2">
                {isLoadingSessions ? (
                    <div className="px-3 py-4 text-sm text-gray-400 text-center">
                        불러오는 중...
                    </div>
                ) : sessions && sessions.length === 0 ? (
                    <div className="px-3 py-4 text-sm text-gray-400 text-center">
                        채팅 기록이 없습니다
                    </div>
                ) : (
                    <div className="space-y-0.5 pb-4">
                        {sessions && sessions.map((session) => (
                            <div
                                key={session.session_id}
                                className="relative group"
                                onMouseEnter={() => setHoveredSessionId(session.session_id)}
                                onMouseLeave={() => {
                                    if (menuOpenSessionId !== session.session_id) {
                                        setHoveredSessionId(null);
                                    }
                                }}
                            >
                                {editingSessionId === session.session_id ? (
                                    /* 이름 편집 모드 */
                                    <input
                                        ref={editInputRef}
                                        type="text"
                                        value={editingTitle}
                                        onChange={(e) => setEditingTitle(e.target.value)}
                                        onBlur={handleConfirmRename}
                                        onKeyDown={handleRenameKeyDown}
                                        className="w-full px-3 py-2 rounded-lg text-sm border-2 border-blue-500 outline-none bg-white"
                                    />
                                ) : (
                                    /* 일반 표시 모드 */
                                    <button
                                        onClick={() => handleClick(() => handleSelectSession(session.session_id))}
                                        className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center ${currentSessionId === session.session_id
                                            ? 'bg-gray-200 text-gray-900 font-medium'
                                            : 'text-gray-600 hover:bg-gray-100'
                                            }`}
                                        title={session.title}
                                    >
                                        <span className="truncate flex-1 pr-6">{session.title}</span>
                                    </button>
                                )}

                                {/* ... 더보기 버튼 (hover 또는 메뉴 열림 시 표시) */}
                                {editingSessionId !== session.session_id && (hoveredSessionId === session.session_id || menuOpenSessionId === session.session_id) && (
                                    <div className="absolute right-1 top-1/2 -translate-y-1/2">
                                        <DropdownMenu
                                            onOpenChange={(open) => {
                                                if (open) {
                                                    setMenuOpenSessionId(session.session_id);
                                                } else {
                                                    setMenuOpenSessionId(null);
                                                    setHoveredSessionId(null);
                                                }
                                            }}
                                        >
                                            <DropdownMenuTrigger asChild>
                                                <button
                                                    className="p-1 rounded hover:bg-gray-200 transition-colors"
                                                    onClick={(e) => e.stopPropagation()}
                                                >
                                                    <MoreHorizontal className="w-4 h-4 text-gray-500" />
                                                </button>
                                            </DropdownMenuTrigger>
                                            <DropdownMenuContent align="end" className="w-40">
                                                <DropdownMenuItem
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleStartRename(session);
                                                    }}
                                                    className="cursor-pointer"
                                                >
                                                    <Pencil className="w-4 h-4 mr-2" />
                                                    이름 바꾸기
                                                </DropdownMenuItem>
                                                <DropdownMenuItem
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        handleDeleteSession(session.session_id);
                                                    }}
                                                    className="cursor-pointer text-red-600 focus:text-red-600"
                                                >
                                                    <Trash2 className="w-4 h-4 mr-2" />
                                                    삭제
                                                </DropdownMenuItem>
                                            </DropdownMenuContent>
                                        </DropdownMenu>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </ScrollArea>

            {/* 하단: 로그아웃 */}
            <div className="p-3 border-t border-gray-200 mt-auto">
                <button
                    onClick={() => handleClick(() => {
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('user_name');
                        localStorage.removeItem('department');
                        onNavigate('/auth/login');
                    })}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                >
                    <LogOut className="w-4 h-4" />
                    로그아웃
                </button>
            </div>
        </div>
    );
}
