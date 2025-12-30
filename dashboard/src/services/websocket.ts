import { io, Socket } from 'socket.io-client';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8081';

export interface ScanProgress {
    scan_id: string;
    progress: number;
    current_phase: string;
}

export interface Vulnerability {
    id: string;
    title: string;
    severity: string;
    description: string;
}

export interface Alert {
    severity: string;
    message: string;
    timestamp: string;
}

class WebSocketService {
    private socket: Socket | null = null;
    private listeners: Map<string, Set<Function>> = new Map();

    connect(token: string) {
        if (this.socket?.connected) {
            return;
        }

        this.socket = io(WS_URL, {
            auth: {
                token,
            },
            transports: ['websocket'],
        });

        this.socket.on('connect', () => {
            console.log('WebSocket connected');
        });

        this.socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
        });

        this.socket.on('message', (data: any) => {
            this.handleMessage(data);
        });

        return this.socket;
    }

    disconnect() {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        this.listeners.clear();
    }

    private handleMessage(data: any) {
        const { type } = data;
        const eventListeners = this.listeners.get(type);

        if (eventListeners) {
            eventListeners.forEach((callback) => callback(data.data));
        }

        // Also trigger 'all' listeners
        const allListeners = this.listeners.get('all');
        if (allListeners) {
            allListeners.forEach((callback) => callback(data));
        }
    }

    on(event: string, callback: Function) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, new Set());
        }
        this.listeners.get(event)!.add(callback);

        // Return unsubscribe function
        return () => {
            this.listeners.get(event)?.delete(callback);
        };
    }

    off(event: string, callback?: Function) {
        if (callback) {
            this.listeners.get(event)?.delete(callback);
        } else {
            this.listeners.delete(event);
        }
    }

    // Convenience methods for specific events
    onScanProgress(callback: (data: ScanProgress) => void) {
        return this.on('scan_progress', callback);
    }

    onScanComplete(callback: (data: any) => void) {
        return this.on('scan_complete', callback);
    }

    onVulnerabilityFound(callback: (data: { scan_id: string; vulnerability: Vulnerability }) => void) {
        return this.on('vulnerability_found', callback);
    }

    onAlert(callback: (data: Alert) => void) {
        return this.on('alert', callback);
    }

    onSystemStatus(callback: (data: any) => void) {
        return this.on('system_status', callback);
    }

    send(type: string, data: any) {
        if (this.socket?.connected) {
            this.socket.emit('message', { type, data });
        }
    }

    subscribe(eventType: string) {
        this.send('subscribe', { event: eventType });
    }

    unsubscribe(eventType: string) {
        this.send('unsubscribe', { event: eventType });
    }
}

export const wsService = new WebSocketService();
export default wsService;
