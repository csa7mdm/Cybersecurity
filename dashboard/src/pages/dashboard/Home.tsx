import React from 'react';
import Sidebar from '../../components/layout/Sidebar';
import StatCard from '../../components/dashboard/StatCard';
import { Card, CardHeader, CardTitle, CardContent, Badge } from '../../components/ui';
import {
    Shield,
    Activity,
    AlertTriangle,
    TrendingUp,
    Clock,
    CheckCircle2,
} from 'lucide-react';
import { formatRelativeTime } from '../../utils/cn';

const DashboardHome: React.FC = () => {
    // Mock data
    const stats = [
        {
            title: 'Total Scans',
            value: 127,
            icon: Shield,
            trend: { value: 12, isPositive: true },
            subtitle: 'This month',
        },
        {
            title: 'Active Vulnerabilities',
            value: 23,
            icon: AlertTriangle,
            trend: { value: 8, isPositive: false },
            subtitle: '15 critical',
        },
        {
            title: 'Risk Score',
            value: '7.2',
            icon: Activity,
            subtitle: 'Medium risk',
        },
        {
            title: 'Remediation Rate',
            value: '68%',
            icon: TrendingUp,
            trend: { value: 5, isPositive: true },
            subtitle: 'Last 30 days',
        },
    ];

    const recentScans = [
        {
            id: '1',
            target: 'api.example.com',
            status: 'completed',
            severity: 'critical' as const,
            findings: 12,
            timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
        },
        {
            id: '2',
            target: 'web.example.com',
            status: 'completed',
            severity: 'high' as const,
            findings: 5,
            timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000),
        },
        {
            id: '3',
            target: 'app.example.com',
            status: 'running',
            severity: 'info' as const,
            findings: 0,
            timestamp: new Date(Date.now() - 10 * 60 * 1000),
        },
        {
            id: '4',
            target: 'admin.example.com',
            status: 'completed',
            severity: 'medium' as const,
            findings: 8,
            timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000),
        },
    ];

    return (
        <Sidebar>
            <div className="space-y-6">
                {/* Page header */}
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                        Dashboard
                    </h1>
                    <p className="mt-1 text-gray-600 dark:text-gray-400">
                        Welcome back! Here's what's happening with your security posture.
                    </p>
                </div>

                {/* Stats grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {stats.map((stat) => (
                        <StatCard key={stat.title} {...stat} />
                    ))}
                </div>

                {/* Recent scans */}
                <Card variant="outlined">
                    <CardHeader>
                        <CardTitle>Recent Scans</CardTitle>
                    </CardHeader>
                    <CardContent className="px-0">
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-gray-200 dark:border-gray-700">
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                            Target
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                            Status
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                            Findings
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                            Time
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                            Actions
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                    {recentScans.map((scan) => (
                                        <tr
                                            key={scan.id}
                                            className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                                        >
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="flex items-center gap-2">
                                                    <Shield className="h-4 w-4 text-gray-400" />
                                                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                                        {scan.target}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                {scan.status === 'completed' ? (
                                                    <Badge variant="success" size="sm">
                                                        <CheckCircle2 className="h-3 w-3" />
                                                        Completed
                                                    </Badge>
                                                ) : (
                                                    <Badge variant="info" size="sm">
                                                        <Clock className="h-3 w-3 animate-spin" />
                                                        Running
                                                    </Badge>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                {scan.findings > 0 ? (
                                                    <Badge variant={scan.severity} size="sm">
                                                        {scan.findings} findings
                                                    </Badge>
                                                ) : (
                                                    <span className="text-sm text-gray-500">-</span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                                {formatRelativeTime(scan.timestamp)}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                <button className="text-primary-600 hover:text-primary-700 font-medium">
                                                    View Details
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </CardContent>
                </Card>

                {/* Quick actions */}
                <Card variant="outlined">
                    <CardHeader>
                        <CardTitle>Quick Actions</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <button className="p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-primary-500 dark:hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/10 transition-colors group">
                                <Shield className="h-8 w-8 text-gray-400 group-hover:text-primary-600 mx-auto mb-2" />
                                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                    New Scan
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                    Start a security scan
                                </p>
                            </button>

                            <button className="p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-primary-500 dark:hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/10 transition-colors group">
                                <Activity className="h-8 w-8 text-gray-400 group-hover:text-primary-600 mx-auto mb-2" />
                                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                    View Analytics
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                    Security insights
                                </p>
                            </button>

                            <button className="p-4 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg hover:border-primary-500 dark:hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/10 transition-colors group">
                                <AlertTriangle className="h-8 w-8 text-gray-400 group-hover:text-primary-600 mx-auto mb-2" />
                                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                    Review Alerts
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                    23 active vulnerabilities
                                </p>
                            </button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </Sidebar>
    );
};

export default DashboardHome;
