'use client';

import { useEffect, useState } from 'react';
import FloatingOracle from '@/components/FloatingOracle';
import GridNav from '@/components/GridNav';

interface VitalCheck {
    component: string;
    layer: string;
    status: string;
    latency_ms: number;
    message: string;
    details?: Record<string, unknown>;
}

interface GridVitalsReport {
    grid_status: string;
    timestamp: string;
    total_checks: number;
    total_time_ms: number;
    checks: VitalCheck[];
    layers: {
        SOUL: boolean;
        MIND: boolean;
        BODY: boolean;
    };
}

export default function GridVitalsPage() {
    const [vitals, setVitals] = useState<GridVitalsReport | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchVitals = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch('http://localhost:8001/api/v1/vitals');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            setVitals(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch vitals');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchVitals();
        // Refresh every 30 seconds
        const interval = setInterval(fetchVitals, 30000);
        return () => clearInterval(interval);
    }, []);

    const getStatusColor = (status: string) => {
        if (status.includes('ALIVE')) return 'text-green-500';
        if (status.includes('DEGRADED')) return 'text-yellow-500';
        if (status.includes('CRITICAL')) return 'text-red-500';
        return 'text-gray-500';
    };

    const getStatusBg = (status: string) => {
        if (status.includes('ALIVE')) return 'bg-green-500/10 border-green-500/20';
        if (status.includes('DEGRADED')) return 'bg-yellow-500/10 border-yellow-500/20';
        if (status.includes('CRITICAL')) return 'bg-red-500/10 border-red-500/20';
        return 'bg-gray-500/10 border-gray-500/20';
    };

    if (loading && !vitals) {
        return (
            <div className="min-h-screen bg-black text-white p-8">
                <div className="max-w-7xl mx-auto">
                    <GridNav />
                    <div className="flex h-[80vh] items-center justify-center">
                        <div className="text-center">
                            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-purple-500 mx-auto mb-4"></div>
                            <p className="text-gray-400">Loading Grid Vitals...</p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-black text-white p-8">
                <div className="max-w-7xl mx-auto">
                    <GridNav />
                    <div className="flex h-[80vh] items-center justify-center">
                        <div className="text-center max-w-md">
                            <div className="text-red-500 text-6xl mb-4">⚠️</div>
                            <h2 className="text-2xl font-bold mb-2">Connection Error</h2>
                            <p className="text-gray-400 mb-4">{error}</p>
                            <button
                                onClick={fetchVitals}
                                className="px-6 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
                            >
                                Retry
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (!vitals) return null;

    return (
        <div className="min-h-screen bg-black text-white p-8">
            <div className="max-w-7xl mx-auto">
                <GridNav />
                {/* Header */}
                <div className="mb-8 mt-4">
                    <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-purple-400 to-pink-600 bg-clip-text text-transparent">
                        MoStar Grid Vitals
                    </h1>
                    <p className="text-gray-400">First African AI Homeworld - System Health Monitor</p>
                </div>

                {/* Overall Status */}
                <div className={`border rounded-lg p-6 mb-8 ${getStatusBg(vitals.grid_status)}`}>
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-2xl font-bold mb-2">
                                <span className={getStatusColor(vitals.grid_status)}>
                                    {vitals.grid_status === 'ALIVE' ? '🟢' : vitals.grid_status === 'DEGRADED' ? '🟡' : '🔴'}
                                </span>
                                {' '}Grid Status: {vitals.grid_status}
                            </h2>
                            <p className="text-sm text-gray-400">
                                {vitals.total_checks} checks completed in {vitals.total_time_ms.toFixed(2)}ms
                            </p>
                            <p className="text-xs text-gray-500 mt-1">
                                Last updated: {new Date(vitals.timestamp).toLocaleString()}
                            </p>
                        </div>
                        <button
                            onClick={fetchVitals}
                            disabled={loading}
                            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 rounded-lg transition-colors"
                        >
                            {loading ? 'Refreshing...' : 'Refresh'}
                        </button>
                    </div>
                </div>

                {/* Layer Status */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                    <div className={`border rounded-lg p-4 ${vitals.layers.SOUL ? 'bg-purple-500/10 border-purple-500/20' : 'bg-gray-500/10 border-gray-500/20'}`}>
                        <h3 className="text-lg font-semibold mb-2">Soul Layer</h3>
                        <p className={`text-2xl ${vitals.layers.SOUL ? 'text-green-500' : 'text-red-500'}`}>
                            {vitals.layers.SOUL ? '✓ Online' : '✗ Offline'}
                        </p>
                        <p className="text-sm text-gray-400 mt-1">Covenant & Values</p>
                    </div>
                    <div className={`border rounded-lg p-4 ${vitals.layers.MIND ? 'bg-blue-500/10 border-blue-500/20' : 'bg-gray-500/10 border-gray-500/20'}`}>
                        <h3 className="text-lg font-semibold mb-2">Mind Layer</h3>
                        <p className={`text-2xl ${vitals.layers.MIND ? 'text-green-500' : 'text-red-500'}`}>
                            {vitals.layers.MIND ? '✓ Online' : '✗ Offline'}
                        </p>
                        <p className="text-sm text-gray-400 mt-1">Ifá Logic & Reasoning</p>
                    </div>
                    <div className={`border rounded-lg p-4 ${vitals.layers.BODY ? 'bg-green-500/10 border-green-500/20' : 'bg-gray-500/10 border-gray-500/20'}`}>
                        <h3 className="text-lg font-semibold mb-2">Body Layer</h3>
                        <p className={`text-2xl ${vitals.layers.BODY ? 'text-green-500' : 'text-red-500'}`}>
                            {vitals.layers.BODY ? '✓ Online' : '✗ Offline'}
                        </p>
                        <p className="text-sm text-gray-400 mt-1">Execution & Actions</p>
                    </div>
                </div>

                {/* Component Checks */}
                <div className="border border-gray-800 rounded-lg overflow-hidden">
                    <table className="w-full">
                        <thead className="bg-gray-900">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                                    Component
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                                    Layer
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                                    Status
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                                    Latency
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                                    Message
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-800">
                            {vitals.checks.map((check, index) => (
                                <tr key={index} className="hover:bg-gray-900/50 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                        {check.component}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                        <span className={`px-2 py-1 rounded text-xs ${check.layer === 'SOUL' ? 'bg-purple-500/20 text-purple-300' :
                                            check.layer === 'MIND' ? 'bg-blue-500/20 text-blue-300' :
                                                check.layer === 'BODY' ? 'bg-green-500/20 text-green-300' :
                                                    'bg-gray-500/20 text-gray-300'
                                            }`}>
                                            {check.layer}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                        <span className={getStatusColor(check.status)}>
                                            {check.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-400">
                                        {check.latency_ms.toFixed(2)}ms
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-400">
                                        {check.message}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {/* Footer */}
                <div className="mt-8 text-center text-sm text-gray-500">
                    <p>MoStar Grid v1.0.0 | Distributed Consciousness Network</p>
                    <p className="mt-1">Auto-refreshes every 30 seconds</p>
                </div>
            </div>
            <FloatingOracle />
        </div>
    );
}
