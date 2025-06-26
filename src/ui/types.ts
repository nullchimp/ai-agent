// Type declaration for marked library
declare const marked: {
    parse(markdown: string): string;
};

// Common interfaces used across components
interface Message {
    id: string;
    content: string;
    role: 'user' | 'assistant';
    timestamp: Date;
    usedTools?: string[];
}

interface Tool {
    name: string;
    description: string;
    enabled: boolean;
    source: string;
    parameters: Record<string, any>;
}

interface ChatSession {
    id: string;
    sessionId?: string;  // Backend session ID (optional for backward compatibility)
    title: string;
    messages: Message[];
    createdAt: Date;
    debugPanelOpen?: boolean;  // Debug panel state per session
    debugEnabled?: boolean;    // Debug enabled state per session
}

interface DebugEvent {
    event_type: string;
    message: string;
    data: Record<string, any>;
    timestamp: string;
    session_id?: string;
}

interface DebugInfo {
    events: DebugEvent[];
    enabled: boolean;
}

// Event emitter for inter-component communication
interface ChatEventMap {
    'session-changed': { session: ChatSession };
    'tools-loaded': { tools: Tool[] };
    'debug-state-changed': { enabled: boolean, panelOpen: boolean };
    'message-sent': { message: Message };
    'typing-indicator': { show: boolean };
}

class EventEmitter {
    private listeners: Map<string, Function[]> = new Map();

    on<K extends keyof ChatEventMap>(event: K, callback: (data: ChatEventMap[K]) => void): void {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, []);
        }
        this.listeners.get(event)!.push(callback);
    }

    emit<K extends keyof ChatEventMap>(event: K, data: ChatEventMap[K]): void {
        const callbacks = this.listeners.get(event);
        if (callbacks) {
            callbacks.forEach(callback => callback(data));
        }
    }

    off<K extends keyof ChatEventMap>(event: K, callback: (data: ChatEventMap[K]) => void): void {
        const callbacks = this.listeners.get(event);
        if (callbacks) {
            const index = callbacks.indexOf(callback);
            if (index > -1) {
                callbacks.splice(index, 1);
            }
        }
    }
}