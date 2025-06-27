import { Message } from '../types';

declare const marked: {
    parse(markdown: string): string;
};

export class ChatUIManager {
    private messagesContainer: HTMLElement;

    constructor() {
        this.messagesContainer = document.getElementById('messagesContainer') as HTMLElement;
    }

    public displayMessage(message: Message): void {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${message.role}`;
        messageEl.innerHTML = `
            <div class="message-avatar">${message.role === 'user' ? 'U' : 'AI'}</div>
            <div class="message-content">
                ${message.role === 'assistant' && message.usedTools && message.usedTools.length > 0 ?
                    `<div class="tool-tags">${message.usedTools.map(tool => `<span class="tool-tag">${tool.toLowerCase()}</span>`).join('')}</div>` : ''
                }
                <div class="message-text">${message.role === 'assistant' ? marked.parse(message.content) : this.escapeHtml(message.content)}</div>
            </div>
        `;
        this.hideWelcomeMessage();
        this.messagesContainer.appendChild(messageEl);
        this.scrollToBottom();
    }

    public showTypingIndicator(): void {
        const typingEl = document.createElement('div');
        typingEl.className = 'message assistant';
        typingEl.id = 'typingIndicator';
        typingEl.innerHTML = `
            <div class="message-avatar">AI</div>
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>
                </div>
            </div>
        `;
        this.hideWelcomeMessage();
        this.messagesContainer.appendChild(typingEl);
        this.scrollToBottom();
    }

    public hideTypingIndicator(): void {
        document.getElementById('typingIndicator')?.remove();
    }

    public clearMessages(): void {
        this.messagesContainer.innerHTML = '';
    }

    public showWelcomeMessage(): void {
        this.messagesContainer.innerHTML = `
            <div class="welcome-message">
                <h1>AI Agent</h1>
                <p>How can I help you today?</p>
            </div>`;
    }

    public showEmptyState(onCreateNew: () => void): void {
        this.messagesContainer.innerHTML = `
            <div class="welcome-message empty-state">
                <h1>AI Agent</h1>
                <p>No active chat sessions.</p>
                <p>Click <span class="new-chat-link" id="newChatLink">New chat</span> to start a conversation.</p>
            </div>`;
        document.getElementById('newChatLink')?.addEventListener('click', onCreateNew);
    }

    public showLoadingState(message: string, details: string): void {
        this.messagesContainer.innerHTML = `
            <div class="welcome-message">
                <div class="session-loading">
                    <div class="loading-spinner"></div>
                    <h1>${message}</h1>
                    <p>${details}</p>
                </div>
            </div>`;
    }

    public showError(message: string): void {
        const errorEl = document.createElement('div');
        errorEl.className = 'error-message';
        errorEl.textContent = message;
        this.messagesContainer.appendChild(errorEl);
        this.scrollToBottom();
        setTimeout(() => errorEl.remove(), 5000);
    }

    private hideWelcomeMessage(): void {
        this.messagesContainer.querySelector('.welcome-message')?.remove();
    }

    private scrollToBottom(): void {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    private escapeHtml(unsafe: string): string {
        return unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }
}
