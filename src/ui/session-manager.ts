import { ChatSession, Message } from './types';
import { ApiManager } from './api-manager';

export class SessionManager {
    public sessions: ChatSession[] = [];
    public currentSession: ChatSession | null = null;
    private chatHistory: HTMLElement;

    constructor(private apiManager: ApiManager, private onSessionChanged: () => Promise<void>) {
        this.chatHistory = document.getElementById('chatHistory') as HTMLElement;
        this.loadChatHistory();
    }

    public async createNewSession(): Promise<ChatSession> {
        const sessionData = await this.apiManager.createNewBackendSession();
        const session: ChatSession = {
            id: this.generateId(),
            sessionId: sessionData.session_id,
            title: 'New Chat',
            messages: [],
            createdAt: new Date(),
            debugPanelOpen: false,
            debugEnabled: false
        };

        this.sessions.unshift(session);
        this.currentSession = session;
        this.saveChatHistory();
        this.renderChatHistory();
        await this.onSessionChanged();
        return session;
    }

    public async loadSession(sessionId: string): Promise<void> {
        const session = this.sessions.find(s => s.id === sessionId);
        if (!session) return;

        this.currentSession = session;
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

        this.saveChatHistory();
        this.renderChatHistory();
    }

    public updateSessionTitle(): void {
        if (!this.currentSession || this.currentSession.messages.length === 0) return;

        const firstUserMessage = this.currentSession.messages.find(m => m.role === 'user');
        if (firstUserMessage && this.currentSession.title === 'New Chat') {
            this.currentSession.title = firstUserMessage.content.substring(0, 50) +
                (firstUserMessage.content.length > 50 ? '...' : '');
            this.renderChatHistory();
            this.saveChatHistory();
        }
    }

    public addMessageToCurrentSession(message: Message): void {
        if (!this.currentSession) return;
        this.currentSession.messages.push(message);
        this.saveChatHistory();
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
                await this.apiManager.verifyBackendSession(this.currentSession.sessionId);
                console.log(`Backend session ${this.currentSession.sessionId} verified.`);
            } catch (error) {
                console.warn(`Backend session ${this.currentSession.sessionId} not found, will create new session when needed.`);
                this.currentSession.sessionId = undefined;
                this.saveChatHistory();
            }
        }
    }

    private saveChatHistory(): void {
        try {
            const sessionsToSave = this.sessions.map(s => ({ ...s }));
            localStorage.setItem('chatSessions', JSON.stringify(sessionsToSave));
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
                    createdAt: new Date(session.createdAt),
                    messages: session.messages.map((msg: any) => ({
                        ...msg,
                        timestamp: new Date(msg.timestamp)
                    }))
                }));
                if (this.sessions.length > 0) {
                    this.currentSession = this.sessions[0];
                }
            } catch (error) {
                console.error('Failed to load chat history:', error);
                this.sessions = [];
            }
        }
    }

    private generateId(): string {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
}
