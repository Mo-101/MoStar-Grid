// ═══════════════════════════════════════════════════════════════════════════════
//                    MOSTAR GRID - FRONTEND API CONFIGURATION
//                      'First African AI Homeworld'
// ═══════════════════════════════════════════════════════════════════════════════

// ═══════════════════════════════════════════════════════════════════════════════
//                           API CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════════

// Base URL for the MoStar Grid API
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

// API Endpoints
export const API_ENDPOINTS = {
    // Health & Status
    ROOT: '/',
    STATUS: '/api/v1/status',
    VITALS: '/api/v1/vitals',

    // Core Triad
    REASON: '/api/v1/reason',      // Mind Layer - Ifá Logic
    VOICE: '/api/v1/voice',        // Body Layer - Text-to-Speech
    MOMENT: '/api/v1/moment',      // Soul Layer - Event Logging
    MOMENTS: '/api/v1/moments',    // Get recent moments

    // Extended
    AGENTS: '/api/v1/agents',
    ODU: '/api/v1/odu',
};

// ═══════════════════════════════════════════════════════════════════════════════
//                           API CLIENT CLASS
// ═══════════════════════════════════════════════════════════════════════════════

class MoStarGridAPI {
    private baseUrl: string;

    constructor(baseUrl: string = API_BASE_URL) {
        this.baseUrl = baseUrl;
    }

    // ─────────────────────────────────────────────────────────────────────────────
    // HEALTH CHECKS
    // ─────────────────────────────────────────────────────────────────────────────

    async getStatus() {
        const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.STATUS}`);
        return response.json();
    }

    async getVitals() {
        const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.VITALS}`);
        return response.json();
    }

    // ─────────────────────────────────────────────────────────────────────────────
    // MIND LAYER - IFÁ REASONING
    // ─────────────────────────────────────────────────────────────────────────────

    async reason(query: string, context: string | null = null) {
        const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.REASON}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, context }),
        });
        return response.json();
    }

    // ─────────────────────────────────────────────────────────────────────────────
    // BODY LAYER - VOICE
    // ─────────────────────────────────────────────────────────────────────────────

    async speak(text: string): Promise<Blob> {
        const formData = new FormData();
        formData.append('text', text);

        const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.VOICE}`, {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            return response.blob();
        }
        throw new Error('Voice synthesis failed');
    }

    // ─────────────────────────────────────────────────────────────────────────────
    // SOUL LAYER - MOMENT LOGGING
    // ─────────────────────────────────────────────────────────────────────────────

    async logMoment(eventType: string, source: string, data: Record<string, any>) {
        const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.MOMENT}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ event_type: eventType, source, data }),
        });
        return response.json();
    }

    async getMoments(limit: number = 50) {
        const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.MOMENTS}?limit=${limit}`);
        return response.json();
    }

    // ─────────────────────────────────────────────────────────────────────────────
    // AGENTS
    // ─────────────────────────────────────────────────────────────────────────────

    async getAgents(layer: string | null = null) {
        const url = layer
            ? `${this.baseUrl}${API_ENDPOINTS.AGENTS}?layer=${layer}`
            : `${this.baseUrl}${API_ENDPOINTS.AGENTS}`;
        const response = await fetch(url);
        return response.json();
    }

    async getAgent(name: string) {
        const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.AGENTS}/${name}`);
        return response.json();
    }

    // ─────────────────────────────────────────────────────────────────────────────
    // ODÚ PATTERNS
    // ─────────────────────────────────────────────────────────────────────────────

    async getOduPatterns(principalOnly: boolean = false) {
        const url = `${this.baseUrl}${API_ENDPOINTS.ODU}?principal_only=${principalOnly}`;
        const response = await fetch(url);
        return response.json();
    }

    async getOduPattern(code: number) {
        const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.ODU}/${code}`);
        return response.json();
    }

    async evaluateOdu(inputVector: number[], query: string | null = null) {
        const response = await fetch(`${this.baseUrl}${API_ENDPOINTS.ODU}/evaluate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input_vector: inputVector, query }),
        });
        return response.json();
    }
}

// Export singleton instance
export const gridAPI = new MoStarGridAPI();

// ═══════════════════════════════════════════════════════════════════════════════
//                           REACT HOOKS
// ═══════════════════════════════════════════════════════════════════════════════

import { useState, useEffect } from 'react';

export function useGridStatus() {
    const [status, setStatus] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        gridAPI.getStatus()
            .then(setStatus)
            .catch(setError)
            .finally(() => setLoading(false));
    }, []);

    return { status, loading, error };
}

export function useGridVitals() {
    const [vitals, setVitals] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    const refresh = () => {
        setLoading(true);
        gridAPI.getVitals()
            .then(setVitals)
            .catch(setError)
            .finally(() => setLoading(false));
    };

    useEffect(() => {
        refresh();
    }, []);

    return { vitals, loading, error, refresh };
}

export function useAgents(layer: string | null = null) {
    const [agents, setAgents] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        gridAPI.getAgents(layer)
            .then(data => setAgents(data.agents || []))
            .catch(setError)
            .finally(() => setLoading(false));
    }, [layer]);

    return { agents, loading, error };
}

export default MoStarGridAPI;
