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
    const [draft, setDraft] = useState<AgentDraft>({
        name: '',
        description: '',
        goal: '',
        model: 'Gemini-1.5-Flash', // Default
        systemPrompt: '',
        ragEnabled: false,
        knowledgeBaseId: undefined,
        category: '업무보조', // Default
        visibility: 'private' // Default
    });

    const handleNext = () => {
        if (currentStep === 1) setCurrentStep(2);
    };

    const handleBack = () => {
        if (currentStep === 2) setCurrentStep(1);
        else router.back();
    };

    const handleComplete = async () => {
        try {
            await api.createAgentDraft({
                name: draft.name,
                description: draft.description,
                category: draft.category,
                visibility: draft.visibility,
                system_prompt: draft.systemPrompt
            });
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
