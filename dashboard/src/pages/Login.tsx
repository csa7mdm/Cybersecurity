import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export default function Login() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const { login, isLoading, error, clearError } = useAuthStore();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        clearError();

        try {
            await login(email, password);
            navigate('/dashboard');
        } catch (err) {
            // Error is handled by store
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 flex items-center justify-center px-4">
            <div className="max-w-md w-full">
                {/* Logo/Header */}
                <div className="text-center mb-8">
                    <h1 className="text-4xl font-bold text-white mb-2">
                        🔐 Cyper Security
                    </h1>
                    <p className="text-gray-400">Cybersecurity Testing Platform</p>
                </div>

                {/* Login Card */}
                <div className="bg-gray-800 rounded-lg shadow-2xl p-8 border border-gray-700">
                    <h2 className="text-2xl font-semibold text-white mb-6">Sign In</h2>

                    {error && (
                        <div className="bg-red-900/30 border border-red-700 text-red-400 px-4 py-3 rounded mb-4">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                                Email Address
                            </label>
                            <input
                                id="email"
                                type="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                                placeholder="you@example.com"
                            />
                        </div>

                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
                                Password
                            </label>
                            <input
                                id="password"
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                                placeholder="••••••••"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-lg transition duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
                        >
                            {isLoading ? 'Signing in...' : 'Sign In'}
                        </button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-gray-400 text-sm">
                            Don't have an account?{' '}
                            <Link to="/register" className="text-blue-400 hover:text-blue-300 font-medium">
                                Sign up
                            </Link>
                        </p>
                    </div>

                    <div className="mt-6 pt-6 border-t border-gray-700">
                        <p className="text-xs text-gray-500 text-center">
                            Default admin: admin@cyper.security / Admin123!
                        </p>
                    </div>
                </div>

                {/* Warning */}
                <div className="mt-6 bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
                    <p className="text-yellow-400 text-sm text-center">
                        ⚠️ <strong>Authorized Use Only</strong> - Requires explicit written permission
                    </p>
                </div>
            </div>
        </div>
    );
}
