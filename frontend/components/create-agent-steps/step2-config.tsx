'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AgentDraft } from '@/types/agent';
import { Save, ArrowLeft, Database, Bot, Sparkles, Settings2 } from 'lucide-react';

interface Step2ConfigProps {
    draft: AgentDraft;
    setDraft: (draft: AgentDraft) => void;
    onBack: () => void;
    onComplete: () => void;
}

export function Step2Config({ draft, setDraft, onBack, onComplete }: Step2ConfigProps) {

    const handleChange = (field: keyof AgentDraft, value: any) => {
        setDraft({ ...draft, [field]: value });
    };

    return (
        <div className="flex flex-col h-full max-w-4xl mx-auto p-6 gap-8 overflow-y-auto">

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Left Column: Basic Info + Prompt */}
                <div className="space-y-6">
                    <div className="bg-white p-6 rounded-xl border border-gray-200 space-y-4">
                        <h3 className="text-lg font-semibold flex items-center gap-2">
                            <Bot className="w-5 h-5 text-blue-600" />
                            기본 정보
                        </h3>

                        <div className="space-y-2">
                            <Label htmlFor="name">에이전트 이름</Label>
                            <Input
                                id="name"
                                value={draft.name}
                                onChange={(e) => handleChange('name', e.target.value)}
                                placeholder="예: 마케팅 카피라이터"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="description">설명</Label>
                            <Textarea
                                id="description"
                                value={draft.description}
                                onChange={(e) => handleChange('description', e.target.value)}
                                placeholder="이 에이전트가 하는 일을 간단히 설명해주세요."
                                className="min-h-[80px]"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label>카테고리</Label>
                            <Select
                                value={draft.category}
                                onValueChange={(value) => handleChange('category', value)}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="카테고리 선택" />
                                </SelectTrigger>
                                <SelectContent>
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

                        <div className="space-y-2">
                            <Label>공개 범위</Label>
                            <Select
                                value={draft.visibility}
                                onValueChange={(value) => handleChange('visibility', value as 'team' | 'public')}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="공개 범위 선택" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="team">👥 팀 공유</SelectItem>
                                    <SelectItem value="public">🌐 전체 공개</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    <div className="bg-white p-6 rounded-xl border border-gray-200 space-y-4">
                        <h3 className="text-lg font-semibold flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-purple-600" />
                            모델 설정
                        </h3>

                        <div className="space-y-2">
                            <Label>사용 모델</Label>
                            <Select
                                value={draft.model}
                                onValueChange={(value) => handleChange('model', value)}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder="모델 선택" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="AUTO">⚡ Auto (자동 선택)</SelectItem>
                                    <SelectItem value="gemini/gemini-2.5-flash-lite">Gemini 2.5 Flash Lite</SelectItem>
                                    <SelectItem value="gemini/gemini-2.5-flash">Gemini 2.5 Flash</SelectItem>
                                    <SelectItem value="gemini/gemini-3.1-flash-lite-preview">Gemini 3.1 Flash Lite</SelectItem>
                                    <SelectItem value="gemini/gemini-3.1-pro-preview">Gemini 3.1 Pro</SelectItem>
                                    <SelectItem value="gpt-5.4-nano">GPT-5.4 Nano</SelectItem>
                                    <SelectItem value="gpt-5.4-mini">GPT-5.4 Mini</SelectItem>
                                    <SelectItem value="gpt-5.4">GPT-5.4</SelectItem>
                                    <SelectItem value="gpt-5.4-pro">GPT-5.4 Pro</SelectItem>
                                    <SelectItem value="claude-haiku-4-5">Claude Haiku 4.5</SelectItem>
                                    <SelectItem value="claude-sonnet-4-6">Claude Sonnet 4.6</SelectItem>
                                    <SelectItem value="claude-opus-4-6">Claude Opus 4.6</SelectItem>
                                    <SelectItem value="perplexity/sonar">Perplexity Sonar</SelectItem>
                                    <SelectItem value="perplexity/sonar-pro">Perplexity Sonar Pro</SelectItem>
                                </SelectContent>
                            </Select>
                            <p className="text-xs text-gray-500">
                                * Auto를 선택하면 질문에 맞는 최적 모델이 자동 선택됩니다.
                            </p>
                        </div>

                        {/* RAG 토글 */}
                        <div className="flex items-center justify-between pt-2 border-t">
                            <div>
                                <Label className="text-sm font-medium">문서 참조 (RAG)</Label>
                                <p className="text-xs text-gray-500">활성화 시 AI 드라이브 문서를 참조하여 답변합니다.</p>
                            </div>
                            <Switch
                                checked={draft.ragEnabled}
                                onCheckedChange={(checked) => handleChange('ragEnabled', checked)}
                            />
                        </div>
                    </div>
                </div>

                {/* Right Column: Prompt + Examples */}
                <div className="space-y-6">
                    <div className="bg-white p-6 rounded-xl border border-gray-200 space-y-4 flex flex-col">
                        <h3 className="text-lg font-semibold flex items-center gap-2">
                            <Settings2 className="w-5 h-5 text-orange-600" />
                            프롬프트 및 예시
                        </h3>

                        <div className="space-y-2 flex-1 flex flex-col">
                            <Label htmlFor="systemPrompt">시스템 프롬프트 (System Prompt)</Label>
                            <Textarea
                                id="systemPrompt"
                                value={draft.systemPrompt}
                                onChange={(e) => handleChange('systemPrompt', e.target.value)}
                                placeholder="에이전트의 페르소나와 행동 지침을 정의하세요."
                                className="flex-1 min-h-[150px] font-mono text-sm leading-relaxed"
                            />
                            <p className="text-xs text-gray-500">
                                * Step 1에서 AI와 대화한 내용이 프롬프트로 자동 변환되었습니다.
                            </p>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="inputExample">입력 예시</Label>
                            <Textarea
                                id="inputExample"
                                value={draft.inputExample || ''}
                                onChange={(e) => handleChange('inputExample', e.target.value)}
                                placeholder="에이전트에 입력할 예시를 작성하세요"
                                className="min-h-[80px] text-sm"
                            />
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="outputExample">출력 예시</Label>
                            <Textarea
                                id="outputExample"
                                value={draft.outputExample || ''}
                                onChange={(e) => handleChange('outputExample', e.target.value)}
                                placeholder="에이전트가 출력할 예시를 작성하세요"
                                className="min-h-[80px] text-sm"
                            />
                        </div>
                    </div>
                </div>
            </div>

            {/* Actions */}
            <div className="flex justify-end gap-4 pt-4 border-t border-gray-200">
                <Button variant="outline" onClick={onBack}>
                    이전 단계 (채팅)
                </Button>
                <Button onClick={onComplete} className="bg-blue-600 hover:bg-blue-700 min-w-[120px]">
                    <Save className="w-4 h-4 mr-2" />
                    에이전트 생성 완료
                </Button>
            </div>
        </div>
    );
}
