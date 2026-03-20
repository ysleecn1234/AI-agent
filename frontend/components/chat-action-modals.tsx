'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FileText, MessageSquare, ChevronDown, ChevronUp, Loader2, Sparkles } from 'lucide-react';
import { api } from '@/lib/api';

interface SaveToDriveModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (data: {
        scope: 'single' | 'all';
        title: string;
        description: string;
        visibility: 'team' | 'public';
    }) => void;
    content: string;
}

export function SaveToDriveModal({ isOpen, onClose, onSave, content }: SaveToDriveModalProps) {
    const [scope, setScope] = useState<'single' | 'all'>('single');
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [visibility, setVisibility] = useState<'team' | 'public'>('team');
    const [showPreview, setShowPreview] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);

    // Auto-generate title and description when modal opens
    useEffect(() => {
        if (isOpen && content) {
            generateTitleAndDescription();
        }
    }, [isOpen, content]);

    const generateTitleAndDescription = async () => {
        setIsGenerating(true);
        try {
            // Call backend API for LLM-based generation
            const metadata = await api.generateDocumentMetadata(content);
            setTitle(metadata.title);
            setDescription(metadata.description);
        } catch (error) {
            console.error('Failed to generate metadata:', error);
            // Fallback to simple generation
            const lines = content.split('\n').filter(l => l.trim());
            const firstLine = lines[0] || '대화 내용';
            const generatedTitle = firstLine.length > 50
                ? firstLine.substring(0, 50) + '...'
                : firstLine;

            setTitle(generatedTitle || `채팅 문서 - ${new Date().toLocaleDateString()}`);
            setDescription(`${lines.length}개의 메시지를 포함한 대화 내용입니다.`);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSave = () => {
        onSave({ scope, title, description, visibility });
        onClose();
        // Reset
        setScope('single');
        setTitle('');
        setDescription('');
        setVisibility('team');
        setShowPreview(false);
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>드라이브에 저장</DialogTitle>
                    <DialogDescription>
                        문서 정보를 입력하고 저장하세요
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    {/* Scope Selection */}
                    <div>
                        <Label className="text-sm font-medium mb-2 block">저장 범위</Label>
                        <RadioGroup value={scope} onValueChange={(value) => setScope(value as 'single' | 'all')} className="grid grid-cols-2 gap-3">
                            <div className="flex items-center space-x-2 p-3 border rounded-lg cursor-pointer hover:bg-gray-50"
                                onClick={() => setScope('single')}>
                                <RadioGroupItem value="single" id="single" />
                                <Label htmlFor="single" className="cursor-pointer text-sm">
                                    이 답변만
                                </Label>
                            </div>
                            <div className="flex items-center space-x-2 p-3 border rounded-lg cursor-pointer hover:bg-gray-50"
                                onClick={() => setScope('all')}>
                                <RadioGroupItem value="all" id="all" />
                                <Label htmlFor="all" className="cursor-pointer text-sm">
                                    전체 대화
                                </Label>
                            </div>
                        </RadioGroup>
                    </div>

                    {/* Title */}
                    <div>
                        <Label htmlFor="title" className="text-sm font-medium mb-2 flex items-center gap-2">
                            제목
                            {isGenerating && <Loader2 className="w-3 h-3 animate-spin text-blue-600" />}
                        </Label>
                        <Input
                            id="title"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="문서 제목을 입력하세요"
                            disabled={isGenerating}
                        />
                    </div>

                    {/* Description */}
                    <div>
                        <Label htmlFor="description" className="text-sm font-medium mb-2 block">
                            설명
                        </Label>
                        <Textarea
                            id="description"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="문서 설명을 입력하세요 (선택)"
                            className="min-h-[80px]"
                            disabled={isGenerating}
                        />
                    </div>

                    {/* Visibility */}
                    <div>
                        <Label htmlFor="visibility" className="text-sm font-medium mb-2 block">
                            공개 범위
                        </Label>
                        <Select value={visibility} onValueChange={(value: any) => setVisibility(value)}>
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="team">👥 팀 공유</SelectItem>
                                <SelectItem value="public">🌐 전사 공개</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Preview Toggle */}
                    <div>
                        <Button
                            variant="outline"
                            onClick={() => setShowPreview(!showPreview)}
                            className="w-full justify-between"
                            type="button"
                        >
                            <span>문서 미리보기</span>
                            {showPreview ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </Button>

                        {showPreview && (
                            <div className="mt-3 p-4 bg-gray-50 border rounded-lg max-h-[200px] overflow-y-auto">
                                <pre className="text-sm whitespace-pre-wrap text-gray-700">
                                    {content}
                                </pre>
                            </div>
                        )}
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>
                        취소
                    </Button>
                    <Button
                        onClick={handleSave}
                        className="bg-blue-600 hover:bg-blue-700"
                        disabled={!title.trim() || isGenerating}
                    >
                        저장
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

interface CreateAgentModalProps {
    isOpen: boolean;
    onClose: () => void;
    onCreate: (data: {
        scope: 'single' | 'all';
        name: string;
        description: string;
        category: string;
        visibility: 'team' | 'public';
        use_rag: boolean;
        input_example: string;
        output_example: string;
        system_prompt: string;
        model_type: string;
    }) => void;
    content: string;
    fullMessages?: { role: string; content: string }[];
}

export function CreateAgentModal({ isOpen, onClose, onCreate, content, fullMessages }: CreateAgentModalProps) {
    const [step, setStep] = useState(1);
    const [scope, setScope] = useState<'single' | 'all'>('single');
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [category, setCategory] = useState('기타');
    const [visibility, setVisibility] = useState<'team' | 'public'>('team');
    const [useRag, setUseRag] = useState(false);
    const [inputExample, setInputExample] = useState('');
    const [outputExample, setOutputExample] = useState('');
    const [systemPrompt, setSystemPrompt] = useState('');
    const [modelType, setModelType] = useState('AUTO');
    const [isGenerating, setIsGenerating] = useState(false);

    // Auto-generate agent info when modal opens or scope changes
    useEffect(() => {
        if (isOpen && content) {
            generateAgentInfo();
        }
    }, [isOpen, content, scope]);

    const generateAgentInfo = async () => {
        setIsGenerating(true);
        try {
            const selected_messages = scope === 'all' && fullMessages && fullMessages.length > 0
                ? fullMessages
                : [{ role: 'user', content }];

            const result = await api.createAgentDraft({
                selected_messages,
            });
            const filled = result.filled;
            if (filled) {
                setName(filled.name || '');
                setDescription(filled.description || '');
                setCategory(filled.category || '기타');
                setInputExample(filled.input_example || '');
                setOutputExample(filled.output_example || '');
                setSystemPrompt(filled.system_prompt || '');
            }
        } catch (error) {
            console.error('Failed to generate agent metadata:', error);
            const contentLower = content.toLowerCase();
            let detectedCategory = '기타';
            if (contentLower.includes('마케팅') || contentLower.includes('광고')) {
                detectedCategory = '마케팅';
            } else if (contentLower.includes('코드') || contentLower.includes('프로그래밍')) {
                detectedCategory = '개발';
            } else if (contentLower.includes('데이터') || contentLower.includes('분석')) {
                detectedCategory = '생산성';
            }
            setName(`AI 어시스턴트 - ${new Date().toLocaleDateString()}`);
            setDescription('대화 내용을 기반으로 생성된 맞춤형 Agent입니다.');
            setCategory(detectedCategory);
            setSystemPrompt('사용자의 요청에 정확하고 유용하게 답변하세요.');
        } finally {
            setIsGenerating(false);
        }
    };

    const handleCreate = () => {
        onCreate({
            scope, name, description, category, visibility,
            use_rag: useRag,
            input_example: inputExample,
            output_example: outputExample,
            system_prompt: systemPrompt,
            model_type: modelType,
        });
        handleClose();
    };

    const handleClose = () => {
        onClose();
        setStep(1);
        setScope('single');
        setName('');
        setDescription('');
        setCategory('기타');
        setVisibility('team');
        setUseRag(false);
        setInputExample('');
        setOutputExample('');
        setSystemPrompt('');
        setModelType('AUTO');
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="sm:max-w-[640px] max-h-[90vh] overflow-y-auto">
                {/* Header with Step indicator */}
                <DialogHeader>
                    <div className="flex items-center justify-between">
                        <DialogTitle className="flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-blue-600" />
                            에이전트 생성
                        </DialogTitle>
                        <div className="flex items-center gap-1 text-sm pr-8">
                            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${step === 1 ? 'bg-blue-600 text-white' : 'bg-green-500 text-white'}`}>
                                {step === 1 ? '1' : '✓'}
                            </span>
                            <span className="text-gray-300">—</span>
                            <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium ${step === 2 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}`}>
                                2
                            </span>
                        </div>
                    </div>
                    <DialogDescription>
                        {step === 1
                            ? '에이전트의 핵심 정보와 프롬프트를 설정하세요.'
                            : '에이전트의 분류와 세부 설정을 완료하세요.'}
                    </DialogDescription>
                </DialogHeader>

                {step === 1 ? (
                    /* ===== Step 1: 학습 범위 + 이름 + 입력/출력 예시 + 시스템 프롬프트 ===== */
                    <div className="space-y-5 py-4">
                        <p className="text-sm font-semibold text-blue-600">Step 1 — 기본 정보 및 프롬프트</p>

                        {/* 학습 범위 */}
                        <div>
                            <Label className="text-sm font-medium mb-2 block">학습 범위</Label>
                            <RadioGroup value={scope} onValueChange={(value) => setScope(value as 'single' | 'all')} className="grid grid-cols-2 gap-3">
                                <div className={`flex items-center space-x-2 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 ${scope === 'single' ? 'border-blue-500 bg-blue-50' : ''}`}
                                    onClick={() => setScope('single')}>
                                    <RadioGroupItem value="single" id="agent-single" />
                                    <Label htmlFor="agent-single" className="cursor-pointer text-sm">
                                        이 답변 기반
                                    </Label>
                                </div>
                                <div className={`flex items-center space-x-2 p-3 border rounded-lg cursor-pointer hover:bg-gray-50 ${scope === 'all' ? 'border-blue-500 bg-blue-50' : ''}`}
                                    onClick={() => setScope('all')}>
                                    <RadioGroupItem value="all" id="agent-all" />
                                    <Label htmlFor="agent-all" className="cursor-pointer text-sm">
                                        전체 대화 기반
                                    </Label>
                                </div>
                            </RadioGroup>
                        </div>

                        {/* 에이전트 이름 */}
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <Label htmlFor="agent-name" className="text-sm font-medium flex items-center gap-2">
                                    에이전트 이름 <span className="text-red-500">*</span>
                                    {isGenerating && <Loader2 className="w-3 h-3 animate-spin text-blue-600" />}
                                </Label>
                                <span className="text-xs text-gray-400">{name.length}/100</span>
                            </div>
                            <Input
                                id="agent-name"
                                value={name}
                                onChange={(e) => setName(e.target.value.slice(0, 100))}
                                placeholder="에이전트 이름을 입력하세요"
                                disabled={isGenerating}
                            />
                        </div>

                        {/* 입력 예시 */}
                        <div>
                            <Label htmlFor="input-example" className="text-sm font-medium mb-2 flex items-center gap-1">
                                입력 예시 <span className="text-red-500">*</span>
                            </Label>
                            <Textarea
                                id="input-example"
                                value={inputExample}
                                onChange={(e) => setInputExample(e.target.value)}
                                placeholder="에이전트에 입력할 예시를 작성하세요"
                                className="min-h-[80px]"
                                disabled={isGenerating}
                            />
                        </div>

                        {/* 출력 예시 */}
                        <div>
                            <Label htmlFor="output-example" className="text-sm font-medium mb-2 flex items-center gap-1">
                                출력 예시 <span className="text-red-500">*</span>
                            </Label>
                            <Textarea
                                id="output-example"
                                value={outputExample}
                                onChange={(e) => setOutputExample(e.target.value)}
                                placeholder="에이전트가 출력할 예시를 작성하세요"
                                className="min-h-[80px]"
                                disabled={isGenerating}
                            />
                        </div>

                        {/* 시스템 프롬프트 */}
                        <div>
                            <Label htmlFor="system-prompt" className="text-sm font-medium mb-2 flex items-center gap-1">
                                시스템 프롬프트
                            </Label>
                            <p className="text-xs text-gray-500 mb-2">에이전트의 역할과 행동 규칙을 정의합니다. 자동 생성된 내용을 수정할 수 있습니다.</p>
                            <Textarea
                                id="system-prompt"
                                value={systemPrompt}
                                onChange={(e) => setSystemPrompt(e.target.value)}
                                placeholder="예: 당신은 숙련된 DBA입니다. 사용자의 자연어 질문을 SQL 쿼리로 변환하세요."
                                className="min-h-[100px] font-mono text-sm"
                                disabled={isGenerating}
                            />
                        </div>
                    </div>
                ) : (
                    /* ===== Step 2: 카테고리 + 설명 + 모델 선택 + RAG + 공개 범위 ===== */
                    <div className="space-y-5 py-4">
                        <p className="text-sm font-semibold text-blue-600">Step 2 — 분류 및 설정</p>

                        {/* 카테고리 */}
                        <div>
                            <Label className="text-sm font-medium flex items-center gap-1 mb-1">
                                카테고리 <span className="text-red-500">*</span>
                            </Label>
                            <p className="text-xs text-gray-500 mb-2">에이전트가 분류되는 카테고리를 선택해주세요</p>
                            <Select value={category} onValueChange={setCategory}>
                                <SelectTrigger>
                                    <SelectValue />
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

                        {/* 에이전트 설명 */}
                        <div>
                            <div className="flex items-center justify-between mb-2">
                                <Label htmlFor="agent-description" className="text-sm font-medium flex items-center gap-1">
                                    에이전트 설명 <span className="text-red-500">*</span>
                                </Label>
                                <span className="text-xs text-gray-400">{description.length}/200</span>
                            </div>
                            <Textarea
                                id="agent-description"
                                value={description}
                                onChange={(e) => setDescription(e.target.value.slice(0, 200))}
                                placeholder="에이전트 설명을 입력하세요"
                                className="min-h-[60px]"
                                disabled={isGenerating}
                            />
                        </div>

                        {/* 모델 선택 */}
                        <div>
                            <Label className="text-sm font-medium flex items-center gap-1 mb-1">
                                사용 모델
                            </Label>
                            <p className="text-xs text-gray-500 mb-2">Auto를 선택하면 질문에 맞는 최적 모델이 자동 선택됩니다.</p>
                            <Select value={modelType} onValueChange={setModelType}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="AUTO">⚡ Auto (자동 선택)</SelectItem>
                                    <SelectItem value="gemini/gemini-2.5-flash-lite">Gemini 2.5 Flash Lite</SelectItem>
                                    <SelectItem value="gemini/gemini-2.5-flash">Gemini 2.5 Flash</SelectItem>
                                    <SelectItem value="gemini/gemini-3-flash-preview">Gemini 3 Flash</SelectItem>
                                    <SelectItem value="gemini/gemini-3.1-pro-preview">Gemini 3.1 Pro</SelectItem>
                                    <SelectItem value="gpt-5-nano">GPT-5 Nano</SelectItem>
                                    <SelectItem value="gpt-5-mini">GPT-5 Mini</SelectItem>
                                    <SelectItem value="gpt-5.2">GPT-5.2</SelectItem>
                                    <SelectItem value="gpt-5.2-pro">GPT-5.2 Pro</SelectItem>
                                    <SelectItem value="claude-haiku-4.5">Claude Haiku 4.5</SelectItem>
                                    <SelectItem value="claude-sonnet-4-6">Claude Sonnet 4.6</SelectItem>
                                    <SelectItem value="claude-opus-4-6">Claude Opus 4.6</SelectItem>
                                    <SelectItem value="perplexity/sonar">Perplexity Sonar</SelectItem>
                                    <SelectItem value="perplexity/sonar-pro">Perplexity Sonar Pro</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        {/* 문서 참조 (RAG) */}
                        <div>
                            <Label className="text-sm font-bold mb-1 block">에이전트가 내부 문서를 참조하게 할까요?</Label>
                            <p className="text-xs text-gray-500 mb-3">활성화 됐을 경우, AI 드라이브에 공유된 문서를 참조하여 답변합니다.</p>
                            <div className="flex items-center gap-3">
                                <Switch
                                    checked={useRag}
                                    onCheckedChange={setUseRag}
                                />
                                <span className="text-sm text-gray-700">{useRag ? '참조합니다' : '참조하지 않습니다'}</span>
                            </div>
                        </div>

                        {/* 공개 범위 */}
                        <div>
                            <Label className="text-sm font-bold mb-1 block">에이전트의 공개 범위를 선택해주세요.</Label>
                            <p className="text-xs text-gray-500 mb-3">저장 후에도 언제든지 변경하실 수 있습니다.</p>
                            <RadioGroup value={visibility} onValueChange={(value) => setVisibility(value as 'team' | 'public')} className="space-y-3">
                                <div className={`p-4 border rounded-lg cursor-pointer hover:bg-gray-50 ${visibility === 'public' ? 'border-blue-500 bg-blue-50' : ''}`}
                                    onClick={() => setVisibility('public')}>
                                    <div className="flex items-center gap-2">
                                        <RadioGroupItem value="public" id="vis-public" />
                                        <Label htmlFor="vis-public" className="cursor-pointer font-medium text-sm">전체 공개</Label>
                                    </div>
                                    <p className="text-xs text-gray-500 ml-6 mt-1">에이전트 허브에 공개로 등록되며, 조직 내 팀원들이 함께 사용할 수 있어요.</p>
                                </div>
                                <div className={`p-4 border rounded-lg cursor-pointer hover:bg-gray-50 ${visibility === 'team' ? 'border-blue-500 bg-blue-50' : ''}`}
                                    onClick={() => setVisibility('team')}>
                                    <div className="flex items-center gap-2">
                                        <RadioGroupItem value="team" id="vis-team" />
                                        <Label htmlFor="vis-team" className="cursor-pointer font-medium text-sm">나만 보기</Label>
                                    </div>
                                    <p className="text-xs text-gray-500 ml-6 mt-1">에이전트 허브에 비공개로 등록되며, 본인만 활용할 수 있어요.</p>
                                </div>
                            </RadioGroup>
                        </div>
                    </div>
                )}

                {/* Footer */}
                <DialogFooter className="flex justify-between">
                    {step === 1 ? (
                        <>
                            <Button variant="outline" onClick={handleClose}>
                                취소
                            </Button>
                            <Button
                                onClick={() => setStep(2)}
                                className="bg-white border border-blue-600 text-blue-600 hover:bg-blue-50 min-w-[100px]"
                                disabled={!name.trim() || isGenerating}
                            >
                                다음
                            </Button>
                        </>
                    ) : (
                        <>
                            <Button variant="outline" onClick={handleClose}>
                                취소
                            </Button>
                            <div className="flex gap-2">
                                <Button
                                    variant="outline"
                                    onClick={() => setStep(1)}
                                >
                                    이전
                                </Button>
                                <Button
                                    onClick={handleCreate}
                                    className="bg-blue-600 hover:bg-blue-700 min-w-[100px]"
                                    disabled={!name.trim() || !description.trim() || isGenerating}
                                >
                                    저장하기
                                </Button>
                            </div>
                        </>
                    )}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
