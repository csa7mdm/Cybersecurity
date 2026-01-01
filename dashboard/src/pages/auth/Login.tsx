import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { Button, Input, Card, CardHeader, CardTitle, CardDescription, CardContent } from '../../components/ui';
import { Mail, Lock, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';

const Login: React.FC = () => {
    const navigate = useNavigate();
    const { login: loginUser, isLoading } = useAuthStore();

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (!email || !password) {
            setError('Please fill in all fields');
            return;
        }

        try {
            await loginUser(email, password);
            toast.success('Welcome back!');
            navigate('/dashboard');
        } catch (err) {
            setError('Invalid email or password');
            toast.error('Login failed');
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
                    <CardTitle className="text-center">Welcome Back</CardTitle>
                    <CardDescription className="text-center">
                        Sign in to your CyperSecurity account
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
                            type="email"
                            label="Email"
                            placeholder="you@example.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            icon={<Mail className="h-4 w-4" />}
                            disabled={isLoading}
                        />

                        <Input
                            type="password"
                            label="Password"
                            placeholder="••••••••"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            icon={<Lock className="h-4 w-4" />}
                            disabled={isLoading}
                        />

                        <div className="flex items-center justify-between text-sm">
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input type="checkbox" className="rounded" />
                                <span className="text-gray-600 dark:text-gray-400">Remember me</span>
                            </label>
                            <a href="#" className="text-primary-600 hover:text-primary-700">
                                Forgot password?
                            </a>
                        </div>

                        <Button
                            type="submit"
                            variant="primary"
                            className="w-full"
                            isLoading={isLoading}
                        >
                            Sign In
                        </Button>

                        <div className="text-center text-sm text-gray-600 dark:text-gray-400">
                            Don't have an account?{' '}
                            <Link to="/signup" className="text-primary-600 hover:text-primary-700 font-medium">
                                Sign up
                            </Link>
                        </div>

                        <div className="text-center text-sm text-gray-500">
                            <Link to="/demo" className="hover:text-primary-600">
                                View Component Demo →
                            </Link>
                        </div>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
};

export default Login;
