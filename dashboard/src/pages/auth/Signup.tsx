import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { Button, Input, Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui';
import { Mail, Lock, User, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';

const Signup: React.FC = () => {
    const navigate = useNavigate();
    const register = useAuthStore((state) => state.register);
    const isLoading = useAuthStore((state) => state.isLoading);

    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const passwordStrength = password.length >= 8 ? 'strong' : password.length >= 6 ? 'medium' : 'weak';

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (!name || !email || !password) {
            setError('Please fill in all fields');
            return;
        }

        if (password.length < 8) {
            setError('Password must be at least 8 characters');
            return;
        }

        try {
            await register(email, name, password);
            toast.success('Account created successfully!');
            navigate('/dashboard');
        } catch (err) {
            setError('Failed to create account');
            toast.error('Signup failed');
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 px-4">
            <Card className="w-full max-w-md" variant="elevated">
                <CardHeader>
                    <div className="flex items-center justify-center mb-4">
                        <div className="h-12 w-12 bg-primary-600 rounded-lg flex items-center justify-center">
                            <span className="text-white text-2xl font-bold">C</span>
                        </div>
                    </div>
                    <CardTitle className="text-center">Create Account</CardTitle>
                    <CardDescription className="text-center">
                        Start securing your infrastructure today
                    </CardDescription>
                </CardHeader>

                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {error && (
                            <div className="flex items-center gap-2 p-3 bg-critical-50 dark:bg-critical-900/20 border border-critical-200 dark:border-critical-800 rounded-md">
                                <AlertCircle className="h-4 w-4 text-critical-600 dark:text-critical-400" />
                                <span className="text-sm text-critical-600 dark:text-critical-400">{error}</span>
                            </div>
                        )}

                        <Input
                            type="text"
                            label="Full Name"
                            placeholder="John Doe"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            icon={<User className="h-4 w-4" />}
                            disabled={isLoading}
                        />

                        <Input
                            type="email"
                            label="Email"
                            placeholder="you@example.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            icon={<Mail className="h-4 w-4" />}
                            disabled={isLoading}
                        />

                        <div>
                            <Input
                                type="password"
                                label="Password"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                icon={<Lock className="h-4 w-4" />}
                                disabled={isLoading}
                                helperText="Must be at least 8 characters"
                            />
                            {password && (
                                <div className="mt-2 flex items-center gap-2 text-sm">
                                    <div className="flex-1 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                        <div
                                            className={`h-full transition-all ${passwordStrength === 'strong'
                                                ? 'bg-low-500 w-full'
                                                : passwordStrength === 'medium'
                                                    ? 'bg-medium-500 w-2/3'
                                                    : 'bg-critical-500 w-1/3'
                                                }`}
                                        />
                                    </div>
                                    <span className={`${passwordStrength === 'strong'
                                        ? 'text-low-600'
                                        : passwordStrength === 'medium'
                                            ? 'text-medium-600'
                                            : 'text-critical-600'
                                        }`}>
                                        {passwordStrength}
                                    </span>
                                </div>
                            )}
                        </div>

                        <label className="flex items-start gap-2 cursor-pointer text-sm">
                            <input type="checkbox" className="mt-0.5 rounded" required />
                            <span className="text-gray-600 dark:text-gray-400">
                                I agree to the{' '}
                                <a href="#" className="text-primary-600 hover:text-primary-700">
                                    Terms of Service
                                </a>{' '}
                                and{' '}
                                <a href="#" className="text-primary-600 hover:text-primary-700">
                                    Privacy Policy
                                </a>
                            </span>
                        </label>

                        <Button
                            type="submit"
                            variant="primary"
                            className="w-full"
                            isLoading={isLoading}
                        >
                            Create Account
                        </Button>

                        <div className="text-center text-sm text-gray-600 dark:text-gray-400">
                            Already have an account?{' '}
                            <Link to="/login" className="text-primary-600 hover:text-primary-700 font-medium">
                                Sign in
                            </Link>
                        </div>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
};

export default Signup;
