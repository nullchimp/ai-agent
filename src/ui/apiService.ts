import { ApiResponse, CreateSessionResponse, Tool, DebugEvent, DebugInfo } from './types';

export class ApiService {
    public apiBaseUrl: string;

    constructor(apiBaseUrl: string = 'http://localhost:5555/api') {
        this.apiBaseUrl = apiBaseUrl;
    }

    async callChatAPI(message: string, sessionId: string): Promise<ApiResponse> {
        const response = await fetch(`${this.apiBaseUrl}/${sessionId}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': 'test_12345'
            },
            body: JSON.stringify({ message })
        });

        if (!response.ok) {
            throw new Error(`API request failed: ${response.status}`);
        }

        const data = await response.json();
        return {
            response: data.response || '',
            usedTools: data.used_tools || []
        };
    }

    async createNewSession(): Promise<string> {
        const response = await fetch(`${this.apiBaseUrl}/sessions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': 'test_12345'
            },
            body: JSON.stringify({})
        });

        if (!response.ok) {
            throw new Error(`Failed to create session: ${response.status}`);
        }

        const data: CreateSessionResponse = await response.json();
        return data.session_id;
    }

    async verifySession(sessionId: string): Promise<boolean> {
        try {
            const response = await fetch(`${this.apiBaseUrl}/${sessionId}/verify`, {
                headers: {
                    'X-API-Key': 'test_12345'
                }
            });
            return response.ok;
        } catch (error) {
            console.error('Error verifying session:', error);
            return false;
        }
    }

    async deleteSession(sessionId: string): Promise<void> {
        const response = await fetch(`${this.apiBaseUrl}/${sessionId}`, {
            method: 'DELETE',
            headers: {
                'X-API-Key': 'test_12345'
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to delete session: ${response.status}`);
        }
    }

    async loadTools(sessionId: string): Promise<Tool[]> {
        const response = await fetch(`${this.apiBaseUrl}/${sessionId}/tools`, {
            headers: {
                'X-API-Key': 'test_12345'
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to load tools: ${response.status}`);
        }

        const data = await response.json();
        return data.tools || [];
    }

    async toggleTool(sessionId: string, toolName: string, enabled: boolean): Promise<void> {
        const response = await fetch(`${this.apiBaseUrl}/${sessionId}/tools/${toolName}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': 'test_12345'
            },
            body: JSON.stringify({ enabled })
        });

        if (!response.ok) {
            throw new Error(`Failed to toggle tool: ${response.status}`);
        }
    }

    async toggleAllTools(sessionId: string, enabled: boolean): Promise<void> {
        const response = await fetch(`${this.apiBaseUrl}/${sessionId}/tools/toggle-all`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': 'test_12345'
            },
            body: JSON.stringify({ enabled })
        });

        if (!response.ok) {
            throw new Error(`Failed to toggle all tools: ${response.status}`);
        }
    }

    async toggleSourceTools(sessionId: string, source: string, enabled: boolean): Promise<void> {
        const response = await fetch(`${this.apiBaseUrl}/${sessionId}/tools/toggle-source`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': 'test_12345'
            },
            body: JSON.stringify({ source, enabled })
        });

        if (!response.ok) {
            throw new Error(`Failed to toggle source tools: ${response.status}`);
        }
    }

    async setDebugMode(sessionId: string, enabled: boolean): Promise<void> {
        const response = await fetch(`${this.apiBaseUrl}/${sessionId}/debug`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': 'test_12345'
            },
            body: JSON.stringify({ enabled })
        });

        if (!response.ok) {
            throw new Error(`Failed to set debug mode: ${response.status}`);
        }
    }

    async clearDebugEvents(sessionId: string): Promise<void> {
        const response = await fetch(`${this.apiBaseUrl}/${sessionId}/debug/clear`, {
            method: 'DELETE',
            headers: {
                'X-API-Key': 'test_12345'
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to clear debug events: ${response.status}`);
        }
    }

    async loadDebugEvents(sessionId: string): Promise<DebugInfo> {
        const response = await fetch(`${this.apiBaseUrl}/${sessionId}/debug`, {
            headers: {
                'X-API-Key': 'test_12345'
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to load debug events: ${response.status}`);
        }

        return await response.json();
    }
}