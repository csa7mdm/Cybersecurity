import axios, { AxiosInstance } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/v1';

class ApiService {
    private client: AxiosInstance;
    private token: string | null = null;

    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Request interceptor to add auth token
        this.client.interceptors.request.use(
            (config) => {
                if (this.token) {
                    config.headers.Authorization = `Bearer ${this.token}`;
                }
                return config;
            },
            (error) => Promise.reject(error)
        );

        // Response interceptor for error handling
        this.client.interceptors.response.use(
            (response) => response,
            (error) => {
                if (error.response?.status === 401) {
                    this.clearToken();
                    window.location.href = '/login';
                }
                return Promise.reject(error);
            }
        );

        // Load token from localStorage
        const storedToken = localStorage.getItem('auth_token');
        if (storedToken) {
            this.token = storedToken;
        }
    }

    setToken(token: string) {
        this.token = token;
        localStorage.setItem('auth_token', token);
    }

    clearToken() {
        this.token = null;
        localStorage.removeItem('auth_token');
    }

    // Authentication
    async login(email: string, password: string) {
        const response = await this.client.post('/auth/login', { email, password });
        if (response.data.access_token) {
            this.setToken(response.data.access_token);
        }
        return response.data;
    }

    async register(email: string, username: string, password: string, fullName?: string) {
        const response = await this.client.post('/auth/register', {
            email,
            username,
            password,
            full_name: fullName,
        });
        return response.data;
    }

    async logout() {
        try {
            await this.client.post('/auth/logout');
        } finally {
            this.clearToken();
        }
    }

    async acceptTerms(userId: string, termsVersion: string) {
        const response = await this.client.post('/auth/accept-terms', {
            user_id: userId,
            terms_version: termsVersion,
            acceptance_ip: 'browser',
        });
        return response.data;
    }

    // Scans
    async getScans(limit = 50) {
        const response = await this.client.get('/scans', { params: { limit } });
        return response.data;
    }

    async getScan(scanId: string) {
        const response = await this.client.get(`/scans/${scanId}`);
        return response.data;
    }

    async createWiFiScan(targetSSID: string, authTargetId: string) {
        const response = await this.client.post('/scans/wifi', {
            target: {
                type: 'wifi_network',
                ssid: targetSSID,
            },
            authorization_target_id: authTargetId,
            scan_mode: 'passive',
        });
        return response.data;
    }

    async createNetworkScan(target: string, portRange: string, authTargetId: string) {
        const response = await this.client.post('/scans/network', {
            target: {
                type: 'network',
                value: target,
            },
            authorization_target_id: authTargetId,
            configuration: {
                port_range: portRange,
                scan_type: 'tcp_connect',
            },
        });
        return response.data;
    }

    async stopScan(scanId: string) {
        const response = await this.client.post(`/scans/${scanId}/stop`);
        return response.data;
    }

    // Results
    async getScanResults(scanId: string) {
        const response = await this.client.get(`/scans/${scanId}/results`);
        return response.data;
    }

    async getVulnerabilities(scanId?: string, severity?: string) {
        const params: any = {};
        if (scanId) params.scan_id = scanId;
        if (severity) params.severity = severity;

        const response = await this.client.get('/vulnerabilities', { params });
        return response.data;
    }

    // Reports
    async getReports(scanId?: string) {
        const params = scanId ? { scan_id: scanId } : {};
        const response = await this.client.get('/reports', { params });
        return response.data;
    }

    async generateReport(scanId: string, reportType: string) {
        const response = await this.client.post(`/scans/${scanId}/reports`, {
            report_type: reportType,
        });
        return response.data;
    }

    async downloadReport(reportId: string) {
        const response = await this.client.get(`/reports/${reportId}/download`, {
            responseType: 'blob',
        });
        return response.data;
    }

    // Monitors
    async getMonitors() {
        const response = await this.client.get('/monitors');
        return response.data;
    }

    async createMonitor(targetId: string, schedule: string, alertThreshold: number) {
        const response = await this.client.post('/monitors', {
            target_id: targetId,
            schedule,
            alert_threshold: alertThreshold,
        });
        return response.data;
    }

    // Audit Logs
    async getAuditLogs(limit = 100) {
        const response = await this.client.get('/audit-logs', { params: { limit } });
        return response.data;
    }
}

export const apiService = new ApiService();
export default apiService;
