import { ChatSession, Message } from '../types';
import { ApiManager } from './api';
import { AuthManager, UserSession } from './auth';

export class SessionManager {
    public sessions: ChatSession[] = [];
    public currentSession: ChatSession | null = null;
    private chatHistory: HTMLElement;
    private authManager: AuthManager;

    constructor(private apiManager: ApiManager, private onSessionChanged: () => Promise<void>) {
        this.chatHistory = document.getElementById('chatHistory') as HTMLElement;
        this.authManager = new AuthManager();
    }

    public async createNewSession(): Promise<ChatSession> {
        try {
            const sessionData = await this.apiManager.createNewBackendSession();
            const session: ChatSession = {
                id: sessionData.session_id,
                sessionId: sessionData.session_id,
                title: 'New Chat',
                messages: [],
                createdAt: new Date(),
                debugPanelOpen: false,
                debugEnabled: false
            };

            this.sessions.unshift(session);
            this.currentSession = session;
            this.renderChatHistory();
            await this.onSessionChanged();
            return session;
        } catch (error: any) {
            if (error.message && error.message.includes('401')) {
                this.authManager.clearAuth();
            }
            throw error;
        }
    }

    public async loadSession(sessionId: string): Promise<void> {
        const session = this.sessions.find(s => s.id === sessionId);
        if (!session) return;

        this.currentSession = session;
        
        if (session.sessionId && session.messages.length === 0) {
            try {
                const sessionData = await this.apiManager.verifyBackendSession(session.sessionId);
                if (sessionData.conversation_history && sessionData.conversation_history.length > 0) {
                    session.messages = sessionData.conversation_history;
                }
                if (sessionData.title) {
                    session.title = sessionData.title;
                }
            } catch (error) {
                console.warn(`Failed to load session data for ${session.sessionId}:`, error);
            }
        }
        
        this.renderChatHistory();
        await this.onSessionChanged();
    }

    public async deleteSession(sessionId: string): Promise<void> {
        const sessionIndex = this.sessions.findIndex(s => s.id === sessionId);
        if (sessionIndex === -1) return;

        const session = this.sessions[sessionIndex];
        if (session.sessionId) {
            try {
                await this.apiManager.deleteBackendSession(session.sessionId);
            } catch (error) {
                console.error('Failed to delete backend session:', error);
            }
        }

        this.sessions.splice(sessionIndex, 1);

        if (this.currentSession?.id === sessionId) {
            if (this.sessions.length > 0) {
                await this.loadSession(this.sessions[0].id);
            } else {
                this.currentSession = null;
                await this.onSessionChanged();
            }
        }

        this.renderChatHistory();
    }

    public updateSessionTitle(): void {
        if (!this.currentSession || this.currentSession.messages.length === 0) return;

        const firstUserMessage = this.currentSession.messages.find(m => m.role === 'user');
        if (firstUserMessage && this.currentSession.title === 'New Chat') {
            this.currentSession.title = firstUserMessage.content.substring(0, 50) +
                (firstUserMessage.content.length > 50 ? '...' : '');
            this.renderChatHistory();
        }
    }

    public addMessageToCurrentSession(message: Message): void {
        if (!this.currentSession) return;
        this.currentSession.messages.push(message);
    }

    public renderChatHistory(): void {
        this.chatHistory.innerHTML = '';
        this.sessions.forEach(session => {
            const item = document.createElement('div');
            item.className = 'chat-item';
            if (session.id === this.currentSession?.id) {
                item.classList.add('active');
            }

            const title = document.createElement('span');
            title.className = 'chat-title';
            title.textContent = session.title;

            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'chat-delete-btn';
            deleteBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <polyline points="3,6 5,6 21,6"></polyline>
                    <path d="M19,6V20a2,2,0,0,1-2,2H7a2,2,0,0,1-2-2V6M8,6V4a2,2,0,0,1,2-2h4a2,2,0,0,1,2,2V6"></path>
                    <line x1="10" y1="11" x2="10" y2="17"></line>
                    <line x1="14" y1="11" x2="14" y2="17"></line>
                </svg>`;
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteSession(session.id);
            });

            item.appendChild(title);
            item.appendChild(deleteBtn);
            item.addEventListener('click', () => this.loadSession(session.id));
            this.chatHistory.appendChild(item);
        });
    }

    public async verifyCurrentSession(): Promise<void> {
        if (this.currentSession?.sessionId) {
            try {
                const sessionData = await this.apiManager.verifyBackendSession(this.currentSession.sessionId);
                console.log(`Backend session ${this.currentSession.sessionId} verified.`);
                if (sessionData.conversation_history && sessionData.conversation_history.length > 0) {
                    this.currentSession.messages = sessionData.conversation_history;
                }
                if (sessionData.title) {
                    this.currentSession.title = sessionData.title;
                }
            } catch (error) {
                console.warn(`Backend session ${this.currentSession.sessionId} not found, will create new session when needed.`);
                this.currentSession.sessionId = undefined;
            }
        }
    }

    public async loadUserSessions(): Promise<void> {
        if (!this.authManager.isAuthenticated()) {
            this.sessions = [];
            this.currentSession = null;
            return;
        }

        try {
            const userSessions = await this.authManager.getUserSessions();
            this.sessions = userSessions.map((session: UserSession) => ({
                id: session.session_id,
                sessionId: session.session_id,
                title: session.title,
                messages: [],
                createdAt: new Date(session.last_activity),
                debugPanelOpen: false,
                debugEnabled: false
            }));
            
            if (this.sessions.length > 0) {
                this.currentSession = this.sessions[0];
            }
        } catch (error: any) {
            console.error('Failed to load user sessions:', error);
            if (error.message && error.message.includes('401')) {
                this.authManager.clearAuth();
                throw error;
            }
            this.sessions = [];
        }
    }

    private async saveChatHistory(): Promise<void> {
    }

    private generateId(): string {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
}
