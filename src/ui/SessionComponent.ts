class SessionComponent {
    private sessions: ChatSession[] = [];
    private currentSession: ChatSession | null = null;
    private eventEmitter: EventEmitter;
    private apiBaseUrl: string;
    private isCreatingSession: boolean = false;
    private isVerifyingSession: boolean = false;

    // DOM elements
    private chatHistory: HTMLElement;
    private newChatBtn: HTMLButtonElement;

    constructor(eventEmitter: EventEmitter, apiBaseUrl: string) {
        this.eventEmitter = eventEmitter;
        this.apiBaseUrl = apiBaseUrl;
        
        this.chatHistory = document.getElementById('chatHistory') as HTMLElement;
        this.newChatBtn = document.getElementById('newChatBtn') as HTMLButtonElement;

        this.setupEventListeners();
        this.loadChatHistory();
    }

    private setupEventListeners(): void {
        this.newChatBtn.addEventListener('click', () => {
            this.createNewSession();
        });
    }

    async init(): Promise<void> {
        // Only create a new session if no sessions exist
        if (this.sessions.length === 0) {
            await this.createNewSession();
        } else {
            // Load the most recent session
            this.currentSession = this.sessions[0];
            
            console.log('Loading existing session:', this.currentSession.sessionId);
            // If the session has a backend sessionId, verify it exists
            if (this.currentSession.sessionId) {
                this.isVerifyingSession = true;
                this.updateNewChatButtonState();
                this.showSessionVerificationLoading();
                await this.verifyBackendSession(this.currentSession.sessionId);
                this.isVerifyingSession = false;
                this.updateNewChatButtonState();
                this.hideSessionVerificationLoading();
            }
            
            await this.loadSession(this.currentSession.id);
        }
        
        this.renderChatHistory();
    }

    async createNewSession(): Promise<void> {
        if (this.isCreatingSession) return;
        
        this.isCreatingSession = true;
        this.updateNewChatButtonState();
        
        try {
            // Create a new backend session
            const response = await fetch(`${this.apiBaseUrl}/session/new`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to create session: ${response.status}`);
            }

            const sessionData = await response.json();
            
            const session: ChatSession = {
                id: this.generateId(),
                sessionId: sessionData.session_id,  // Backend session ID
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
            
            // Emit session changed event
            this.eventEmitter.emit('session-changed', { session });
            
        } catch (error) {
            console.error('Failed to create new session:', error);
            // Show error (this would need to be passed to chat component)
        } finally {
            this.isCreatingSession = false;
            this.updateNewChatButtonState();
        }
    }

    private async loadSession(sessionId: string): Promise<void> {
        const session = this.sessions.find(s => s.id === sessionId);
        if (!session) return;

        this.currentSession = session;
        this.renderChatHistory();
        
        // Emit session changed event
        this.eventEmitter.emit('session-changed', { session });
    }

    private async deleteSession(sessionId: string): Promise<void> {
        const sessionIndex = this.sessions.findIndex(s => s.id === sessionId);
        if (sessionIndex === -1) return;

        this.sessions.splice(sessionIndex, 1);
        
        // If we deleted the current session, switch to another or create new
        if (this.currentSession?.id === sessionId) {
            if (this.sessions.length > 0) {
                await this.loadSession(this.sessions[0].id);
            } else {
                await this.createNewSession();
            }
        }
        
        this.saveChatHistory();
        this.renderChatHistory();
    }

    getCurrentSession(): ChatSession | null {
        return this.currentSession;
    }

    updateSessionTitle(): void {
        if (!this.currentSession || this.currentSession.messages.length === 0) return;
        
        const firstMessage = this.currentSession.messages.find(m => m.role === 'user');
        if (firstMessage) {
            const title = firstMessage.content.substring(0, 50).trim();
            this.currentSession.title = title + (firstMessage.content.length > 50 ? '...' : '');
            this.saveChatHistory();
            this.renderChatHistory();
        }
    }

    addMessage(message: Message): void {
        if (this.currentSession) {
            this.currentSession.messages.push(message);
            this.saveChatHistory();
        }
    }

    private renderChatHistory(): void {
        this.chatHistory.innerHTML = '';
        
        this.sessions.forEach(session => {
            const chatItem = document.createElement('div');
            chatItem.className = 'chat-item';
            if (this.currentSession?.id === session.id) {
                chatItem.classList.add('active');
            }
            
            const chatTitle = document.createElement('span');
            chatTitle.className = 'chat-title';
            chatTitle.textContent = session.title;
            
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'chat-delete-btn';
            deleteBtn.innerHTML = '×';
            deleteBtn.onclick = (e) => {
                e.stopPropagation();
                this.deleteSession(session.id);
            };
            
            chatItem.appendChild(chatTitle);
            chatItem.appendChild(deleteBtn);
            
            chatItem.onclick = () => {
                if (this.currentSession?.id !== session.id) {
                    this.loadSession(session.id);
                }
            };
            
            this.chatHistory.appendChild(chatItem);
        });
    }

    private updateNewChatButtonState(): void {
        if (this.isCreatingSession || this.isVerifyingSession) {
            this.newChatBtn.disabled = true;
            this.newChatBtn.classList.add('loading');
        } else {
            this.newChatBtn.disabled = false;
            this.newChatBtn.classList.remove('loading');
        }
    }

    private saveChatHistory(): void {
        localStorage.setItem('chatSessions', JSON.stringify(this.sessions.map(session => ({
            ...session,
            createdAt: session.createdAt.toISOString()
        }))));
    }

    private loadChatHistory(): void {
        const saved = localStorage.getItem('chatSessions');
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                this.sessions = parsed.map((session: any) => ({
                    ...session,
                    createdAt: new Date(session.createdAt)
                }));
            } catch (error) {
                console.error('Failed to parse saved chat history:', error);
                this.sessions = [];
            }
        }
    }

    private generateId(): string {
        return Math.random().toString(36).substring(2) + Date.now().toString(36);
    }

    private async verifyBackendSession(sessionId: string): Promise<void> {
        try {
            const response = await fetch(`${this.apiBaseUrl}/${sessionId}/verify`, {
                headers: {
                    'X-API-Key': 'test_12345'
                }
            });

            if (response.ok) {
                console.log('Session verified successfully');
                // Session exists and is reinitialized
            } else {
                console.warn('Session verification failed, creating new session');
                if (this.currentSession) {
                    this.currentSession.sessionId = undefined;
                    this.saveChatHistory();
                }
                await this.createNewSession();
            }
        } catch (error) {
            console.error('Session verification error:', error);
            if (this.currentSession) {
                this.currentSession.sessionId = undefined;
                this.saveChatHistory();
            }
        }
    }

    private showSessionVerificationLoading(): void {
        // This would be implemented to show loading state
        console.log('Showing session verification loading...');
    }

    private hideSessionVerificationLoading(): void {
        // This would be implemented to hide loading state
        console.log('Hiding session verification loading...');
    }

    // Debug state management per session
    getCurrentDebugPanelState(): boolean {
        return this.currentSession?.debugPanelOpen ?? false;
    }

    setCurrentDebugPanelState(open: boolean): void {
        if (this.currentSession) {
            this.currentSession.debugPanelOpen = open;
            this.saveChatHistory();
        }
    }

    getCurrentDebugEnabled(): boolean {
        return this.currentSession?.debugEnabled ?? false;
    }

    setCurrentDebugEnabled(enabled: boolean): void {
        if (this.currentSession) {
            this.currentSession.debugEnabled = enabled;
            this.saveChatHistory();
        }
    }

    getIsCreatingSession(): boolean {
        return this.isCreatingSession;
    }

    getIsVerifyingSession(): boolean {
        return this.isVerifyingSession;
    }
}