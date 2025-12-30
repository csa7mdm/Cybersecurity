import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiService } from '../services/api';

interface WiFiScannerProps {
    onScanStarted?: (scanId: string) => void;
}

export default function WiFiScanner({ onScanStarted }: WiFiScannerProps) {
    const [ssid, setSSID] = useState('');
    const [authTargetId, setAuthTargetId] = useState('');
    const [isScanning, setIsScanning] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleScan = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsScanning(true);

        try {
            const result = await apiService.createWiFiScan(ssid, authTargetId);

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
                <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mr-4">
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0" />
                    </svg>
                </div>
                <div>
                    <h2 className="text-2xl font-semibold text-white">WiFi Scanner</h2>
                    <p className="text-gray-400 text-sm">Analyze WiFi network security</p>
                </div>
            </div>

            {error && (
                <div className="bg-red-900/30 border border-red-700 text-red-400 px-4 py-3 rounded mb-4">
                    {error}
                </div>
            )}

            <form onSubmit={handleScan} className="space-y-4">
                <div>
                    <label htmlFor="ssid" className="block text-sm font-medium text-gray-300 mb-2">
                        Target SSID *
                    </label>
                    <input
                        id="ssid"
                        type="text"
                        required
                        value={ssid}
                        onChange={(e) => setSSID(e.target.value)}
                        placeholder="WiFi Network Name"
                        className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">Leave empty to scan all visible networks</p>
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
                        className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                        Required: Proof of authorization for this target
                    </p>
                </div>

                <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-4">
                    <p className="text-yellow-400 text-sm">
                        ⚠️ <strong>Authorization Required:</strong> Only scan networks you own or have explicit written permission to test.
                    </p>
                </div>

                <button
                    type="submit"
                    disabled={isScanning}
                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-semibold py-3 px-4 rounded-lg transition duration-200"
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
                        '🔍 Start WiFi Scan'
                    )}
                </button>
            </form>

            <div className="mt-6 pt-6 border-t border-gray-700">
                <h3 className="text-sm font-semibold text-gray-300 mb-2">What This Scans:</h3>
                <ul className="text-sm text-gray-400 space-y-1">
                    <li>• Security protocol (WEP, WPA, WPA2, WPA3)</li>
                    <li>• Signal strength and channel</li>
                    <li>• WPS status and vulnerabilities</li>
                    <li>• Crackability assessment</li>
                    <li>• Security recommendations</li>
                </ul>
            </div>
        </div>
    );
}
