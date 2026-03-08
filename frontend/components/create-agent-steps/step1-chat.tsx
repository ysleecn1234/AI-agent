'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AgentDraft } from '@/types/agent';
import { Send, Bot, User, Sparkles } from 'lucide-react';
import { api } from '@/lib/api';

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

const ARCHITECT_SYSTEM_PROMPT = `당신은 AI 에이전트 기획을 도와주는 "Agent Architect"입니다.
사용자가 원하는 에이전트의 역할, 기능, 대상 사용자를 파악하여 에이전트를 기획해 주세요.

대화를 통해 다음 정보를 자연스럽게 수집하고 구체화하세요:
1. 에이전트 이름
2. 에이전트 설명 (한 줄)
3. 에이전트의 목표/역할
4. 실제 사용자가 입력할 법한 구체적인 질문 예시 ("입력 예시")
5. 에이전트가 그 질문에 대해 답변하는 모의 응답 형태 그대로 작성 ("출력 예시" - 단순 설명이 아닌 진짜 마크다운 표나 JSON 등 최종 응답 포맷)
6. 명확한 규칙과 역할을 부여하는 구체적인 행동 지침 ("시스템 프롬프트")

응답 마지막에 항상 아래 형식으로 현재까지의 초안을 정리해 주세요:
---DRAFT---
이름: (에이전트 이름)
설명: (한 줄 설명)
목표: (에이전트의 핵심 목표)
입력 예시: (사용자의 구체적인 질문 예시 1개)
출력 예시: (입력 예시에 대한 실제 에이전트의 완성된 답변 구조/예시)
프롬프트: (시스템 프롬프트 초안)
---END---`;

export function Step1Chat({ draft, setDraft, onNext }: Step1ChatProps) {
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', content: '안녕하세요! 어떤 에이전트를 만들고 싶으신가요? 에이전트의 역할이나 목표를 말씀해 주세요.' }
    ]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    // Parse draft info from AI response
    const parseDraftFromResponse = (response: string) => {
        const draftMatch = response.match(/---DRAFT---([\s\S]*?)---END---/);
        if (!draftMatch) return;

        const draftText = draftMatch[1];
        const nameMatch = draftText.match(/이름:\s*(.+)/);
        const descMatch = draftText.match(/설명:\s*(.+)/);
        const goalMatch = draftText.match(/목표:\s*(.+)/);
        const inputExampleMatch = draftText.match(/입력 예시:\s*(.+)/);
        // 출력 예시와 프롬프트는 여러 줄일 수 있으므로 추출 방식을 조정
        const outputExampleMatch = draftText.match(/출력 예시:\s*([\s\S]*?)(?=\n프롬프트:|$)/);
        const promptMatch = draftText.match(/프롬프트:\s*([\s\S]*?)(?=\n(?:이름|설명|목표|입력 예시|출력 예시):|$)/);

        setDraft({
            ...draft,
            name: nameMatch?.[1]?.trim() || draft.name,
            description: descMatch?.[1]?.trim() || draft.description,
            goal: goalMatch?.[1]?.trim() || draft.goal,
            inputExample: inputExampleMatch?.[1]?.trim() || draft.inputExample,
            outputExample: outputExampleMatch?.[1]?.trim() || draft.outputExample,
            systemPrompt: promptMatch?.[1]?.trim() || draft.systemPrompt,
        });
    };

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading) return;

        const userMsg = inputValue;
        setInputValue('');
        const newMessages: Message[] = [...messages, { role: 'user', content: userMsg }];
        setMessages(newMessages);
        setIsLoading(true);

        try {
            // Build conversation context with system prompt
            const contextMessage = `[시스템 지시] ${ARCHITECT_SYSTEM_PROMPT}\n\n[대화 기록]\n${newMessages.map(m => `${m.role === 'user' ? '사용자' : 'AI'}: ${m.content}`).join('\n')}\n\n위 대화를 바탕으로 Agent Architect로서 응답해 주세요.`;

            const response = await api.sendMessage({
                message: contextMessage,
                model_type: 'AUTO',
                use_rag: false,
            });

            const aiResponse = response.response;
            setMessages(prev => [...prev, { role: 'assistant', content: aiResponse }]);

            // Parse draft info from response
            parseDraftFromResponse(aiResponse);

            // Save messages to draft
            const updatedMessages = [...newMessages, { role: 'assistant' as const, content: aiResponse }];
            setDraft({ ...draft, messages: updatedMessages });
        } catch (error) {
            console.error('AI 응답 실패:', error);
            const fallbackResponse = '죄송합니다. 일시적인 오류가 발생했습니다. 다시 시도해 주세요.';
            setMessages(prev => [...prev, { role: 'assistant', content: fallbackResponse }]);
        } finally {
            setIsLoading(false);
        }
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
                                    {/* Hide draft block from display */}
                                    {msg.content.replace(/---DRAFT---[\s\S]*?---END---/g, '').trim()}
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
