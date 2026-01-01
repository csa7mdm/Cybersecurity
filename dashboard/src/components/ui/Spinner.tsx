import React from 'react';
import { cn } from '../../utils/cn';
import { Loader2 } from 'lucide-react';

export interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
    size?: 'sm' | 'md' | 'lg' | 'xl';
    variant?: 'default' | 'primary';
}

const Spinner = React.forwardRef<HTMLDivElement, SpinnerProps>(
    ({ className, size = 'md', variant = 'default', ...props }, ref) => {
        const sizes = {
            sm: 'h-4 w-4',
            md: 'h-6 w-6',
            lg: 'h-8 w-8',
            xl: 'h-12 w-12',
        };

        const variants = {
            default: 'text-gray-400',
            primary: 'text-primary-600',
        };

        return (
            <div
                ref={ref}
                role="status"
                aria-label="Loading"
                className={cn('inline-block', className)}
                {...props}
            >
                <Loader2 className={cn('animate-spin', sizes[size], variants[variant])} />
                <span className="sr-only">Loading...</span>
            </div>
        );
    }
);

Spinner.displayName = 'Spinner';

export default Spinner;
