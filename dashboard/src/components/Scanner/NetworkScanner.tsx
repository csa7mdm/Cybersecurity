import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';

interface NetworkScannerProps {
    onScanStarted?: (scanId: string) => void;
}

export default function NetworkScanner({ onScanStarted }: NetworkScannerProps) {
    const [target, setTarget] = useState('');
    const [portRange, setPortRange] = useState('1-1000');
    const [authTargetId, setAuthTargetId] = useState('');
    const [isScanning, setIsScanning] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleScan = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsScanning(true);

        try {
            const result = await apiService.createNetworkScan(target, portRange, authTargetId);

            if (onScanStarted) {
                onScanStarted(result.scan_id);
            }

            navigate(`/scans/${result.scan_id}`);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to start scan');
        } finally {
            setIsScanning(false);
        }
    };

    return (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center mb-6">
                <div className="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center mr-4">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                    </svg>
                </div>
                <div>
                    <h2 className="text-2xl font-semibold text-white">Network Scanner</h2>
                    <p className="text-gray-400 text-sm">Port scanning and service detection</p>
                </div>
            </div>

            {error && (
                <div className="bg-red-900/30 border border-red-700 text-red-400 px-4 py-3 rounded mb-4">
                    {error}
                </div>
            )}

            <form onSubmit={handleScan} className="space-y-4">
                <div>
                    <label htmlFor="target" className="block text-sm font-medium text-gray-300 mb-2">
                        Target IP / CIDR *
                    </label>
                    <input
                        id="target"
                        type="text"
                        required
                        value={target}
                        onChange={(e) => setTarget(e.target.value)}
                        placeholder="192.168.1.0/24 or 192.168.1.1"
                        className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Single IP or network range (CIDR notation)</p>
                </div>

                <div>
                    <label htmlFor="portRange" className="block text-sm font-medium text-gray-300 mb-2">
                        Port Range *
                    </label>
                    <select
                        id="portRange"
                        value={portRange}
                        onChange={(e) => setPortRange(e.target.value)}
                        className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-green-500"
                    >
                        <option value="1-1000">Top 1000 (1-1000)</option>
                        <option value="1-65535">All Ports (1-65535)</option>
                        <option value="1-100">Quick Scan (1-100)</option>
                        <option value="20-25,80,443,3306,5432">Common Services</option>
                    </select>
                    <p className="text-xs text-gray-500 mt-1">Select predefined range or enter custom (e.g., 80,443,8080-8090)</p>
                </div>

                <div>
                    <label htmlFor="authTarget" className="block text-sm font-medium text-gray-300 mb-2">
                        Authorization Target ID *
                    </label>
                    <input
                        id="authTarget"
                        type="text"
                        required
                        value={authTargetId}
                        onChange={(e) => setAuthTargetId(e.target.value)}
                        placeholder="UUID of authorized target"
                        className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                </div>

                <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
                    <p className="text-yellow-400 text-sm">
                        ⚠️ <strong>Authorization Required:</strong> Only scan networks you own or have explicit written permission to test.
                    </p>
                </div>

                <button
                    type="submit"
                    disabled={isScanning}
                    className="w-full bg-green-600 hover:bg-green-700 disabled:bg-green-800 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-lg transition duration-200"
                >
                    {isScanning ? (
                        <span className="flex items-center justify-center">
                            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Scanning...
                        </span>
                    ) : (
                        '🌐 Start Network Scan'
                    )}
                </button>
            </form>

            <div className="mt-6 pt-6 border-t border-gray-700">
                <h3 className="text-sm font-semibold text-gray-300 mb-2">What This Scans:</h3>
                <ul className="text-sm text-gray-400 space-y-1">
                    <li>• Open/closed port detection</li>
                    <li>• Service identification (HTTP, SSH, MySQL, etc.)</li>
                    <li>• Banner grabbing for version info</li>
                    <li>• OS fingerprinting</li>
                    <li>• Vulnerability detection</li>
                </ul>
            </div>
        </div>
    );
}
