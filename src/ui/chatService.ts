import { Utils } from './utils.js';

interface Message {
    id: string;
    content: string;
    role: 'user' | 'assistant';
    timestamp: Date;
    usedTools?: string[];
}

interface ChatSession {
    id: string;
    sessionId?: string;
    title: string;
    messages: Message[];
    createdAt: Date;
    debugPanelOpen?: boolean;
    debugEnabled?: boolean;
}

export class ChatService {
    private sessions: ChatSession[] = [];

    constructor() {
        this.loadChatHistory();
    }

    getSessions(): ChatSession[] {
        return this.sessions;
    }

    getCurrentSession(): ChatSession | null {
        return this.sessions.length > 0 ? this.sessions[0] : null;
    }

    createSession(backendSessionId?: string): ChatSession {
        const newSession: ChatSession = {
            id: Utils.generateId(),
            sessionId: backendSessionId,
            title: 'New Chat',
            messages: [],
            createdAt: new Date(),
            debugPanelOpen: false,
            debugEnabled: false
        };

        this.sessions.unshift(newSession);
        this.saveChatHistory();
        return newSession;
    }

    deleteSession(sessionId: string): ChatSession | null {
        const index = this.sessions.findIndex(s => s.id === sessionId);
        if (index === -1) return null;

        const deletedSession = this.sessions.splice(index, 1)[0];
        this.saveChatHistory();
        return deletedSession;
    }

    updateSessionTitle(session: ChatSession): void {
        if (session.messages.length === 0) return;

        const firstUserMessage = session.messages.find(m => m.role === 'user');
        if (firstUserMessage && session.title === 'New Chat') {
            session.title = firstUserMessage.content.substring(0, 50) + 
                (firstUserMessage.content.length > 50 ? '...' : '');
            this.saveChatHistory();
        }
    }

    addMessage(session: ChatSession, message: Message): void {
        session.messages.push(message);
        this.updateSessionTitle(session);
        this.saveChatHistory();
    }

    clearMessages(session: ChatSession): void {
        session.messages = [];
        this.saveChatHistory();
    }

    updateSessionBackendId(session: ChatSession, backendSessionId: string | undefined): void {
        session.sessionId = backendSessionId;
        this.saveChatHistory();
    }

    updateDebugState(session: ChatSession, debugPanelOpen: boolean, debugEnabled: boolean): void {
        session.debugPanelOpen = debugPanelOpen;
        session.debugEnabled = debugEnabled;
        this.saveChatHistory();
    }

    getSessionDebugState(session: ChatSession): { debugPanelOpen: boolean; debugEnabled: boolean } {
        return {
            debugPanelOpen: session.debugPanelOpen || false,
            debugEnabled: session.debugEnabled || false
        };
    }

    private saveChatHistory(): void {
        try {
            const sessionsToSave = this.sessions.map(session => ({
                id: session.id,
                sessionId: session.sessionId,
                title: session.title,
                messages: session.messages,
                createdAt: session.createdAt,
                debugPanelOpen: session.debugPanelOpen || false,
                debugEnabled: session.debugEnabled || false
            }));
            
            localStorage.setItem('chatSessions', JSON.stringify(sessionsToSave));
            console.log('Saved chat history:', sessionsToSave.length, 'sessions');
        } catch (error) {
            console.error('Failed to save chat history:', error);
        }
    }

    private loadChatHistory(): void {
        const saved = localStorage.getItem('chatSessions');
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                this.sessions = parsed.map((session: any) => ({
                    ...session,
                    sessionId: session.sessionId || null,
                    createdAt: new Date(session.createdAt),
                    debugPanelOpen: session.debugPanelOpen || false,
                    debugEnabled: session.debugEnabled || false,
                    messages: session.messages.map((msg: any) => ({
                        ...msg,
                        timestamp: new Date(msg.timestamp)
                    }))
                }));
                
                console.log('Loaded chat history:', this.sessions.length, 'sessions');
                this.sessions.forEach(session => {
                    console.log(`Session ${session.id}: backend sessionId = ${session.sessionId}, debugPanel = ${session.debugPanelOpen}, debugEnabled = ${session.debugEnabled}`);
                });
            } catch (error) {
                console.error('Failed to load chat history:', error);
                this.sessions = [];
            }
        }
    }

    validateMessage(content: string): { isValid: boolean; error?: string } {
        if (!content || content.trim().length === 0) {
            return { isValid: false, error: 'Message cannot be empty' };
        }
        
        if (content.length > 10000) {
            return { isValid: false, error: 'Message is too long (max 10,000 characters)' };
        }
        
        return { isValid: true };
    }

    createMessage(content: string, role: 'user' | 'assistant', usedTools?: string[]): Message {
        return {
            id: Utils.generateId(),
            content,
            role,
            timestamp: new Date(),
            usedTools
        };
    }

    getSessionById(sessionId: string): ChatSession | null {
        return this.sessions.find(s => s.id === sessionId) || null;
    }

    getSessionByBackendId(backendSessionId: string): ChatSession | null {
        return this.sessions.find(s => s.sessionId === backendSessionId) || null;
    }

    shouldCreateNewSession(): boolean {
        return this.sessions.length === 0;
    }

    getMostRecentSession(): ChatSession | null {
        return this.sessions.length > 0 ? this.sessions[0] : null;
    }
}