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
    sessionId?: string;  // Backend session ID (optional for backward compatibility)
    title: string;
    messages: Message[];
    createdAt: Date;
    debugPanelOpen?: boolean;  // Debug panel state per session
    debugEnabled?: boolean;    // Debug enabled state per session
}

export interface DebugEvent {
    event_type: string;
    message: string;
    data: Record<string, any>;
    timestamp: string;
    session_id?: string;
}

export interface DebugInfo {
    events: DebugEvent[];
    enabled: boolean;
}

export interface ApiResponse {
    response: string;
    usedTools: string[];
}

export interface CreateSessionResponse {
    session_id: string;
    message: string;
}