'use client';

import { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check } from 'lucide-react';

interface CodeBlockProps {
    children: string;
    language?: string;
}

export function CodeBlock({ children, language }: CodeBlockProps) {
    const [copied, setCopied] = useState(false);

    const handleCopy = async () => {
        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(children);
            } else {
                const textArea = document.createElement('textarea');
                textArea.value = children;
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try {
                    document.execCommand('copy');
                } catch (err) {
                    throw new Error('Fallback copy failed');
                }
                document.body.removeChild(textArea);
            }
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (error) {
            console.error('Failed to copy code:', error);
        }
    };

    return (
        <div className="relative group my-2">
            {/* 언어 라벨 + 복사 버튼 헤더 */}
            <div className="flex items-center justify-between bg-gray-200 rounded-t-lg px-4 py-1.5 border border-b-0 border-gray-300">
                <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">
                    {language || 'code'}
                </span>
                <button
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-800 transition-colors px-2 py-1 rounded hover:bg-gray-300"
                >
                    {copied ? (
                        <>
                            <Check className="w-3.5 h-3.5 text-green-600" />
                            <span className="text-green-600">복사됨!</span>
                        </>
                    ) : (
                        <>
                            <Copy className="w-3.5 h-3.5" />
                            <span>복사</span>
                        </>
                    )}
                </button>
            </div>

            {/* 코드 블록 본문 (Syntax Highlighting 적용) */}
            <SyntaxHighlighter
                language={language || 'text'}
                style={oneLight}
                customStyle={{
                    margin: 0,
                    borderTopLeftRadius: 0,
                    borderTopRightRadius: 0,
                    borderBottomLeftRadius: '0.5rem',
                    borderBottomRightRadius: '0.5rem',
                    border: '1px solid #d1d5db',
                    borderTop: 'none',
                    fontSize: '0.85rem',
                    padding: '1rem',
                }}
                showLineNumbers={false}
            >
                {children}
            </SyntaxHighlighter>
        </div>
    );
}
