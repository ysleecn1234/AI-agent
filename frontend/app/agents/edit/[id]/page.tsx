'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Sparkles, Settings2 } from 'lucide-react';
import { AgentDraft, Step1Chat } from '@/components/create-agent-steps/step1-chat';
import { Step2Config } from '@/components/create-agent-steps/step2-config';
import { api } from '@/lib/api';

export default function EditAgentPage() {
    const router = useRouter();
    const params = useParams();
    const agentId = params.id as string;

    const [isLoading, setIsLoading] = useState(true);
    const [currentStep, setCurrentStep] = useState<1 | 2>(2);
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

    useEffect(() => {
        const fetchAgent = async () => {
            try {
                const data = await api.getAgent(agentId);
                setDraft({
                    name: data.name || '',
                    description: data.description || '',
                    goal: '',
                    model: data.model_type || 'AUTO',
                    systemPrompt: data.system_prompt || '',
                    ragEnabled: data.use_rag || false,
                    category: data.category || '기타',
                    visibility: typeof data.visibility === 'string' ? data.visibility.toLowerCase() as any : 'team',
                    inputExample: (data as any).input_example || '',
                    outputExample: (data as any).output_example || '',
                    messages: []
                });
            } catch (err) {
                console.error('Failed to load agent', err);
                alert('에이전트 정보를 불러올 수 없습니다.');
                router.push('/agents');
            } finally {
                setIsLoading(false);
            }
        };

        if (agentId) {
            fetchAgent();
        }
    }, [agentId, router]);

    const handleNext = async () => {
        if (currentStep === 1) {
            setCurrentStep(2);
        }
    };

    const handleBack = () => {
        if (currentStep === 2) setCurrentStep(1);
        else router.back();
    };

    const handleComplete = async () => {
        try {
            await api.updateAgent(agentId, {
                name: draft.name,
                description: draft.description,
                category: draft.category,
                system_prompt: draft.systemPrompt,
                model_type: draft.model || 'AUTO',
                use_rag: draft.ragEnabled,
                visibility: (draft.visibility || 'team').toUpperCase(),
                input_example: draft.inputExample,
                output_example: draft.outputExample,
            });

            alert('에이전트가 성공적으로 수정되었습니다!');
            router.push('/agents');
        } catch (error) {
            console.error('에이전트 수정 실패:', error);
            alert('에이전트 수정에 실패했습니다. 다시 시도해주세요.');
        }
    };

    if (isLoading) {
        return <div className="flex items-center justify-center h-screen">로딩중...</div>;
    }

    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => router.back()}>
                        <ArrowLeft className="w-5 h-5 text-gray-600" />
                    </Button>
                    <h1 className="text-xl font-bold text-gray-900">에이전트 수정</h1>
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
