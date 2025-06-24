// Type declaration for marked library
declare const marked: {
    parse(markdown: string): string;
};

interface Message {
    id: string;
    content: string;
    role: 'user' | 'assistant';
    timestamp: Date;
    usedTools?: string[];
}

interface Tool {
    name: string;
    description: string;
    enabled: boolean;
    parameters: Record<string, any>;
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
    private toolsHeader: HTMLElement;
    private toolsList: HTMLElement;
    private currentSession: ChatSession | null = null;
    private sessions: ChatSession[] = [];
    private tools: Tool[] = [];

    private apiBaseUrl = 'http://localhost:5555/api';

    constructor() {
        this.messagesContainer = document.getElementById('messagesContainer') as HTMLElement;
        this.messageInput = document.getElementById('messageInput') as HTMLTextAreaElement;
        this.sendBtn = document.getElementById('sendBtn') as HTMLButtonElement;
        this.chatHistory = document.getElementById('chatHistory') as HTMLElement;
        this.newChatBtn = document.getElementById('newChatBtn') as HTMLButtonElement;
        this.toolsHeader = document.getElementById('toolsHeader') as HTMLElement;
        this.toolsList = document.getElementById('toolsList') as HTMLElement;

        this.init();
    }

    private async init(): Promise<void> {
        this.loadChatHistory();
        this.setupEventListeners();
        await this.loadTools();
        
        // Only create a new session if no sessions exist
        if (this.sessions.length === 0) {
            this.createNewSession();
        } else {
            // Load the most recent session
            this.currentSession = this.sessions[0];
            this.loadSession(this.currentSession.id);
        }
        
        this.renderChatHistory();
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

        this.toolsHeader.addEventListener('click', () => this.toggleToolsSection());
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
            const apiResponse = await this.callAPI(content);
            this.hideTypingIndicator();

            const assistantMessage: Message = {
                id: this.generateId(),
                content: apiResponse.response,
                role: 'assistant',
                timestamp: new Date(),
                usedTools: apiResponse.usedTools
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

    private async callAPI(message: string): Promise<{response: string, usedTools: string[]}> {
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
            console.log('API Response Data:', data); // Debug log
            return {
                response: data.response || 'Sorry, I couldn\'t process your request.',
                usedTools: data.used_tools || []
            };
        } catch (error) {
            console.error('API call failed:', error);
            return {
                response: 'An error occurred while communicating with the AI.',
                usedTools: []
            };
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

        // Add tool tags at the top for assistant messages
        if (message.role === 'assistant' && message.usedTools && message.usedTools.length > 0) {
            console.log('Adding tool tags:', message.usedTools); // Debug log
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
            
            const title = document.createElement('span');
            title.className = 'chat-title';
            title.textContent = session.title;
            title.addEventListener('click', () => this.loadSession(session.id));
            
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'chat-delete-btn';
            deleteBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <polyline points="3,6 5,6 21,6"></polyline>
                    <path d="M19,6V20a2,2,0,0,1-2,2H7a2,2,0,0,1-2-2V6M8,6V4a2,2,0,0,1,2-2h4a2,2,0,0,1,2,2V6"></path>
                    <line x1="10" y1="11" x2="10" y2="17"></line>
                    <line x1="14" y1="11" x2="14" y2="17"></line>
                </svg>
            `;
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.deleteSession(session.id);
            });
            
            item.appendChild(title);
            item.appendChild(deleteBtn);
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

    private deleteSession(sessionId: string): void {
        const sessionIndex = this.sessions.findIndex(s => s.id === sessionId);
        if (sessionIndex === -1) return;
        
        // Remove the session from the array
        this.sessions.splice(sessionIndex, 1);
        
        // If we deleted the current session, switch to another one or create new
        if (this.currentSession?.id === sessionId) {
            if (this.sessions.length > 0) {
                // Load the first available session
                this.currentSession = this.sessions[0];
                this.loadSession(this.currentSession.id);
            } else {
                // No sessions left, create a new one
                this.createNewSession();
                return; // createNewSession already saves and renders
            }
        }
        
        this.saveChatHistory();
        this.renderChatHistory();
    }

    // Tool management methods
    private async loadTools(): Promise<void> {
        try {
            const response = await fetch(`${this.apiBaseUrl}/tools`, {
                headers: {
                    'X-API-Key': 'test_12345'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.tools = data.tools || [];
                this.renderTools();
            }
        } catch (error) {
            console.error('Failed to load tools:', error);
        }
    }

    private toggleToolsSection(): void {
        const isExpanded = this.toolsHeader.classList.contains('expanded');
        
        if (isExpanded) {
            this.toolsHeader.classList.remove('expanded');
            this.toolsList.classList.remove('expanded');
        } else {
            this.toolsHeader.classList.add('expanded');
            this.toolsList.classList.add('expanded');
        }
    }

    private renderTools(): void {
        this.toolsList.innerHTML = '';
        
        // Add toggle all item at the top
        const toggleAllItem = document.createElement('div');
        toggleAllItem.className = 'disable-all-item';
        
        const toggleAllName = document.createElement('div');
        toggleAllName.className = 'disable-all-name';
        toggleAllName.textContent = 'Toggle All Tools';
        
        const toggleAllDescription = document.createElement('div');
        toggleAllDescription.className = 'disable-all-description';
        toggleAllDescription.textContent = 'Enable or disable all tools at once';
        
        const enabledCount = this.tools.filter(tool => tool.enabled).length;
        const totalCount = this.tools.length;
        const allEnabled = enabledCount === totalCount;
        
        // Update the tools configuration text to show active/total format
        const toolsLabelSpan = this.toolsHeader.querySelector('.tools-label span');
        if (toolsLabelSpan) {
            toolsLabelSpan.textContent = `Tools Configuration [${enabledCount}/${totalCount}]`;
        }
        
        const toggleAllToggle = document.createElement('div');
        toggleAllToggle.className = `tool-toggle ${allEnabled ? 'enabled' : ''}`;
        toggleAllToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleAllTools(!allEnabled);
        });
        
        toggleAllItem.appendChild(toggleAllName);
        toggleAllItem.appendChild(toggleAllDescription);
        toggleAllItem.appendChild(toggleAllToggle);
        
        this.toolsList.appendChild(toggleAllItem);
        
        // Sort tools alphabetically by name
        const sortedTools = [...this.tools].sort((a, b) => a.name.localeCompare(b.name));
        
        sortedTools.forEach(tool => {
            const toolItem = document.createElement('div');
            toolItem.className = 'tool-item';
            
            const toolName = document.createElement('div');
            toolName.className = 'tool-name';
            toolName.textContent = tool.name;
            
            const toolDescription = document.createElement('div');
            toolDescription.className = 'tool-description';
            toolDescription.textContent = tool.description;
            toolDescription.title = tool.description; // Show full description on hover
            
            const toolToggle = document.createElement('div');
            toolToggle.className = `tool-toggle ${tool.enabled ? 'enabled' : ''}`;
            toolToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleTool(tool.name, !tool.enabled);
            });
            
            toolItem.appendChild(toolName);
            toolItem.appendChild(toolDescription);
            toolItem.appendChild(toolToggle);
            
            this.toolsList.appendChild(toolItem);
        });
    }

    private async toggleTool(toolName: string, enabled: boolean): Promise<void> {
        try {
            const response = await fetch(`${this.apiBaseUrl}/tools/toggle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': 'test_12345'
                },
                body: JSON.stringify({
                    tool_name: toolName,
                    enabled: enabled
                })
            });

            if (response.ok) {
                // Update the local tool state
                const tool = this.tools.find(t => t.name === toolName);
                if (tool) {
                    tool.enabled = enabled;
                    this.renderTools();
                }
            } else {
                console.error('Failed to toggle tool:', await response.text());
            }
        } catch (error) {
            console.error('Error toggling tool:', error);
        }
    }

    private async toggleAllTools(enabled: boolean): Promise<void> {
        const toolsToChange = this.tools.filter(tool => tool.enabled !== enabled);
        
        for (const tool of toolsToChange) {
            try {
                const response = await fetch(`${this.apiBaseUrl}/tools/toggle`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-API-Key': 'test_12345'
                    },
                    body: JSON.stringify({
                        tool_name: tool.name,
                        enabled: enabled
                    })
                });

                if (response.ok) {
                    tool.enabled = enabled;
                } else {
                    console.error(`Failed to ${enabled ? 'enable' : 'disable'} tool ${tool.name}:`, await response.text());
                }
            } catch (error) {
                console.error(`Error ${enabled ? 'enabling' : 'disabling'} tool ${tool.name}:`, error);
            }
        }
        
        this.renderTools();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
