export interface Message {
    id: string;
    content: string;
    role: 'user' | 'assistant';
    timestamp: Date;
    usedTools?: string[];
}

export interface Tool {
    name: string;
    description: string;
    enabled: boolean;
    source: string;
    parameters: Record<string, any>;
}

export interface ChatSession {
    id: string;
    sessionId?: string;
    title: string;
    messages: Message[];
    createdAt: Date;
    debugPanelOpen?: boolean;
    debugEnabled?: boolean;
}

export interface DebugEvent {
    event_type: string;
    message: string;
    data: Record<string, any>;
    timestamp: string;
    session_id?: string;
}
