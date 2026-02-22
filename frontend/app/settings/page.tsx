'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { Menu, User, Settings, MessageSquare, FolderOpen, Bot, Clock, LogOut, Save } from 'lucide-react';
import { api } from '@/lib/api';

interface SettingsData {
    privacy: {
        mode: 'block' | 'mask';
        detectionItems: {
            ssn: boolean;          // 주민등록번호
            phone: boolean;        // 전화번호
            email: boolean;        // 이메일
            creditCard: boolean;   // 신용카드
            account: boolean;      // 계좌번호
            address: boolean;      // 주소
        };
    };
    account: {
        name: string;
        email: string;
        department: string;
    };
}

export default function SettingsPage() {
    const router = useRouter();
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    const [settings, setSettings] = useState<SettingsData>({
        privacy: {
            mode: 'block',
            detectionItems: {
                ssn: true,
                phone: true,
                email: true,
                creditCard: true,
                account: true,
                address: true,
            },
        },
        account: {
            name: '',
            email: '',
            department: '',
        },
    });

    const userName = typeof window !== 'undefined' ? localStorage.getItem('user_name') || '사용자' : '사용자';

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        setIsLoading(true);
        try {
            const data = await api.getSettings();
            setSettings(data);
        } catch (error) {
            console.error('Error fetching settings:', error);
            // API 실패 시 기본값
            setSettings({
                privacy: {
                    mode: 'block',
                    detectionItems: {
                        ssn: true,
                        phone: true,
                        email: true,
                        creditCard: true,
                        account: true,
                        address: true,
                    },
                },
                account: {
                    name: localStorage.getItem('user_name') || '',
                    email: localStorage.getItem('user_email') || '',
                    department: localStorage.getItem('department') || '',
                },
            });
        } finally {
            setIsLoading(false);
        }
    };

    const handleSaveSettings = async () => {
        setIsSaving(true);
        try {
            await api.updateSettings(settings);
            alert('설정이 저장되었습니다!');
        } catch (error) {
            console.error('Error saving settings:', error);
            alert('설정 저장에 실패했습니다.');
        } finally {
            setIsSaving(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_name');
        localStorage.removeItem('department');
        router.push('/auth/login');
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">설정을 불러오는 중...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
                {/* Sidebar Trigger */}
                <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
                    <SheetTrigger asChild>
                        <button className="p-2 hover:bg-gray-100 rounded-lg">
                            <Menu className="w-6 h-6 text-gray-700" />
                        </button>
                    </SheetTrigger>
                    <SheetContent side="left" className="w-[300px] sm:w-[400px]">
                        <SheetHeader>
                            <SheetTitle className="flex items-center gap-2">
                                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                                    <span className="text-white text-lg font-bold">ISOR</span>
                                </div>
                                <span>AI 플랫폼</span>
                            </SheetTitle>
                        </SheetHeader>
                        <nav className="mt-8 space-y-2">
                            <button
                                onClick={() => { router.push('/chat'); setSidebarOpen(false); }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <MessageSquare className="w-5 h-5 text-blue-600" />
                                <span className="font-medium">채팅</span>
                            </button>
                            <button
                                onClick={() => { router.push('/chat/history'); setSidebarOpen(false); }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <Clock className="w-5 h-5 text-blue-600" />
                                <span className="font-medium">채팅 기록</span>
                            </button>
                            <button
                                onClick={() => { router.push('/drive'); setSidebarOpen(false); }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <FolderOpen className="w-5 h-5 text-blue-600" />
                                <span className="font-medium">AI Drive</span>
                            </button>
                            <button
                                onClick={() => { router.push('/agents'); setSidebarOpen(false); }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <Bot className="w-5 h-5 text-blue-600" />
                                <span className="font-medium">Agent Hub</span>
                            </button>
                            <button
                                onClick={() => { router.push('/settings'); setSidebarOpen(false); }}
                                className="w-full flex items-center gap-3 px-4 py-3 text-left bg-blue-50 rounded-lg transition-colors"
                            >
                                <Settings className="w-5 h-5 text-blue-600" />
                                <span className="font-medium text-blue-600">설정</span>
                            </button>
                        </nav>
                    </SheetContent>
                </Sheet>

                {/* User Menu */}
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <button className="p-2 hover:bg-gray-100 rounded-lg">
                            <User className="w-6 h-6 text-gray-700" />
                        </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-56">
                        <DropdownMenuLabel>
                            <div className="flex flex-col">
                                <span className="font-medium">{userName}</span>
                                <span className="text-sm text-gray-500">{typeof window !== 'undefined' ? localStorage.getItem('department') || '' : ''}</span>
                            </div>
                        </DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => router.push('/settings')}>
                            <Settings className="w-4 h-4 mr-2" />
                            설정
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                            <LogOut className="w-4 h-4 mr-2" />
                            로그아웃
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </header>

            {/* Main Content */}
            <div className="flex-1 overflow-y-auto p-6">
                <div className="max-w-4xl mx-auto space-y-6">
                    {/* Page Header */}
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">설정</h1>
                        <p className="text-gray-600 mt-1">개인정보 보호 및 계정 설정을 관리합니다</p>
                    </div>

                    {/* Privacy Settings */}
                    <Card>
                        <CardHeader>
                            <CardTitle>개인정보 보호</CardTitle>
                            <CardDescription>
                                문서 업로드 및 대화 시 개인정보 처리 방식을 설정합니다
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            {/* Processing Mode */}
                            <div className="space-y-3">
                                <Label className="text-base font-semibold">개인정보 처리 방식</Label>
                                <RadioGroup
                                    value={settings.privacy.mode}
                                    onValueChange={(value: 'block' | 'mask') =>
                                        setSettings({
                                            ...settings,
                                            privacy: { ...settings.privacy, mode: value }
                                        })
                                    }
                                >
                                    <div className="flex items-center space-x-2">
                                        <RadioGroupItem value="block" id="block" />
                                        <Label htmlFor="block" className="font-normal cursor-pointer">
                                            자동 차단 (기본값) - 개인정보가 포함된 문서 업로드 차단
                                        </Label>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <RadioGroupItem value="mask" id="mask" />
                                        <Label htmlFor="mask" className="font-normal cursor-pointer">
                                            자동 마스킹 - 개인정보를 마스킹 처리 후 업로드 허용
                                        </Label>
                                    </div>
                                </RadioGroup>
                            </div>

                            {/* Detection Items */}
                            <div className="space-y-3">
                                <Label className="text-base font-semibold">감지 항목</Label>
                                <div className="space-y-3">
                                    <div className="flex items-center space-x-2">
                                        <Checkbox
                                            id="ssn"
                                            checked={settings.privacy.detectionItems.ssn}
                                            onCheckedChange={(checked) =>
                                                setSettings({
                                                    ...settings,
                                                    privacy: {
                                                        ...settings.privacy,
                                                        detectionItems: {
                                                            ...settings.privacy.detectionItems,
                                                            ssn: checked as boolean
                                                        }
                                                    }
                                                })
                                            }
                                        />
                                        <Label htmlFor="ssn" className="font-normal cursor-pointer">
                                            주민등록번호
                                        </Label>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <Checkbox
                                            id="phone"
                                            checked={settings.privacy.detectionItems.phone}
                                            onCheckedChange={(checked) =>
                                                setSettings({
                                                    ...settings,
                                                    privacy: {
                                                        ...settings.privacy,
                                                        detectionItems: {
                                                            ...settings.privacy.detectionItems,
                                                            phone: checked as boolean
                                                        }
                                                    }
                                                })
                                            }
                                        />
                                        <Label htmlFor="phone" className="font-normal cursor-pointer">
                                            전화번호
                                        </Label>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <Checkbox
                                            id="email"
                                            checked={settings.privacy.detectionItems.email}
                                            onCheckedChange={(checked) =>
                                                setSettings({
                                                    ...settings,
                                                    privacy: {
                                                        ...settings.privacy,
                                                        detectionItems: {
                                                            ...settings.privacy.detectionItems,
                                                            email: checked as boolean
                                                        }
                                                    }
                                                })
                                            }
                                        />
                                        <Label htmlFor="email" className="font-normal cursor-pointer">
                                            이메일 주소
                                        </Label>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <Checkbox
                                            id="creditCard"
                                            checked={settings.privacy.detectionItems.creditCard}
                                            onCheckedChange={(checked) =>
                                                setSettings({
                                                    ...settings,
                                                    privacy: {
                                                        ...settings.privacy,
                                                        detectionItems: {
                                                            ...settings.privacy.detectionItems,
                                                            creditCard: checked as boolean
                                                        }
                                                    }
                                                })
                                            }
                                        />
                                        <Label htmlFor="creditCard" className="font-normal cursor-pointer">
                                            신용카드 번호
                                        </Label>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <Checkbox
                                            id="account"
                                            checked={settings.privacy.detectionItems.account}
                                            onCheckedChange={(checked) =>
                                                setSettings({
                                                    ...settings,
                                                    privacy: {
                                                        ...settings.privacy,
                                                        detectionItems: {
                                                            ...settings.privacy.detectionItems,
                                                            account: checked as boolean
                                                        }
                                                    }
                                                })
                                            }
                                        />
                                        <Label htmlFor="account" className="font-normal cursor-pointer">
                                            계좌번호
                                        </Label>
                                    </div>
                                    <div className="flex items-center space-x-2">
                                        <Checkbox
                                            id="address"
                                            checked={settings.privacy.detectionItems.address}
                                            onCheckedChange={(checked) =>
                                                setSettings({
                                                    ...settings,
                                                    privacy: {
                                                        ...settings.privacy,
                                                        detectionItems: {
                                                            ...settings.privacy.detectionItems,
                                                            address: checked as boolean
                                                        }
                                                    }
                                                })
                                            }
                                        />
                                        <Label htmlFor="address" className="font-normal cursor-pointer">
                                            주소
                                        </Label>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Account Settings */}
                    <Card>
                        <CardHeader>
                            <CardTitle>계정 설정</CardTitle>
                            <CardDescription>
                                계정 정보를 확인하고 수정합니다
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label htmlFor="name">이름</Label>
                                <Input
                                    id="name"
                                    value={settings.account.name}
                                    onChange={(e) =>
                                        setSettings({
                                            ...settings,
                                            account: { ...settings.account, name: e.target.value }
                                        })
                                    }
                                    placeholder="이름을 입력하세요"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="email">이메일</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    value={settings.account.email}
                                    onChange={(e) =>
                                        setSettings({
                                            ...settings,
                                            account: { ...settings.account, email: e.target.value }
                                        })
                                    }
                                    placeholder="email@example.com"
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="department">부서</Label>
                                <Input
                                    id="department"
                                    value={settings.account.department}
                                    onChange={(e) =>
                                        setSettings({
                                            ...settings,
                                            account: { ...settings.account, department: e.target.value }
                                        })
                                    }
                                    placeholder="부서명을 입력하세요"
                                />
                            </div>
                        </CardContent>
                    </Card>

                    {/* Save Button */}
                    <div className="flex justify-end">
                        <Button
                            onClick={handleSaveSettings}
                            disabled={isSaving}
                            className="bg-blue-600 hover:bg-blue-700"
                        >
                            <Save className="w-4 h-4 mr-2" />
                            {isSaving ? '저장 중...' : '설정 저장'}
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
