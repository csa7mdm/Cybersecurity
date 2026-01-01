import React from 'react';
import { cn } from '../../utils/cn';

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
    variant?: Severity | 'default' | 'success' | 'warning';
    size?: 'sm' | 'md' | 'lg';
    dot?: boolean;
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
    ({ className, variant = 'default', size = 'md', dot, children, ...props }, ref) => {
        const baseStyles = 'inline-flex items-center gap-1.5 font-medium rounded-full';

        const variants = {
            critical: 'bg-critical-100 text-critical-800 dark:bg-critical-900/30 dark:text-critical-400',
            high: 'bg-high-100 text-high-800 dark:bg-high-900/30 dark:text-high-400',
            medium: 'bg-medium-100 text-medium-800 dark:bg-medium-900/30 dark:text-medium-400',
            low: 'bg-low-100 text-low-800 dark:bg-low-900/30 dark:text-low-400',
            info: 'bg-info-100 text-info-800 dark:bg-info-900/30 dark:text-info-400',
            default: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300',
            success: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
            warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
        };

        const sizes = {
            sm: 'px-2 py-0.5 text-xs',
            md: 'px-2.5 py-1 text-sm',
            lg: 'px-3 py-1.5 text-base',
        };

        const dotColors = {
            critical: 'bg-critical-500',
            high: 'bg-high-500',
            medium: 'bg-medium-500',
            low: 'bg-low-500',
            info: 'bg-info-500',
            default: 'bg-gray-500',
            success: 'bg-green-500',
            warning: 'bg-yellow-500',
        };

        return (
            <span
                ref={ref}
                className={cn(
                    baseStyles,
                    variants[variant],
                    sizes[size],
                    className
                )}
                {...props}
            >
                {dot && <span className={cn('h-1.5 w-1.5 rounded-full', dotColors[variant])} />}
                {children}
            </span>
        );
    }
);

Badge.displayName = 'Badge';

export default Badge;
