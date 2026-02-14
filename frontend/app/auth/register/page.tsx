'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';

export default function RegisterPage() {
    const router = useRouter();
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        name: '',
        department: '',
    });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        // 비밀번호 확인
        if (formData.password !== formData.confirmPassword) {
            setError('비밀번호가 일치하지 않습니다.');
            setIsLoading(false);
            return;
        }

        try {
            const data = await api.register({
                email: formData.email,
                password: formData.password,
                name: formData.name,
                department: formData.department,
            });

            // 토큰 저장 (api.register에서 이미 access_token 저장됨)
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('user_name', data.user_name);
            localStorage.setItem('department', data.department);

            // 채팅 페이지로 이동
            router.push('/chat');
        } catch (err) {
            setError(err instanceof Error ? err.message : '회원가입에 실패했습니다.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
            <Card className="w-full max-w-md">
                <CardHeader className="space-y-1 text-center">
                    <div className="flex justify-center mb-4">
                        <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center">
                            <span className="text-white text-2xl font-bold">ISOR</span>
                        </div>
                    </div>
                    <CardTitle className="text-2xl font-bold">회원가입</CardTitle>
                    <CardDescription>
                        새로운 계정을 만들어 시작하세요
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="email">이메일</Label>
                            <Input
                                id="email"
                                name="email"
                                type="email"
                                placeholder="example@company.com"
                                value={formData.email}
                                onChange={handleChange}
                                required
                                disabled={isLoading}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="name">이름</Label>
                            <Input
                                id="name"
                                name="name"
                                type="text"
                                placeholder="홍길동"
                                value={formData.name}
                                onChange={handleChange}
                                required
                                disabled={isLoading}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="department">부서</Label>
                            <Input
                                id="department"
                                name="department"
                                type="text"
                                placeholder="개발팀"
                                value={formData.department}
                                onChange={handleChange}
                                required
                                disabled={isLoading}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="password">비밀번호</Label>
                            <Input
                                id="password"
                                name="password"
                                type="password"
                                placeholder="••••••••"
                                value={formData.password}
                                onChange={handleChange}
                                required
                                disabled={isLoading}
                            />
                        </div>
                        <div className="space-y-2">
                            <Label htmlFor="confirmPassword">비밀번호 확인</Label>
                            <Input
                                id="confirmPassword"
                                name="confirmPassword"
                                type="password"
                                placeholder="••••••••"
                                value={formData.confirmPassword}
                                onChange={handleChange}
                                required
                                disabled={isLoading}
                            />
                        </div>
                        {error && (
                            <div className="text-sm text-red-600 bg-red-50 p-3 rounded-md">
                                {error}
                            </div>
                        )}
                        <Button
                            type="submit"
                            className="w-full bg-blue-600 hover:bg-blue-700"
                            disabled={isLoading}
                        >
                            {isLoading ? '가입 중...' : '회원가입'}
                        </Button>
                    </form>
                    <div className="mt-4 text-center text-sm">
                        <span className="text-gray-600">이미 계정이 있으신가요? </span>
                        <a
                            href="/auth/login"
                            className="text-blue-600 hover:text-blue-700 font-medium"
                        >
                            로그인
                        </a>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
