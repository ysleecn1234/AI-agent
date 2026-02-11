'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { FileText, MessageSquare } from 'lucide-react';

interface SaveToDriveModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (scope: 'single' | 'all') => void;
}

export function SaveToDriveModal({ isOpen, onClose, onSave }: SaveToDriveModalProps) {
    const [scope, setScope] = useState<'single' | 'all'>('single');

    const handleSave = () => {
        onSave(scope);
        onClose();
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>드라이브에 저장</DialogTitle>
                    <DialogDescription>
                        저장할 범위를 선택하세요
                    </DialogDescription>
                </DialogHeader>

                <RadioGroup value={scope} onValueChange={(value) => setScope(value as 'single' | 'all')} className="space-y-4 py-4">
                    <div className="flex items-start space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                        onClick={() => setScope('single')}>
                        <RadioGroupItem value="single" id="single" />
                        <div className="flex-1">
                            <Label htmlFor="single" className="cursor-pointer flex items-center gap-2 font-medium">
                                <FileText className="w-4 h-4 text-blue-600" />
                                이 답변만 저장
                            </Label>
                            <p className="text-sm text-gray-500 mt-1">
                                현재 선택한 답변만 드라이브에 저장합니다
                            </p>
                        </div>
                    </div>

                    <div className="flex items-start space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                        onClick={() => setScope('all')}>
                        <RadioGroupItem value="all" id="all" />
                        <div className="flex-1">
                            <Label htmlFor="all" className="cursor-pointer flex items-center gap-2 font-medium">
                                <MessageSquare className="w-4 h-4 text-blue-600" />
                                전체 대화 저장
                            </Label>
                            <p className="text-sm text-gray-500 mt-1">
                                지금까지의 모든 대화 내용을 드라이브에 저장합니다
                            </p>
                        </div>
                    </div>
                </RadioGroup>

                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>
                        취소
                    </Button>
                    <Button onClick={handleSave} className="bg-blue-600 hover:bg-blue-700">
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
    onCreate: (scope: 'single' | 'all') => void;
}

export function CreateAgentModal({ isOpen, onClose, onCreate }: CreateAgentModalProps) {
    const [scope, setScope] = useState<'single' | 'all'>('single');

    const handleCreate = () => {
        onCreate(scope);
        onClose();
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>에이전트 생성</DialogTitle>
                    <DialogDescription>
                        에이전트 생성에 사용할 대화 범위를 선택하세요
                    </DialogDescription>
                </DialogHeader>

                <RadioGroup value={scope} onValueChange={(value) => setScope(value as 'single' | 'all')} className="space-y-4 py-4">
                    <div className="flex items-start space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                        onClick={() => setScope('single')}>
                        <RadioGroupItem value="single" id="agent-single" />
                        <div className="flex-1">
                            <Label htmlFor="agent-single" className="cursor-pointer flex items-center gap-2 font-medium">
                                <FileText className="w-4 h-4 text-blue-600" />
                                이 답변 기반
                            </Label>
                            <p className="text-sm text-gray-500 mt-1">
                                현재 답변을 기반으로 에이전트를 생성합니다
                            </p>
                        </div>
                    </div>

                    <div className="flex items-start space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-colors"
                        onClick={() => setScope('all')}>
                        <RadioGroupItem value="all" id="agent-all" />
                        <div className="flex-1">
                            <Label htmlFor="agent-all" className="cursor-pointer flex items-center gap-2 font-medium">
                                <MessageSquare className="w-4 h-4 text-blue-600" />
                                전체 대화 기반
                            </Label>
                            <p className="text-sm text-gray-500 mt-1">
                                전체 대화 내용을 분석하여 에이전트를 생성합니다
                            </p>
                        </div>
                    </div>
                </RadioGroup>

                <DialogFooter>
                    <Button variant="outline" onClick={onClose}>
                        취소
                    </Button>
                    <Button onClick={handleCreate} className="bg-blue-600 hover:bg-blue-700">
                        생성
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
