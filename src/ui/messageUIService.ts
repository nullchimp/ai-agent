import { Message } from './types';

declare const marked: {
    parse(markdown: string): string;
};

export class MessageUIService {
    private messagesContainer: HTMLElement;

    constructor(messagesContainer: HTMLElement) {
        this.messagesContainer = messagesContainer;
    }

    displayMessage(message: Message): void {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${message.role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = message.role === 'user' ? 'U' : 'AI';
        
        const content = document.createElement('div');
        content.className = 'message-content';

        if (message.role === 'assistant' && message.usedTools && message.usedTools.length > 0) {
            console.log('Adding tool tags:', message.usedTools);
            const toolsContainer = document.createElement('div');
            toolsContainer.className = 'tool-tags';
            
            message.usedTools.forEach(tool => {
                const toolTag = document.createElement('span');
                toolTag.className = 'tool-tag';
                toolTag.textContent = tool.toLowerCase();
                toolsContainer.appendChild(toolTag);
            });
            
            content.appendChild(toolsContainer);
        }
        
        const text = document.createElement('div');
        text.className = 'message-text';
        
        if (message.role === 'assistant') {
            text.innerHTML = marked.parse(message.content);
        } else {
            text.textContent = message.content;
        }
        
        content.appendChild(text);
        messageEl.appendChild(avatar);
        messageEl.appendChild(content);
        
        this.hideWelcomeMessage();
        this.messagesContainer.appendChild(messageEl);
        this.scrollToBottom();
    }

    showTypingIndicator(): void {
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

    hideTypingIndicator(): void {
        const typingEl = document.getElementById('typingIndicator');
        if (typingEl) {
            typingEl.remove();
        }
    }

    showError(message: string): void {
        const errorEl = document.createElement('div');
        errorEl.className = 'error-message';
        errorEl.textContent = message;
        this.messagesContainer.appendChild(errorEl);
        this.scrollToBottom();
        
        setTimeout(() => {
            errorEl.remove();
        }, 5000);
    }

    clearMessages(): void {
        this.messagesContainer.innerHTML = `
            <div class="welcome-message">
                <h2>Welcome to AI Assistant</h2>
                <p>Start a conversation by typing a message below.</p>
            </div>
        `;
    }

    private hideWelcomeMessage(): void {
        const welcomeEl = this.messagesContainer.querySelector('.welcome-message') as HTMLElement;
        if (welcomeEl) {
            welcomeEl.style.display = 'none';
        }
    }

    private scrollToBottom(): void {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
}