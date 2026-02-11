'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AgentDraft } from '@/types/agent';
import { Save, ArrowLeft, Database, Bot, Sparkles } from 'lucide-react';

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
                {/* Left Column: Basic Info & Model */}
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
                                    <SelectItem value="Gemini-1.5-Flash">Gemini 1.5 Flash (빠름/저렴)</SelectItem>
                                    <SelectItem value="Gemini-1.5-Pro">Gemini 1.5 Pro (고성능)</SelectItem>
                                    <SelectItem value="GPT-4o">GPT-4o (범용)</SelectItem>
                                    <SelectItem value="Claude-3.5-Sonnet">Claude 3.5 Sonnet (논리적)</SelectItem>
                                </SelectContent>
                            </Select>
                            <p className="text-xs text-gray-500">
                                * 복잡한 추론이 필요하면 Pro/GPT-4o, 단순 작업은 Flash를 추천합니다.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Right Column: Prompt & Knowledge */}
                <div className="space-y-6">
                    <div className="bg-white p-6 rounded-xl border border-gray-200 space-y-4 h-full flex flex-col">
                        <h3 className="text-lg font-semibold flex items-center gap-2">
                            <Settings2 className="w-5 h-5 text-orange-600" />
                            프롬프트 엔지니어링
                        </h3>

                        <div className="space-y-2 flex-1 flex flex-col">
                            <Label htmlFor="systemPrompt">시스템 프롬프트 (System Prompt)</Label>
                            <Textarea
                                id="systemPrompt"
                                value={draft.systemPrompt}
                                onChange={(e) => handleChange('systemPrompt', e.target.value)}
                                placeholder="에이전트의 페르소나와 행동 지침을 정의하세요."
                                className="flex-1 min-h-[200px] font-mono text-sm leading-relaxed"
                            />
                            <p className="text-xs text-gray-500">
                                * Step 1에서 AI와 대화한 내용이 프롬프트로 자동 변환되었습니다.
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Knowledge Base Section (Full Width) */}
            <div className="bg-white p-6 rounded-xl border border-gray-200 space-y-4">
                <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold flex items-center gap-2">
                        <Database className="w-5 h-5 text-green-600" />
                        지식 연동 (RAG)
                    </h3>
                    <Switch
                        checked={draft.ragEnabled}
                        onCheckedChange={(checked) => handleChange('ragEnabled', checked)}
                    />
                </div>

                {draft.ragEnabled && (
                    <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 animate-in fade-in slide-in-from-top-2">
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <Label>연동할 문서함 선택</Label>
                                <Select
                                    value={draft.knowledgeBaseId}
                                    onValueChange={(value) => handleChange('knowledgeBaseId', value)}
                                >
                                    <SelectTrigger>
                                        <SelectValue placeholder="문서함 선택" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="kb-marketing">마케팅 팀 공유 문서함</SelectItem>
                                        <SelectItem value="kb-tech">개발 팀 기술 문서함</SelectItem>
                                        <SelectItem value="kb-hr">인사 규정 문서함</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <p className="text-sm text-gray-600">
                                선택된 문서함의 내용을 기반으로 에이전트가 답변을 생성합니다.
                            </p>
                        </div>
                    </div>
                )}
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

import { Settings2 } from 'lucide-react';
