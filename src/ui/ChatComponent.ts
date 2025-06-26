class ChatComponent {
    private eventEmitter: EventEmitter;
    private apiBaseUrl: string;
    private currentSession: ChatSession | null = null;
    private isSendingMessage: boolean = false;
    private sessionComponent: SessionComponent;
    private toolsComponent: ToolsComponent;
    private debugComponent: DebugComponent;

    // DOM elements
    private messagesContainer: HTMLElement;
    private messageInput: HTMLTextAreaElement;
    private sendBtn: HTMLButtonElement;

    constructor(
        eventEmitter: EventEmitter, 
        apiBaseUrl: string,
        sessionComponent: SessionComponent,
        toolsComponent: ToolsComponent,
        debugComponent: DebugComponent
    ) {
        this.eventEmitter = eventEmitter;
        this.apiBaseUrl = apiBaseUrl;
        this.sessionComponent = sessionComponent;
        this.toolsComponent = toolsComponent;
        this.debugComponent = debugComponent;
        
        this.messagesContainer = document.getElementById('messagesContainer') as HTMLElement;
        this.messageInput = document.getElementById('messageInput') as HTMLTextAreaElement;
        this.sendBtn = document.getElementById('sendBtn') as HTMLButtonElement;

        this.setupEventListeners();
    }

    private setupEventListeners(): void {
        this.sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });

        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        this.messageInput.addEventListener('input', () => {
            this.adjustTextareaHeight();
        });

        // Listen for session changes
        this.eventEmitter.on('session-changed', ({ session }) => {
            this.currentSession = session;
            this.clearMessages();
            
            session.messages.forEach(message => {
                this.displayMessage(message);
            });

            this.enableInput();
        });

        // Listen for debug state changes to reload debug events
        this.eventEmitter.on('debug-state-changed', ({ enabled }) => {
            if (enabled && this.debugComponent.getCurrentDebugEnabled()) {
                this.debugComponent.loadDebugEvents();
            }
        });
    }

    private adjustTextareaHeight(): void {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
    }

    private updateSendButtonState(): void {
        const hasText = this.messageInput.value.trim().length > 0;
        const canSend = hasText && 
                       !this.isSendingMessage && 
                       !this.sessionComponent.getIsCreatingSession() && 
                       !this.toolsComponent.getIsLoadingTools() &&
                       this.currentSession?.sessionId;
        
        this.sendBtn.disabled = !canSend;
        
        if (this.isSendingMessage) {
            this.messageInput.disabled = true;
            this.messageInput.classList.add('loading');
        } else {
            this.messageInput.disabled = false;
            this.messageInput.classList.remove('loading');
        }
    }

    private async sendMessage(): Promise<void> {
        const messageText = this.messageInput.value.trim();
        if (!messageText || this.isSendingMessage || !this.currentSession?.sessionId) {
            return;
        }

        this.isSendingMessage = true;
        this.updateSendButtonState();
        
        // Create user message
        const userMessage: Message = {
            id: this.generateId(),
            content: messageText,
            role: 'user',
            timestamp: new Date()
        };

        // Display user message immediately
        this.displayMessage(userMessage);
        this.sessionComponent.addMessage(userMessage);
        
        // Clear input
        this.messageInput.value = '';
        this.adjustTextareaHeight();
        
        // Show typing indicator
        this.showTypingIndicator();

        try {
            // Call API
            const apiResponse = await this.callAPI(messageText);
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Create assistant message
            const assistantMessage: Message = {
                id: this.generateId(),
                content: apiResponse.response,
                role: 'assistant',
                timestamp: new Date(),
                usedTools: apiResponse.usedTools
            };

            this.sessionComponent.addMessage(assistantMessage);
            this.displayMessage(assistantMessage);
            this.sessionComponent.updateSessionTitle();
            
            // Load debug events after message processing
            if (this.debugComponent.getCurrentDebugEnabled()) {
                this.debugComponent.loadDebugEvents();
            }

            // Emit message sent event
            this.eventEmitter.emit('message-sent', { message: assistantMessage });
            
        } catch (error) {
            this.hideTypingIndicator();
            this.showError('Failed to get response. Please try again.');
            console.error('API Error:', error);
        } finally {
            this.isSendingMessage = false;
            this.updateSendButtonState();
        }
    }

    private async callAPI(message: string): Promise<{response: string, usedTools: string[]}> {
        if (!this.currentSession?.sessionId) {
            throw new Error('No active session');
        }

        const requestBody = { message };
        console.log('Sending API request:', requestBody);

        const response = await fetch(`${this.apiBaseUrl}/${this.currentSession.sessionId}/message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': 'test_12345'
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            throw new Error(`API request failed: ${response.status}`);
        }

        const data = await response.json();
        console.log('API Response Data:', data);

        return {
            response: data.response || 'No response received',
            usedTools: data.used_tools || []
        };
    }

    private displayMessage(message: Message): void {
        const messageEl = document.createElement('div');
        messageEl.className = `message ${message.role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = message.role === 'user' ? 'U' : 'AI';
        
        const content = document.createElement('div');
        content.className = 'message-content';

        // Add tool tags at the top for assistant messages
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
            // Render markdown for assistant messages
            text.innerHTML = marked.parse(message.content);
        } else {
            // Keep user messages as plain text for security
            text.textContent = message.content;
        }
        
        content.appendChild(text);
        
        messageEl.appendChild(avatar);
        messageEl.appendChild(content);
        
        this.hideWelcomeMessage();
        this.messagesContainer.appendChild(messageEl);
        this.scrollToBottom();
    }

    private showTypingIndicator(): void {
        // Remove any existing typing indicator
        this.hideTypingIndicator();
        
        const typingEl = document.createElement('div');
        typingEl.className = 'message assistant typing-indicator-message';
        typingEl.id = 'typingIndicator';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = 'AI';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        
        content.appendChild(indicator);
        typingEl.appendChild(avatar);
        typingEl.appendChild(content);
        
        this.messagesContainer.appendChild(typingEl);
        this.scrollToBottom();

        // Emit typing indicator event
        this.eventEmitter.emit('typing-indicator', { show: true });
    }

    private hideTypingIndicator(): void {
        const typingEl = document.getElementById('typingIndicator');
        if (typingEl) {
            typingEl.remove();
        }

        // Emit typing indicator event
        this.eventEmitter.emit('typing-indicator', { show: false });
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

    clearMessages(): void {
        // Clear all messages except welcome message
        const welcomeMessage = this.messagesContainer.querySelector('.welcome-message');
        this.messagesContainer.innerHTML = '';
        if (welcomeMessage) {
            this.messagesContainer.appendChild(welcomeMessage);
            (welcomeMessage as HTMLElement).style.display = 'block';
        }
    }

    private enableInput(): void {
        this.messageInput.disabled = false;
        this.messageInput.classList.remove('loading');
        this.updateSendButtonState();
    }

    private generateId(): string {
        return Math.random().toString(36).substring(2) + Date.now().toString(36);
    }

    // Public methods
    focusInput(): void {
        this.messageInput.focus();
    }

    getIsSendingMessage(): boolean {
        return this.isSendingMessage;
    }

    // Call this method whenever state changes that might affect send button
    updateButtonStates(): void {
        this.updateSendButtonState();
    }
}