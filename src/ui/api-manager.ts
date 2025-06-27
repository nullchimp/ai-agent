import { Tool, DebugEvent } from './types';

export class ApiManager {
    private apiBaseUrl = 'http://localhost:5555/api';

    public async createNewBackendSession(): Promise<{ session_id: string }> {
        const response = await fetch(`${this.apiBaseUrl}/session/new`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) {
            throw new Error(`Failed to create session: ${response.status}`);
        }
        return response.json();
    }

    public async verifyBackendSession(sessionId: string): Promise<any> {
        const response = await fetch(`${this.apiBaseUrl}/session/${sessionId}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            return response.json();
        }
        throw new Error(`Backend session ${sessionId} not found`);
    }
    
    public async deleteBackendSession(sessionId: string): Promise<void> {
        const deleteUrl = `${this.apiBaseUrl}/session/${sessionId}`;
        console.log(`Deleting backend session at: ${deleteUrl}`);
        const response = await fetch(deleteUrl, { method: 'DELETE' });
        if (!response.ok && response.status !== 404) {
            console.warn(`Failed to delete backend session ${sessionId}: ${response.status}`);
        } else {
            console.log(`Successfully deleted backend session ${sessionId}`);
        }
    }

    public async ask(sessionId: string, message: string): Promise<{ response: string, usedTools: string[] }> {
        const apiUrl = `${this.apiBaseUrl}/${sessionId}/ask`;
        console.log(`Making API call to: ${apiUrl}`);
        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-API-Key': 'test_12345' },
                body: JSON.stringify({ query: message })
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return {
                response: data.response || 'Sorry, I couldn\'t process your request.',
                usedTools: data.used_tools || []
            };
        } catch (error) {
            console.error('API call failed:', error);
            return {
                response: 'An error occurred while communicating with the AI.',
                usedTools: []
            };
        }
    }

    public async loadTools(sessionId: string): Promise<Tool[]> {
        const toolsUrl = `${this.apiBaseUrl}/${sessionId}/tools`;
        console.log(`Loading tools from: ${toolsUrl}`);
        try {
            const response = await fetch(toolsUrl, { headers: { 'X-API-Key': 'test_12345' } });
            if (response.ok) {
                const data = await response.json();
                return data.tools || [];
            }
            console.error(`Failed to load tools: ${response.status}`);
        } catch (error) {
            console.error('Failed to load tools:', error);
        }
        return [];
    }

    public async toggleTool(sessionId: string, toolName: string, enabled: boolean): Promise<boolean> {
        const toggleUrl = `${this.apiBaseUrl}/${sessionId}/tools/toggle`;
        console.log(`Toggling tool ${toolName} to ${enabled} at: ${toggleUrl}`);
        try {
            const response = await fetch(toggleUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-API-Key': 'test_12345' },
                body: JSON.stringify({ tool_name: toolName, enabled: enabled })
            });
            if (response.ok) {
                console.log(`Successfully toggled tool ${toolName} to ${enabled}`);
                return true;
            }
            console.error('Failed to toggle tool:', await response.text());
        } catch (error) {
            console.error('Error toggling tool:', error);
        }
        return false;
    }

    public async setDebugMode(sessionId: string, enabled: boolean): Promise<{ enabled: boolean } | null> {
        try {
            const response = await fetch(`${this.apiBaseUrl}/${sessionId}/debug/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-API-Key': 'test_12345' },
                body: JSON.stringify({ enabled: enabled })
            });
            if (response.ok) {
                return await response.json();
            }
            console.error('Failed to set debug mode:', await response.text());
        } catch (error) {
            console.error('Error setting debug mode:', error);
        }
        return null;
    }

    public async loadDebugEvents(sessionId: string): Promise<{ events: DebugEvent[], enabled: boolean } | null> {
        try {
            const response = await fetch(`${this.apiBaseUrl}/${sessionId}/debug`, {
                headers: { 'X-API-Key': 'test_12345' }
            });
            if (response.ok) {
                return await response.json();
            }
            console.error('Failed to load debug events:', await response.text());
        } catch (error) {
            console.error('Error loading debug events:', error);
        }
        return null;
    }

    public async clearDebugEvents(sessionId: string): Promise<boolean> {
        try {
            const response = await fetch(`${this.apiBaseUrl}/${sessionId}/debug`, {
                method: 'DELETE',
                headers: { 'X-API-Key': 'test_12345' }
            });
            if (response.ok) {
                return true;
            }
            console.error('Failed to clear debug events:', await response.text());
        } catch (error) {
            console.error('Error clearing debug events:', error);
        }
        return false;
    }
}
