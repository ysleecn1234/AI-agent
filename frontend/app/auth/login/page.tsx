'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { api } from '@/lib/api';

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const data = await api.login({ email, password });

      localStorage.setItem('user_id', data.user_id);
      localStorage.setItem('user_name', data.user_name);
      localStorage.setItem('user_email', email);
      localStorage.setItem('department', data.department);

      // 로그인 전 접근하려던 페이지로 리다이렉트, 없으면 채팅으로
      const redirect = searchParams.get('redirect') || '/chat';
      router.push(redirect);
    } catch (err) {
      let errorMessage = '로그인에 실패했습니다.';
      if (err instanceof Error) {
        if (err.message.includes('401')) {
          errorMessage = '이메일 또는 비밀번호가 일치하지 않습니다.';
        } else if (err.message.includes('404')) {
          errorMessage = '존재하지 않는 계정입니다.';
        } else {
          errorMessage = err.message.replace('API Error:', '네트워크 오류:');
        }
      }
      setError(errorMessage);
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
          <CardTitle className="text-2xl font-bold">로그인</CardTitle>
          <CardDescription>
            AI 에이전트 플랫폼에 오신 것을 환영합니다
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">이메일</Label>
              <Input
                id="email"
                type="email"
                placeholder="example@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">비밀번호</Label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
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
              {isLoading ? '로그인 중...' : '로그인'}
            </Button>
          </form>
          <div className="mt-4 text-center text-sm">
            <span className="text-gray-600">계정이 없으신가요? </span>
            <a
              href="/auth/register"
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              회원가입
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
