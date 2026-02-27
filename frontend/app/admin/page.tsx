'use client';

import { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { AppSidebar } from '@/components/app-sidebar';
import { api } from '@/lib/api';
import { Menu, User, Settings, LogOut, TrendingUp, TrendingDown, Wallet, Coins, Zap, ArrowUpRight, ArrowDownRight } from 'lucide-react';

import {
    PieChart, Pie, Cell, ResponsiveContainer, Tooltip as RechartsTooltip,
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend
} from 'recharts';

// 차트 색상 — 사용자 관점 4개 카테고리
const CATEGORY_COLORS: Record<string, string> = {
    ai_chat: '#3B82F6',        // blue-500
    doc_qa: '#8B5CF6',         // purple-500
    doc_processing: '#10B981', // emerald-500
    agent: '#F59E0B',          // amber-500
    other: '#6B7280',          // gray-500
};

const CATEGORY_LABELS: Record<string, string> = {
    ai_chat: 'AI 채팅',
    doc_qa: '문서 Q&A',
    doc_processing: '문서 처리',
    agent: 'AI 에이전트',
    other: '기타',
};

function formatKRW(value: number): string {
    if (value >= 1_000_000) return `₩${(value / 1_000_000).toFixed(1)}M`;
    if (value >= 1_000) return `₩${(value / 1_000).toFixed(0)}K`;
    return `₩${Math.round(value).toLocaleString()}`;
}

function formatNumber(value: number): string {
    if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
    if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`;
    return value.toLocaleString();
}

export default function AdminPage() {
    const router = useRouter();
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [selectedMonth, setSelectedMonth] = useState('');
    const [summary, setSummary] = useState<any>(null);
    const [daily, setDaily] = useState<any>(null);
    const [byUser, setByUser] = useState<any>(null);
    const [byDept, setByDept] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);

    const userName = typeof window !== 'undefined' ? localStorage.getItem('user_name') || '사용자' : '사용자';

    // 월 옵션 (이번 달 / 지난달 / 2달 전)
    const monthOptions = useMemo(() => {
        const now = new Date();
        const opts = [];
        for (let i = 0; i < 3; i++) {
            const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
            const val = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
            const label = i === 0 ? '이번 달' : i === 1 ? '지난달' : '2달 전';
            opts.push({ value: val, label: `${label} (${val})` });
        }
        return opts;
    }, []);

    useEffect(() => {
        if (!selectedMonth && monthOptions.length > 0) {
            setSelectedMonth(monthOptions[0].value);
        }
    }, [monthOptions, selectedMonth]);

    useEffect(() => {
        if (!selectedMonth) return;
        const fetchData = async () => {
            setIsLoading(true);
            try {
                const [s, d, u, dept] = await Promise.all([
                    api.getUsageSummary(),
                    api.getUsageDaily(selectedMonth),
                    api.getUsageByUser(selectedMonth),
                    api.getUsageByDepartment(selectedMonth),
                ]);
                setSummary(s);
                setDaily(d);
                setByUser(u);
                setByDept(dept);
            } catch (err) {
                console.error('Failed to load usage data:', err);
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, [selectedMonth]);

    // 도넛 차트 데이터 (other는 비용이 있을 때만 표시)
    const pieData = useMemo(() => {
        if (!summary?.cost_by_category) return [];
        return Object.entries(summary.cost_by_category)
            .filter(([key, val]: [string, any]) => key !== 'other' || val.cost_krw > 0)
            .map(([key, val]: [string, any]) => ({
                name: CATEGORY_LABELS[key] || key,
                value: val.cost_krw,
                count: val.activity_count ?? 0,   // activity_logs 기반 건수
                color: CATEGORY_COLORS[key] || CATEGORY_COLORS.other,
            }));
    }, [summary]);

    // 바 차트 데이터
    const barData = useMemo(() => {
        if (!daily?.daily) return [];
        return daily.daily.map((d: any) => ({
            date: d.date.substring(5),  // "02-01" 형태
            비용: d.cost_krw,
            토큰: d.tokens,
        }));
    }, [daily]);

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_name');
        localStorage.removeItem('department');
        router.push('/auth/login');
    };

    const totalKRW = summary?.total_cost_krw ?? 0;
    const budget = summary?.monthly_budget_krw ?? 1_000_000;
    const budgetPct = summary?.budget_usage_percent ?? 0;
    const remaining = Math.max(0, budget - totalKRW);
    const costChangePct = summary?.vs_last_month?.cost_change_percent ?? 0;

    return (
        <div className="flex flex-col h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
                <Sheet open={sidebarOpen} onOpenChange={setSidebarOpen}>
                    <SheetTrigger asChild>
                        <button className="p-2 hover:bg-gray-100 rounded-lg">
                            <Menu className="w-6 h-6 text-gray-700" />
                        </button>
                    </SheetTrigger>
                    <SheetContent side="left" className="p-0 w-[280px]">
                        <AppSidebar
                            onNavigate={(path) => router.push(path)}
                            isMobile
                            onClose={() => setSidebarOpen(false)}
                            currentPath="/admin"
                        />
                    </SheetContent>
                </Sheet>

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
            <div className="flex-1 overflow-y-auto p-4 md:p-6">
                <div className="max-w-7xl mx-auto space-y-6">
                    {/* Page Header & Month Selector */}
                    <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3">
                        <div>
                            <h1 className="text-2xl md:text-3xl font-bold text-gray-900">사용 통계 및 한도 관리</h1>
                            <p className="text-gray-500 mt-1 text-sm">조직/개인별 이용 요금 및 현황을 한눈에 파악하여 예산을 안정적으로 관리합니다</p>
                        </div>
                        <Select value={selectedMonth} onValueChange={setSelectedMonth}>
                            <SelectTrigger className="w-[200px] bg-white">
                                <SelectValue placeholder="월 선택" />
                            </SelectTrigger>
                            <SelectContent>
                                {monthOptions.map(opt => (
                                    <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {isLoading ? (
                        <div className="flex items-center justify-center py-20">
                            <div className="text-center">
                                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
                                <p className="text-gray-500">통계를 불러오는 중...</p>
                            </div>
                        </div>
                    ) : (
                        <>
                            {/* Row 1: Summary Donut + Insight Cards */}
                            <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
                                {/* 이용 내역 도넛 차트 */}
                                <Card className="lg:col-span-3 shadow-sm">
                                    <CardHeader className="pb-2">
                                        <CardTitle className="text-lg font-semibold text-blue-700 flex items-center gap-2">
                                            <Coins className="w-5 h-5" />
                                            이번 달 이용 내역
                                        </CardTitle>
                                    </CardHeader>
                                    <CardContent>
                                        <div className="flex flex-col md:flex-row items-center gap-4">
                                            {/* 도넛 차트 */}
                                            <div className="w-full md:w-1/2 h-[220px]">
                                                {pieData.length > 0 ? (
                                                    <ResponsiveContainer width="100%" height="100%">
                                                        <PieChart>
                                                            <Pie
                                                                data={pieData}
                                                                cx="50%"
                                                                cy="50%"
                                                                innerRadius={55}
                                                                outerRadius={85}
                                                                paddingAngle={3}
                                                                dataKey="value"
                                                                strokeWidth={0}
                                                            >
                                                                {pieData.map((entry, idx) => (
                                                                    <Cell key={idx} fill={entry.color} />
                                                                ))}
                                                            </Pie>
                                                            <RechartsTooltip
                                                                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                                                formatter={((value: any) => [`₩${Math.round(Number(value) || 0).toLocaleString()}`, '비용']) as any}
                                                            />
                                                            {/* 가운데 텍스트 */}
                                                            <text x="50%" y="46%" textAnchor="middle" className="text-2xl font-bold fill-gray-900">
                                                                ₩{Math.round(totalKRW).toLocaleString()}
                                                            </text>
                                                            <text x="50%" y="58%" textAnchor="middle" className="text-xs fill-gray-500">
                                                                이번 달 총 비용
                                                            </text>
                                                        </PieChart>
                                                    </ResponsiveContainer>
                                                ) : (
                                                    <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                                                        데이터가 없습니다
                                                    </div>
                                                )}
                                            </div>

                                            {/* 카테고리 범례 */}
                                            <div className="w-full md:w-1/2 space-y-2">
                                                {pieData.map((item, idx) => (
                                                    <div key={idx} className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg">
                                                        <div className="flex items-center gap-2">
                                                            <div className="w-3 h-3 rounded-full" style={{ background: item.color }} />
                                                            <span className="text-sm text-gray-700">{item.name}</span>
                                                        </div>
                                                        <div className="text-right">
                                                            <span className="text-sm font-semibold text-gray-900">₩{Math.round(item.value).toLocaleString()}</span>
                                                            <span className="text-xs text-gray-500 ml-2">{item.count}건</span>
                                                        </div>
                                                    </div>
                                                ))}
                                                {pieData.length === 0 && (
                                                    <p className="text-sm text-gray-400 text-center py-4">사용 내역이 없습니다</p>
                                                )}
                                            </div>
                                        </div>
                                    </CardContent>
                                </Card>

                                {/* 인사이트 카드 */}
                                <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-4">
                                    {/* 전월 대비 */}
                                    <Card className="shadow-sm border-l-4" style={{ borderLeftColor: costChangePct >= 0 ? '#EF4444' : '#10B981' }}>
                                        <CardContent className="py-4 px-5">
                                            <p className="text-sm text-gray-500 mb-1">전월 대비</p>
                                            <div className="flex items-center gap-2">
                                                {costChangePct >= 0 ? (
                                                    <ArrowUpRight className="w-5 h-5 text-red-500" />
                                                ) : (
                                                    <ArrowDownRight className="w-5 h-5 text-emerald-500" />
                                                )}
                                                <span className={`text-2xl font-bold ${costChangePct >= 0 ? 'text-red-600' : 'text-emerald-600'}`}>
                                                    {costChangePct > 0 ? '+' : ''}{costChangePct}%
                                                </span>
                                            </div>
                                            <p className="text-xs text-gray-400 mt-1">
                                                지난 달 같은 기간 대비 비용 {costChangePct >= 0 ? '증가' : '감소'}
                                            </p>
                                        </CardContent>
                                    </Card>

                                    {/* 예산 사용률 */}
                                    <Card className="shadow-sm border-l-4 border-l-blue-500">
                                        <CardContent className="py-4 px-5">
                                            <p className="text-sm text-gray-500 mb-1">월 예산 사용률</p>
                                            <div className="flex items-baseline gap-1">
                                                <span className="text-2xl font-bold text-gray-900">{budgetPct}%</span>
                                                <span className="text-xs text-gray-400">/ {formatKRW(budget)}</span>
                                            </div>
                                            <Progress value={Math.min(budgetPct, 100)} className="mt-2 h-2" />
                                        </CardContent>
                                    </Card>

                                    {/* 사용 가능 잔액 */}
                                    <Card className="shadow-sm border-l-4 border-l-emerald-500">
                                        <CardContent className="py-4 px-5">
                                            <div className="flex items-center gap-2 mb-1">
                                                <Wallet className="w-4 h-4 text-emerald-600" />
                                                <p className="text-sm text-gray-500">사용 가능 잔액</p>
                                            </div>
                                            <span className="text-2xl font-bold text-emerald-700">
                                                ₩{Math.round(remaining).toLocaleString()}
                                            </span>
                                        </CardContent>
                                    </Card>

                                    {/* 총 토큰 */}
                                    <Card className="shadow-sm border-l-4 border-l-amber-500">
                                        <CardContent className="py-4 px-5">
                                            <div className="flex items-center gap-2 mb-1">
                                                <Zap className="w-4 h-4 text-amber-600" />
                                                <p className="text-sm text-gray-500">총 사용 토큰</p>
                                            </div>
                                            <span className="text-2xl font-bold text-gray-900">
                                                {formatNumber(summary?.total_tokens ?? 0)}
                                            </span>
                                        </CardContent>
                                    </Card>
                                </div>
                            </div>

                            {/* Row 2: Daily Cost Bar Chart */}
                            <Card className="shadow-sm">
                                <CardHeader className="pb-2">
                                    <CardTitle className="text-lg font-semibold text-blue-700 flex items-center gap-2">
                                        <TrendingUp className="w-5 h-5" />
                                        일별 비용 추이
                                    </CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="h-[280px]">
                                        {barData.length > 0 ? (
                                            <ResponsiveContainer width="100%" height="100%">
                                                <BarChart data={barData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                                                    <XAxis dataKey="date" tick={{ fontSize: 11 }} stroke="#9CA3AF" />
                                                    <YAxis tick={{ fontSize: 11 }} stroke="#9CA3AF" tickFormatter={(v) => formatKRW(v)} />
                                                    <RechartsTooltip
                                                        // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                                        formatter={((value: any, name: any) => [
                                                            name === '비용' ? `₩${Math.round(Number(value) || 0).toLocaleString()}` : (Number(value) || 0).toLocaleString(),
                                                            name,
                                                        ]) as any}
                                                    />
                                                    <Bar dataKey="비용" fill="#3B82F6" radius={[3, 3, 0, 0]} />
                                                </BarChart>
                                            </ResponsiveContainer>
                                        ) : (
                                            <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                                                데이터가 없습니다
                                            </div>
                                        )}
                                    </div>
                                </CardContent>
                            </Card>

                            {/* Row 3: Department & User Tables */}
                            <Card className="shadow-sm">
                                <CardContent className="pt-6">
                                    <Tabs defaultValue="department">
                                        <TabsList className="mb-4">
                                            <TabsTrigger value="department">부서별</TabsTrigger>
                                            <TabsTrigger value="user">사용자별</TabsTrigger>
                                        </TabsList>

                                        <TabsContent value="department">
                                            <div className="overflow-x-auto">
                                                <Table>
                                                    <TableHeader>
                                                        <TableRow>
                                                            <TableHead>부서</TableHead>
                                                            <TableHead className="text-right">비용 (KRW)</TableHead>
                                                            <TableHead className="text-right">토큰</TableHead>
                                                            <TableHead className="text-right">사용자 수</TableHead>
                                                        </TableRow>
                                                    </TableHeader>
                                                    <TableBody>
                                                        {byDept?.departments?.length > 0 ? (
                                                            byDept.departments.map((d: any, idx: number) => (
                                                                <TableRow key={idx}>
                                                                    <TableCell className="font-medium">{d.department}</TableCell>
                                                                    <TableCell className="text-right">₩{Math.round(d.total_cost_krw).toLocaleString()}</TableCell>
                                                                    <TableCell className="text-right">{d.total_tokens.toLocaleString()}</TableCell>
                                                                    <TableCell className="text-right">{d.user_count}</TableCell>
                                                                </TableRow>
                                                            ))
                                                        ) : (
                                                            <TableRow>
                                                                <TableCell colSpan={4} className="text-center text-gray-400 py-8">
                                                                    데이터가 없습니다
                                                                </TableCell>
                                                            </TableRow>
                                                        )}
                                                    </TableBody>
                                                </Table>
                                            </div>
                                        </TabsContent>

                                        <TabsContent value="user">
                                            <div className="overflow-x-auto">
                                                <Table>
                                                    <TableHeader>
                                                        <TableRow>
                                                            <TableHead>이름</TableHead>
                                                            <TableHead className="text-right">비용 (KRW)</TableHead>
                                                            <TableHead className="text-right">토큰</TableHead>
                                                            <TableHead className="text-right">채팅 횟수</TableHead>
                                                        </TableRow>
                                                    </TableHeader>
                                                    <TableBody>
                                                        {byUser?.users?.length > 0 ? (
                                                            byUser.users.map((u: any, idx: number) => (
                                                                <TableRow key={idx}>
                                                                    <TableCell className="font-medium">{u.user_name}</TableCell>
                                                                    <TableCell className="text-right">₩{Math.round(u.total_cost_krw).toLocaleString()}</TableCell>
                                                                    <TableCell className="text-right">{u.total_tokens.toLocaleString()}</TableCell>
                                                                    <TableCell className="text-right">{u.chat_count}</TableCell>
                                                                </TableRow>
                                                            ))
                                                        ) : (
                                                            <TableRow>
                                                                <TableCell colSpan={4} className="text-center text-gray-400 py-8">
                                                                    데이터가 없습니다
                                                                </TableCell>
                                                            </TableRow>
                                                        )}
                                                    </TableBody>
                                                </Table>
                                            </div>
                                        </TabsContent>
                                    </Tabs>
                                </CardContent>
                            </Card>
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}
