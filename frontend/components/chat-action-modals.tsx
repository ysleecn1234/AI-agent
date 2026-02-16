'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FileText, MessageSquare, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';

interface SaveToDriveModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (data: {
        scope: 'single' | 'all';
        title: string;
        description: string;
        visibility: 'private' | 'team' | 'public';
    }) => void;
    content: string;
}

export function SaveToDriveModal({ isOpen, onClose, onSave, content }: SaveToDriveModalProps) {
    const [scope, setScope] = useState<'single' | 'all'>('single');
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [visibility, setVisibility] = useState<'private' | 'team' | 'public'>('team');
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
        setVisibility('private');
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
                            <span>미리보기</span>
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
        visibility: 'private' | 'team' | 'public';
    }) => void;
    content: string;
}

export function CreateAgentModal({ isOpen, onClose, onCreate, content }: CreateAgentModalProps) {
    const [scope, setScope] = useState<'single' | 'all'>('single');
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [category, setCategory] = useState('기타');
    const [visibility, setVisibility] = useState<'private' | 'team' | 'public'>('team');
    const [showPreview, setShowPreview] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);

    // Auto-generate agent info when modal opens
    useEffect(() => {
        if (isOpen && content) {
            generateAgentInfo();
        }
    }, [isOpen, content]);

    const generateAgentInfo = async () => {
        setIsGenerating(true);
        try {
            // Call backend API for LLM-based generation
            const metadata = await api.generateAgentMetadata(content);
            setName(metadata.name);
            setDescription(metadata.description);
            setCategory(metadata.category);
        } catch (error) {
            console.error('Failed to generate agent metadata:', error);
            // Fallback to simple generation
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
        } finally {
            setIsGenerating(false);
        }
    };

    const handleCreate = () => {
        onCreate({ scope, name, description, category, visibility });
        onClose();
        // Reset
        setScope('single');
        setName('');
        setDescription('');
        setCategory('기타');
        setVisibility('private');
        setShowPreview(false);
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Agent 생성</DialogTitle>
                    <DialogDescription>
                        Agent 정보를 입력하고 생성하세요
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 py-4">
                    {/* Scope Selection */}
                    <div>
                        <Label className="text-sm font-medium mb-2 block">학습 범위</Label>
                        <RadioGroup value={scope} onValueChange={(value) => setScope(value as 'single' | 'all')} className="grid grid-cols-2 gap-3">
                            <div className="flex items-center space-x-2 p-3 border rounded-lg cursor-pointer hover:bg-gray-50"
                                onClick={() => setScope('single')}>
                                <RadioGroupItem value="single" id="agent-single" />
                                <Label htmlFor="agent-single" className="cursor-pointer text-sm">
                                    이 답변 기반
                                </Label>
                            </div>
                            <div className="flex items-center space-x-2 p-3 border rounded-lg cursor-pointer hover:bg-gray-50"
                                onClick={() => setScope('all')}>
                                <RadioGroupItem value="all" id="agent-all" />
                                <Label htmlFor="agent-all" className="cursor-pointer text-sm">
                                    전체 대화 기반
                                </Label>
                            </div>
                        </RadioGroup>
                    </div>

                    {/* Name */}
                    <div>
                        <Label htmlFor="agent-name" className="text-sm font-medium mb-2 flex items-center gap-2">
                            Agent 이름
                            {isGenerating && <Loader2 className="w-3 h-3 animate-spin text-blue-600" />}
                        </Label>
                        <Input
                            id="agent-name"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="Agent 이름을 입력하세요"
                            disabled={isGenerating}
                        />
                    </div>

                    {/* Description */}
                    <div>
                        <Label htmlFor="agent-description" className="text-sm font-medium mb-2 block">
                            설명
                        </Label>
                        <Textarea
                            id="agent-description"
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="Agent 설명을 입력하세요"
                            className="min-h-[80px]"
                            disabled={isGenerating}
                        />
                    </div>

                    {/* Category */}
                    <div>
                        <Label htmlFor="agent-category" className="text-sm font-medium mb-2 block">
                            카테고리
                        </Label>
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

                    {/* Visibility */}
                    <div>
                        <Label htmlFor="agent-visibility" className="text-sm font-medium mb-2 block">
                            공개 범위
                        </Label>
                        <Select value={visibility} onValueChange={(value: any) => setVisibility(value)}>
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="private">🔒 나만 사용</SelectItem>
                                <SelectItem value="team">👥 팀 공유</SelectItem>
                                <SelectItem value="public">🌐 전체 공개</SelectItem>
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
                            <span>학습 데이터 미리보기</span>
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
                        onClick={handleCreate} 
                        className="bg-blue-600 hover:bg-blue-700"
                        disabled={!name.trim() || !description.trim() || isGenerating}
                    >
                        생성
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
