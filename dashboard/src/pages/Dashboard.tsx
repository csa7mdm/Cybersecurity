import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import WiFiScanner from '../components/Scanner/WiFiScanner';
import NetworkScanner from '../components/Scanner/NetworkScanner';

export default function Dashboard() {
    const { user, logout } = useAuthStore();
    const [activeTab, setActiveTab] = useState<'wifi' | 'network'>('wifi');
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    return (
        <div className="min-h-screen bg-gray-900">
            {/* Header */}
            <header className="bg-gray-800 shadow-lg border-b border-gray-700">
                <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <h1 className="text-2xl font-bold text-white">🔐 Cyper Security</h1>
                        <span className="px-3 py-1 bg-blue-600 text-white text-xs font-semibold rounded-full">
                            v0.1.0-alpha
                        </span>
                    </div>

                    <div className="flex items-center space-x-4">
                        <div className="text-right">
                            <p className="text-sm text-gray-400">Signed in as</p>
                            <p className="text-white font-medium">{user?.email}</p>
                        </div>
                        <button
                            onClick={handleLogout}
                            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition"
                        >
                            Logout
                        </button>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-4 py-8">
                {/* Welcome Section */}
                <div className="mb-8">
                    <h2 className="text-3xl font-bold text-white mb-2">Welcome back!</h2>
                    <p className="text-gray-400">Select a scan type to begin security assessment</p>
                </div>

                {/* Tabs */}
                <div className="flex space-x-2 mb-6">
                    <button
                        onClick={() => setActiveTab('wifi')}
                        className={`px-6 py-3 rounded-lg font-semibold transition ${activeTab === 'wifi'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
                            }`}
                    >
                        📡 WiFi Security
                    </button>
                    <button
                        onClick={() => setActiveTab('network')}
                        className={`px-6 py-3 rounded-lg font-semibold transition ${activeTab === 'network'
                                ? 'bg-green-600 text-white'
                                : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
                            }`}
                    >
                        🌐 Network Scanning
                    </button>
                </div>

                {/* Scanner Content */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2">
                        {activeTab === 'wifi' && <WiFiScanner />}
                        {activeTab === 'network' && <NetworkScanner />}
                    </div>

                    {/* Sidebar */}
                    <div className="space-y-6">
                        {/* Recent Scans */}
                        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                            <h3 className="text-lg font-semibold text-white mb-4">Recent Scans</h3>
                            <p className="text-gray-400 text-sm">No recent scans</p>
                        </div>

                        {/* Quick Stats */}
                        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
                            <h3 className="text-lg font-semibold text-white mb-4">Quick Stats</h3>
                            <div className="space-y-3">
                                <div className="flex justify-between">
                                    <span className="text-gray-400 text-sm">Total Scans</span>
                                    <span className="text-white font-semibold">0</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-400 text-sm">Vulnerabilities</span>
                                    <span className="text-red-400 font-semibold">0</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-gray-400 text-sm">Reports</span>
                                    <span className="text-white font-semibold">0</span>
                                </div>
                            </div>
                        </div>

                        {/* Legal Notice */}
                        <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
                            <p className="text-yellow-400 text-xs">
                                <strong>⚠️ Legal Notice:</strong> Unauthorized scanning is illegal. Always obtain explicit written permission before testing.
                            </p>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
