import React from 'react';
import { cn } from '../../utils/cn';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
    helperText?: string;
    icon?: React.ReactNode;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
    ({ className, label, error, helperText, icon, id, ...props }, ref) => {
        const inputId = id || `input-${Math.random().toString(36).substring(7)}`;

        return (
            <div className="w-full">
                {label && (
                    <label
                        htmlFor={inputId}
                        className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                    >
                        {label}
                    </label>
                )}

                <div className="relative">
                    {icon && (
                        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
                            {icon}
                        </div>
                    )}

                    <input
                        ref={ref}
                        id={inputId}
                        className={cn(
                            'w-full h-10 px-3 py-2 text-base',
                            'border rounded-md',
                            'bg-white dark:bg-gray-800',
                            'text-gray-900 dark:text-gray-100',
                            'placeholder:text-gray-400',
                            'focus:outline-none focus:ring-2 focus:ring-offset-0',
                            'disabled:opacity-50 disabled:cursor-not-allowed',
                            'transition-colors',
                            error
                                ? 'border-critical-500 focus:ring-critical-500'
                                : 'border-gray-300 dark:border-gray-600 focus:ring-primary-500',
                            icon && 'pl-10',
                            className
                        )}
                        {...props}
                    />
                </div>

                {(error || helperText) && (
                    <p
                        className={cn(
                            'mt-1 text-sm',
                            error ? 'text-critical-600 dark:text-critical-400' : 'text-gray-500 dark:text-gray-400'
                        )}
                    >
                        {error || helperText}
                    </p>
                )}
            </div>
        );
    }
);

Input.displayName = 'Input';

export default Input;
