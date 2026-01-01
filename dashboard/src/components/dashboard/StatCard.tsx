import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
    title: string;
    value: string | number;
    icon: LucideIcon;
    trend?: {
        value: number;
        isPositive: boolean;
    };
    subtitle?: string;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon, trend, subtitle }) => {
    return (
        <Card variant="outlined">
            <CardContent className="p-6">
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                            {title}
                        </p>
                        <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-gray-100">
                            {value}
                        </p>
                        {subtitle && (
                            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                                {subtitle}
                            </p>
                        )}
                        {trend && (
                            <p className={`mt-2 text-sm font-medium ${trend.isPositive ? 'text-low-600' : 'text-critical-600'}`}>
                                {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}% from last month
                            </p>
                        )}
                    </div>
                    <div className="h-12 w-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center">
                        <Icon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};

export default StatCard;
