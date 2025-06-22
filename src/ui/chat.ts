interface Message {
    id: string;
    content: string;
    role: 'user' | 'assistant';
    timestamp: Date;
}

interface ChatSession {
    id: string;
    title: string;
    messages: Message[];
    createdAt: Date;
}

class ChatApp {
    private messagesContainer: HTMLElement;
    private messageInput: HTMLTextAreaElement;
    private sendBtn: HTMLButtonElement;
    private chatHistory: HTMLElement;
    private newChatBtn: HTMLButtonElement;
    private currentSession: ChatSession | null = null;
    private sessions: ChatSession[] = [];

    private apiBaseUrl = 'http://localhost:5555/api';

    constructor() {
        this.messagesContainer = document.getElementById('messagesContainer') as HTMLElement;
        this.messageInput = document.getElementById('messageInput') as HTMLTextAreaElement;
        this.sendBtn = document.getElementById('sendBtn') as HTMLButtonElement;
        this.chatHistory = document.getElementById('chatHistory') as HTMLElement;
        this.newChatBtn = document.getElementById('newChatBtn') as HTMLButtonElement;

        this.init();
    }

    private init(): void {
        this.loadChatHistory();
        this.setupEventListeners();
        this.createNewSession();
    }

    private setupEventListeners(): void {
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        this.messageInput.addEventListener('input', () => {
            this.adjustTextareaHeight();
            this.updateSendButtonState();
        });

        this.newChatBtn.addEventListener('click', () => this.createNewSession());
    }

    private adjustTextareaHeight(): void {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    private updateSendButtonState(): void {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendBtn.disabled = !hasText;
    }

    private async sendMessage(): Promise<void> {
        const content = this.messageInput.value.trim();
        if (!content || !this.currentSession) return;

        const userMessage: Message = {
            id: this.generateId(),
            content,
            role: 'user',
            timestamp: new Date()
        };

        this.currentSession.messages.push(userMessage);
        this.displayMessage(userMessage);
        this.messageInput.value = '';
        this.adjustTextareaHeight();
        this.updateSendButtonState();

        this.showTypingIndicator();

        try {
            const response = await this.callAPI(content);
            this.hideTypingIndicator();

            const assistantMessage: Message = {
                id: this.generateId(),
                content: response,
                role: 'assistant',
                timestamp: new Date()
            };

            this.currentSession.messages.push(assistantMessage);
            this.displayMessage(assistantMessage);
            this.updateSessionTitle();
            this.saveChatHistory();
            this.renderChatHistory();
        } catch (error) {
            this.hideTypingIndicator();
            this.showError('Failed to get response. Please try again.');
            console.error('API Error:', error);
        }
    }

    private async callAPI(message: string): Promise<string> {
        try {
            const response = await fetch(`${this.apiBaseUrl}/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': 'test_12345'
                },
                body: JSON.stringify({ query: message })
            });

            console.log('API response status:', response);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data.response || 'Sorry, I couldn\'t process your request.';
        } catch (error) {
            console.error('API call failed:', error);
            return 'An error occurred while communicating with the AI.';
        }
    }

    private displayMessage(message: Message): void {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${message.role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = message.role === 'user' ? 'U' : 'AI';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const text = document.createElement('div');
        text.className = 'message-text';
        text.textContent = message.content;
        
        content.appendChild(text);
        messageEl.appendChild(avatar);
        messageEl.appendChild(content);
        
        this.hideWelcomeMessage();
        this.messagesContainer.appendChild(messageEl);
        this.scrollToBottom();
    }

    private showTypingIndicator(): void {
        const typingEl = document.createElement('div');
        typingEl.className = 'message assistant';
        typingEl.id = 'typingIndicator';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = 'AI';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            indicator.appendChild(dot);
        }
        
        content.appendChild(indicator);
        typingEl.appendChild(avatar);
        typingEl.appendChild(content);
        
        this.hideWelcomeMessage();
        this.messagesContainer.appendChild(typingEl);
        this.scrollToBottom();
    }

    private hideTypingIndicator(): void {
        const typingEl = document.getElementById('typingIndicator');
        if (typingEl) {
            typingEl.remove();
        }
    }

    private hideWelcomeMessage(): void {
        const welcomeEl = this.messagesContainer.querySelector('.welcome-message') as HTMLElement;
        if (welcomeEl) {
            welcomeEl.style.display = 'none';
        }
    }

    private showError(message: string): void {
        const errorEl = document.createElement('div');
        errorEl.className = 'error-message';
        errorEl.textContent = message;
        this.messagesContainer.appendChild(errorEl);
        this.scrollToBottom();
        
        setTimeout(() => {
            errorEl.remove();
        }, 5000);
    }

    private scrollToBottom(): void {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    private createNewSession(): void {
        const session: ChatSession = {
            id: this.generateId(),
            title: 'New Chat',
            messages: [],
            createdAt: new Date()
        };

        this.sessions.unshift(session);
        this.currentSession = session;
        this.clearMessages();
        this.renderChatHistory();
        this.saveChatHistory();
        this.messageInput.focus();
    }

    private clearMessages(): void {
        this.messagesContainer.innerHTML = `
            <div class="welcome-message">
                <h1>AI Agent</h1>
                <p>How can I help you today?</p>
            </div>
        `;
    }

    private updateSessionTitle(): void {
        if (!this.currentSession || this.currentSession.messages.length === 0) return;

        const firstUserMessage = this.currentSession.messages.find(m => m.role === 'user');
        if (firstUserMessage && this.currentSession.title === 'New Chat') {
            this.currentSession.title = firstUserMessage.content.substring(0, 50) + 
                (firstUserMessage.content.length > 50 ? '...' : '');
            this.renderChatHistory();
            this.saveChatHistory();
        }
    }

    private renderChatHistory(): void {
        this.chatHistory.innerHTML = '';
        
        this.sessions.forEach(session => {
            const item = document.createElement('div');
            item.className = 'chat-item';
            if (session.id === this.currentSession?.id) {
                item.classList.add('active');
            }
            item.textContent = session.title;
            item.addEventListener('click', () => this.loadSession(session.id));
            this.chatHistory.appendChild(item);
        });
    }

    private loadSession(sessionId: string): void {
        const session = this.sessions.find(s => s.id === sessionId);
        if (!session) return;

        this.currentSession = session;
        this.clearMessages();
        
        session.messages.forEach(message => {
            this.displayMessage(message);
        });

        this.renderChatHistory();
    }

    private saveChatHistory(): void {
        localStorage.setItem('chatSessions', JSON.stringify(this.sessions));
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

document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
