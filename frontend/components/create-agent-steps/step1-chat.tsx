'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AgentDraft } from '@/types/agent';
import { Send, Bot, User, Sparkles } from 'lucide-react';

export type { AgentDraft };

interface Step1ChatProps {
    draft: AgentDraft;
    setDraft: (draft: AgentDraft) => void;
    onNext: () => void;
}

interface Message {
    role: 'user' | 'assistant';
    content: string;
}

export function Step1Chat({ draft, setDraft, onNext }: Step1ChatProps) {
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', content: '안녕하세요! 어떤 에이전트를 만들고 싶으신가요? 에이전트의 역할이나 목표를 말씀해 주세요.' }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading) return;

        const userMsg = inputValue;
        setInputValue('');
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setIsLoading(true);

        // Simulate Orchestrator analysis & response
        setTimeout(() => {
            let aiResponse = '';

            // Simple mock logic based on interaction count
            if (messages.length === 1) {
                aiResponse = `네, '${userMsg}' 역할을 수행하는 에이전트를 기획해 드릴게요.\n\n에이전트 이름은 "AI Assistant"로, 목표는 사용자의 요청을 수행하는 것으로 설정했습니다.\n\n이 에이전트가 특별히 참고해야 할 문서나 데이터가 있나요?`;

                // Update draft mock
                setDraft({
                    ...draft,
                    name: 'AI Assistant',
                    description: userMsg,
                    goal: userMsg,
                    systemPrompt: `You are a helpful assistant specialized in ${userMsg}.`,
                    category: draft.category || '업무보조',
                    visibility: draft.visibility || 'private'
                });
            } else if (messages.length === 3) {
                aiResponse = `알겠습니다. 지식 기반도 고려하여 설정을 업데이트했습니다.\n\n이제 기본적인 기획이 완료되었습니다. [다음] 버튼을 눌러 세부 설정을 확인하고 모델을 선택해 주세요.`;
                setDraft({
                    ...draft,
                    ragEnabled: true
                });
            } else {
                aiResponse = `추가적인 요청사항이 반영되었습니다. 더 수정할 내용이 없다면 [다음] 단계로 진행해 주세요.`;
            }

            const updatedMessages = [...messages, { role: 'user', content: userMsg }, { role: 'assistant', content: aiResponse }];
            setMessages(prev => [...prev, { role: 'assistant', content: aiResponse }]);
            // 대화 내용을 draft에 저장
            setDraft({ ...draft, messages: updatedMessages });
            setIsLoading(false);
        }, 1500);
    };

    return (
        <div className="flex h-full gap-6 max-w-6xl mx-auto p-6">
            {/* Chat Interface (Left) */}
            <div className="flex-1 flex flex-col bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="bg-gray-50 px-4 py-3 border-b border-gray-200 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-blue-600" />
                        <span className="font-medium text-sm text-gray-700">Agent Architect AI</span>
                    </div>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={onNext}
                        className="text-xs text-gray-500 hover:text-gray-900 h-8 px-2"
                    >
                        건너뛰기 (직접 설정) &rarr;
                    </Button>
                </div>

                <ScrollArea className="flex-1 p-4" ref={scrollRef}>
                    <div className="space-y-4">
                        {messages.map((msg, idx) => (
                            <div key={idx} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                {msg.role === 'assistant' && (
                                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                                        <Bot className="w-5 h-5 text-blue-600" />
                                    </div>
                                )}
                                <div className={`max-w-[80%] rounded-lg px-4 py-3 text-sm whitespace-pre-wrap ${msg.role === 'user'
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-gray-100 text-gray-800'
                                    }`}>
                                    {msg.content}
                                </div>
                                {msg.role === 'user' && (
                                    <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                                        <User className="w-5 h-5 text-gray-600" />
                                    </div>
                                )}
                            </div>
                        ))}
                        {isLoading && (
                            <div className="flex gap-3">
                                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0">
                                    <Bot className="w-5 h-5 text-blue-600" />
                                </div>
                                <div className="bg-gray-100 rounded-lg px-4 py-3 flex items-center gap-1">
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-75" />
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-150" />
                                </div>
                            </div>
                        )}
                    </div>
                </ScrollArea>

                <div className="p-4 border-t border-gray-200 bg-white">
                    <form
                        onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}
                        className="flex gap-2"
                    >
                        <Input
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            placeholder="에이전트에 대해 설명해주세요 (예: '파이썬 코드 리뷰만 해주는 에이전트')"
                            className="flex-1"
                        />
                        <Button type="submit" disabled={isLoading || !inputValue.trim()}>
                            <Send className="w-4 h-4" />
                        </Button>
                    </form>
                </div>
            </div>

            {/* Live Draft Preview (Right) */}
            <div className="w-80 flex flex-col gap-4">
                <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
                    <h3 className="text-sm font-semibold text-blue-800 mb-3 flex items-center gap-2">
                        <Bot className="w-4 h-4" />
                        실시간 생성된 초안
                    </h3>

                    <div className="space-y-4 text-sm">
                        <div className="space-y-1">
                            <label className="text-xs text-blue-600 font-medium">이름</label>
                            <Input
                                value={draft.name}
                                onChange={(e) => setDraft({ ...draft, name: e.target.value })}
                                placeholder="에이전트 이름"
                                className="text-sm"
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs text-blue-600 font-medium">설명</label>
                            <Input
                                value={draft.description}
                                onChange={(e) => setDraft({ ...draft, description: e.target.value })}
                                placeholder="에이전트 설명"
                                className="text-sm"
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-xs text-blue-600 font-medium">목표</label>
                            <Input
                                value={draft.goal}
                                onChange={(e) => setDraft({ ...draft, goal: e.target.value })}
                                placeholder="에이전트 목표"
                                className="text-sm"
                            />
                        </div>
                    </div>
                </div>

                <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 flex-1 flex flex-col justify-center text-center">
                    <p className="text-sm text-gray-500 mb-4">
                        AI와의 대화가 충분하다면<br />다음 단계로 이동하여 디테일을 수정하세요.
                    </p>
                    <Button onClick={onNext} className="w-full bg-blue-600 hover:bg-blue-700">
                        다음 단계로 이동 →
                    </Button>
                </div>
            </div>
        </div>
    );
}
