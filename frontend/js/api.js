/**
 * Vanilla JavaScript API Client (Phase 4 Stage 4J & Stage 45)
 * Centralizes REST API calls to FastAPI backend.
 */

const API_BASE = "/api";

async function apiFetch(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        if (!response.ok) {
            throw new Error(`API Error ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Fetch failed for ${endpoint}:`, error);
        throw error;
    }
}

const API = {
    getHealth: () => apiFetch("/health"),
    getCompany: () => apiFetch("/company"),
    getRequirements: () => apiFetch("/requirements"),
    getPolicies: () => apiFetch("/policies"),
    getRecommendation: () => apiFetch("/recommendation"),
    getAudit: () => apiFetch("/audit"),
    getPitch: () => apiFetch("/pitch"),
    getEvidenceDetail: (id) => apiFetch(`/evidence/${id}`)
};
