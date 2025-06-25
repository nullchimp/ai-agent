import { ChatSession } from './types';

export class SessionUIService {
    private chatHistory: HTMLElement;
    private newChatBtn: HTMLButtonElement;

    constructor(chatHistory: HTMLElement, newChatBtn: HTMLButtonElement) {
        this.chatHistory = chatHistory;
        this.newChatBtn = newChatBtn;
    }

    renderChatHistory(
        sessions: ChatSession[], 
        currentSession: ChatSession | null,
        onLoadSession: (sessionId: string) => Promise<void>,
        onDeleteSession: (sessionId: string) => Promise<void>
    ): void {
        this.chatHistory.innerHTML = '';
        
        if (sessions.length === 0) {
            const emptyState = document.createElement('div');
            emptyState.className = 'empty-history';
            emptyState.innerHTML = `
                <div class="empty-history-message">
                    No chat history yet. Start a new conversation!
                </div>
            `;
            this.chatHistory.appendChild(emptyState);
            return;
        }
        
        sessions.forEach(session => {
            const sessionEl = document.createElement('div');
            sessionEl.className = `chat-history-item ${currentSession?.id === session.id ? 'active' : ''}`;
            
            const sessionContent = document.createElement('div');
            sessionContent.className = 'session-content';
            sessionContent.addEventListener('click', () => {
                if (currentSession?.id !== session.id) {
                    onLoadSession(session.id);
                }
            });
            
            const sessionTitle = document.createElement('div');
            sessionTitle.className = 'session-title';
            sessionTitle.textContent = session.title;
            
            const sessionDate = document.createElement('div');
            sessionDate.className = 'session-date';
            sessionDate.textContent = new Date(session.createdAt).toLocaleDateString();
            
            sessionContent.appendChild(sessionTitle);
            sessionContent.appendChild(sessionDate);
            
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-session-btn';
            deleteBtn.innerHTML = '×';
            deleteBtn.title = 'Delete session';
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                onDeleteSession(session.id);
            });
            
            sessionEl.appendChild(sessionContent);
            sessionEl.appendChild(deleteBtn);
            
            this.chatHistory.appendChild(sessionEl);
        });
    }

    updateNewChatButtonState(isCreatingSession: boolean): void {
        this.newChatBtn.disabled = isCreatingSession;
        const span = this.newChatBtn.querySelector('span');
        if (span) {
            span.textContent = isCreatingSession ? 'Creating...' : 'New chat';
        }
    }

    showEmptyState(): void {
        const messagesContainer = document.getElementById('messagesContainer');
        if (messagesContainer) {
            messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <h2>Welcome to AI Assistant</h2>
                    <p>Start a conversation by typing a message below.</p>
                </div>
            `;
        }
    }

    showSessionVerificationLoading(): void {
        const messagesContainer = document.getElementById('messagesContainer');
        if (messagesContainer) {
            messagesContainer.innerHTML = `
                <div class="session-loading">
                    <div class="loading-spinner"></div>
                    <span>Verifying session...</span>
                </div>
            `;
        }
    }

    hideSessionVerificationLoading(): void {
        const sessionLoading = document.querySelector('.session-loading');
        if (sessionLoading) {
            sessionLoading.remove();
        }
    }
}