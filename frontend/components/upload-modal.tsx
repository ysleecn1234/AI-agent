'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Progress } from '@/components/ui/progress';
import { Upload, X, FileText } from 'lucide-react';

interface UploadModalProps {
    isOpen: boolean;
    onClose: () => void;
    onUploadSuccess: () => void;
}

const ALLOWED_FILE_TYPES = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/plain',
    'text/markdown',
    'text/csv',
];

const ALLOWED_EXTENSIONS = ['pdf', 'docx', 'pptx', 'xlsx', 'txt', 'md', 'csv'];
const MAX_FILE_SIZE = 1024 * 1024 * 1024; // 1GB

export default function UploadModal({ isOpen, onClose, onUploadSuccess }: UploadModalProps) {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [visibility, setVisibility] = useState<'private' | 'team' | 'public'>('private');
    const [uploadProgress, setUploadProgress] = useState(0);
    const [isUploading, setIsUploading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isDragging, setIsDragging] = useState(false);

    const validateFile = (file: File): string | null => {
        // Check file size
        if (file.size > MAX_FILE_SIZE) {
            return '파일 크기는 1GB를 초과할 수 없습니다.';
        }

        // Check file extension
        const extension = file.name.split('.').pop()?.toLowerCase();
        if (!extension || !ALLOWED_EXTENSIONS.includes(extension)) {
            return `지원되지 않는 파일 형식입니다. 지원 형식: ${ALLOWED_EXTENSIONS.join(', ')}`;
        }

        return null;
    };

    const handleFileSelect = (file: File) => {
        const validationError = validateFile(file);
        if (validationError) {
            setError(validationError);
            setSelectedFile(null);
            return;
        }

        setError(null);
        setSelectedFile(file);
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    };

    const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            handleFileSelect(files[0]);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        setIsUploading(true);
        setUploadProgress(0);

        try {
            const formData = new FormData();
            formData.append('file', selectedFile);
            formData.append('visibility', visibility);

            const token = localStorage.getItem('access_token');

            // Using XMLHttpRequest for progress tracking
            const xhr = new XMLHttpRequest();

            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const progress = Math.round((e.loaded / e.total) * 100);
                    setUploadProgress(progress);
                }
            });

            xhr.addEventListener('load', () => {
                if (xhr.status === 200) {
                    onUploadSuccess();
                    handleClose();
                } else {
                    setError('파일 업로드에 실패했습니다.');
                }
                setIsUploading(false);
            });

            xhr.addEventListener('error', () => {
                setError('파일 업로드 중 오류가 발생했습니다.');
                setIsUploading(false);
            });

            xhr.open('POST', 'http://localhost:8000/drive/upload');
            xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            xhr.send(formData);
        } catch (error) {
            console.error('Upload error:', error);
            setError('파일 업로드 중 오류가 발생했습니다.');
            setIsUploading(false);
        }
    };

    const handleClose = () => {
        if (!isUploading) {
            setSelectedFile(null);
            setVisibility('private');
            setUploadProgress(0);
            setError(null);
            setIsDragging(false);
            onClose();
        }
    };

    const formatFileSize = (bytes: number): string => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>파일 업로드</DialogTitle>
                    <DialogDescription>
                        문서를 업로드하여 AI Drive에 저장하세요. (최대 1GB)
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4">
                    {/* Drag and Drop Area */}
                    <div
                        onDragOver={handleDragOver}
                        onDragLeave={handleDragLeave}
                        onDrop={handleDrop}
                        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${isDragging
                                ? 'border-blue-600 bg-blue-50'
                                : 'border-gray-300 hover:border-gray-400'
                            }`}
                    >
                        {selectedFile ? (
                            <div className="space-y-2">
                                <div className="flex items-center justify-center gap-2">
                                    <FileText className="w-8 h-8 text-blue-600" />
                                    <div className="text-left">
                                        <p className="font-medium text-gray-900">{selectedFile.name}</p>
                                        <p className="text-sm text-gray-500">{formatFileSize(selectedFile.size)}</p>
                                    </div>
                                    <button
                                        onClick={() => setSelectedFile(null)}
                                        className="ml-auto p-1 hover:bg-gray-100 rounded"
                                        disabled={isUploading}
                                    >
                                        <X className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <>
                                <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                                <p className="text-gray-700 mb-2">
                                    파일을 드래그하여 놓거나 클릭하여 선택하세요
                                </p>
                                <p className="text-sm text-gray-500 mb-4">
                                    지원 형식: PDF, DOCX, PPTX, XLSX, TXT, MD, CSV
                                </p>
                                <input
                                    type="file"
                                    id="file-input"
                                    className="hidden"
                                    onChange={handleFileInputChange}
                                    accept={ALLOWED_EXTENSIONS.map(ext => `.${ext}`).join(',')}
                                    disabled={isUploading}
                                />
                                <Button
                                    onClick={() => document.getElementById('file-input')?.click()}
                                    variant="outline"
                                    disabled={isUploading}
                                >
                                    📂 파일 선택
                                </Button>
                            </>
                        )}
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                            <p className="text-sm text-red-600">{error}</p>
                        </div>
                    )}

                    {/* Visibility Selector */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-700">공개 범위</label>
                        <Select value={visibility} onValueChange={(value: any) => setVisibility(value)} disabled={isUploading}>
                            <SelectTrigger>
                                <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="private">🔒 나만 보기</SelectItem>
                                <SelectItem value="team">👥 팀 공유</SelectItem>
                                <SelectItem value="public">🌐 전체 공개</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Upload Progress */}
                    {isUploading && (
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span className="text-gray-700">업로드 중...</span>
                                <span className="text-gray-700">{uploadProgress}%</span>
                            </div>
                            <Progress value={uploadProgress} />
                        </div>
                    )}
                </div>

                <DialogFooter>
                    <Button variant="outline" onClick={handleClose} disabled={isUploading}>
                        취소
                    </Button>
                    <Button
                        onClick={handleUpload}
                        disabled={!selectedFile || isUploading}
                        className="bg-blue-600 hover:bg-blue-700"
                    >
                        {isUploading ? '업로드 중...' : '업로드'}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
