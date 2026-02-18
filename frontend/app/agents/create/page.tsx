'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Check, Sparkles, Settings2 } from 'lucide-react';
import { AgentDraft, Step1Chat } from '@/components/create-agent-steps/step1-chat';
import { Step2Config } from '@/components/create-agent-steps/step2-config';
import { api } from '@/lib/api';

export default function CreateAgentPage() {
    const router = useRouter();
    const [currentStep, setCurrentStep] = useState<1 | 2>(1);
    const [draftId, setDraftId] = useState<string | null>(null);
    const [draft, setDraft] = useState<AgentDraft>({
        name: '',
        description: '',
        goal: '',
        model: 'Gemini-1.5-Flash', // Default
        systemPrompt: '',
        ragEnabled: false,
        knowledgeBaseId: undefined,
        category: '업무보조', // Default
        visibility: 'private', // Default
        messages: []
    });

    const handleNext = async () => {
        if (currentStep !== 1 || !draft.messages?.length) {
            setCurrentStep(2);
            return;
        }
        try {
            const res = await api.createAgentDraft({ selected_messages: draft.messages });
            setDraftId(res.draft_id);
            if (res.filled) {
                const f = res.filled;
                setDraft(prev => ({
                    ...prev,
                    name: f.name ?? prev.name,
                    description: f.description ?? prev.description,
                    category: f.category ?? prev.category,
                    systemPrompt: f.system_prompt ?? prev.systemPrompt
                }));
            }
            setCurrentStep(2);
        } catch (e) {
            console.error('Draft 생성 실패, Step2만 이동:', e);
            setCurrentStep(2);
        }
    };

    const handleBack = () => {
        if (currentStep === 2) setCurrentStep(1);
        else router.back();
    };

    const handleComplete = async () => {
        let id = draftId;
        let name = draft.name;
        let description = draft.description;
        let category = draft.category;
        let inputExample = draft.messages?.[0]?.content ?? '';
        let outputExample = draft.messages?.[1]?.content ?? '';

        if (!id && draft.messages?.length) {
            try {
                const res = await api.createAgentDraft({ selected_messages: draft.messages });
                id = res.draft_id;
                if (res.filled) {
                    name = res.filled.name ?? name;
                    description = res.filled.description ?? description;
                    category = res.filled.category ?? category;
                    inputExample = res.filled.input_example ?? inputExample;
                    outputExample = res.filled.output_example ?? outputExample;
                }
            } catch (e) {
                console.error(e);
                alert('Draft 생성에 실패했습니다.');
                return;
            }
        }
        if (!id) {
            alert('먼저 [다음]을 눌러 기획을 완료해 주세요.');
            return;
        }
        try {
            await api.updateAgentStep1({
                draft_id: id,
                name,
                description,
                input_example: inputExample,
                output_example: outputExample
            });

            await api.updateAgentStep2({
                draft_id: id,
                category,
                visibility: (draft.visibility || 'private').toUpperCase() as 'PRIVATE' | 'TEAM' | 'PUBLIC',
                model_type: draft.model,
                use_rag: draft.ragEnabled,
                linked_doc_ids: draft.knowledgeBaseId ? [draft.knowledgeBaseId] : []
            });

            await api.publishAgent({ draft_id: id });

            alert('에이전트가 생성되었습니다!');
            router.push('/agents');
        } catch (error) {
            console.error('에이전트 생성 실패:', error);
            alert('에이전트 생성에 실패했습니다. 다시 시도해주세요.');
        }
    };

    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={handleBack}>
                        <ArrowLeft className="w-5 h-5 text-gray-600" />
                    </Button>
                    <h1 className="text-xl font-bold text-gray-900">새 에이전트 만들기</h1>
                </div>

                {/* Steps Indicator */}
                <div className="flex items-center gap-2">
                    <div className={`flex items-center px-4 py-2 rounded-full ${currentStep === 1 ? 'bg-blue-100 text-blue-700' : 'text-gray-500'}`}>
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center mr-2 ${currentStep === 1 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}`}>1</div>
                        <Sparkles className="w-4 h-4 mr-1" />
                        <span className="font-medium">기획 (Chat)</span>
                    </div>
                    <div className="w-8 h-px bg-gray-300"></div>
                    <div className={`flex items-center px-4 py-2 rounded-full ${currentStep === 2 ? 'bg-blue-100 text-blue-700' : 'text-gray-500'}`}>
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center mr-2 ${currentStep === 2 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}`}>2</div>
                        <Settings2 className="w-4 h-4 mr-1" />
                        <span className="font-medium">설정 (Config)</span>
                    </div>
                </div>

                <div className="w-24"></div> {/* Spacer for center alignment */}
            </header>

            {/* Main Content */}
            <main className="flex-1 overflow-hidden">
                {currentStep === 1 ? (
                    <Step1Chat
                        draft={draft}
                        setDraft={setDraft}
                        onNext={handleNext}
                    />
                ) : (
                    <Step2Config
                        draft={draft}
                        setDraft={setDraft}
                        onBack={handleBack}
                        onComplete={handleComplete}
                    />
                )}
            </main>
        </div>
    );
}
