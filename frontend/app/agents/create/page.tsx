'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Sparkles, Settings2, FileText } from 'lucide-react';
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
        model: 'AUTO',
        systemPrompt: '',
        ragEnabled: false,
        knowledgeBaseId: undefined,
        category: '기타',
        visibility: 'team',
        inputExample: '',
        outputExample: '',
        messages: []
    });

    const handleNext = async () => {
        if (currentStep === 1) {
            // Step 1 → Step 2: AI 채팅 → 설정
            if (draft.messages?.length) {
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
                            systemPrompt: f.system_prompt ?? prev.systemPrompt,
                            inputExample: f.input_example ?? prev.inputExample,
                            outputExample: f.output_example ?? prev.outputExample,
                        }));
                    }
                } catch (e) {
                    console.error('Draft 생성 실패:', e);
                }
            }
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
        let inputExample = draft.inputExample || draft.messages?.[0]?.content || '';
        let outputExample = draft.outputExample || draft.messages?.[1]?.content || '';

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
            // No draft from chat — create one with manual data
            try {
                const res = await api.createAgentDraft({
                    selected_messages: [{ role: 'user', content: draft.description || draft.name }]
                });
                id = res.draft_id;
            } catch (e) {
                console.error(e);
                alert('Draft 생성에 실패했습니다.');
                return;
            }
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
                visibility: (draft.visibility || 'team').toUpperCase() as 'PRIVATE' | 'TEAM' | 'PUBLIC',
                model_type: draft.model || 'AUTO',
                use_rag: draft.ragEnabled,
                linked_doc_ids: []
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
                    {/* Step 1 */}
                    <div className={`flex items-center px-3 py-2 rounded-full text-sm ${currentStep === 1 ? 'bg-blue-100 text-blue-700' : currentStep > 1 ? 'bg-green-50 text-green-700' : 'text-gray-400'}`}>
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center mr-2 text-xs font-medium ${currentStep === 1 ? 'bg-blue-600 text-white' : currentStep > 1 ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-500'}`}>
                            {currentStep > 1 ? '✓' : '1'}
                        </div>
                        <Sparkles className="w-3.5 h-3.5 mr-1" />
                        <span className="font-medium">AI 기획</span>
                    </div>
                    <div className="w-6 h-px bg-gray-300"></div>
                    {/* Step 2 */}
                    <div className={`flex items-center px-3 py-2 rounded-full text-sm ${currentStep === 2 ? 'bg-blue-100 text-blue-700' : 'text-gray-400'}`}>
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center mr-2 text-xs font-medium ${currentStep === 2 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}`}>
                            2
                        </div>
                        <Settings2 className="w-3.5 h-3.5 mr-1" />
                        <span className="font-medium">상세 설정</span>
                    </div>
                </div>

                <div className="w-24"></div>
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
