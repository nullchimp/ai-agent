// Import service modules
import { ApiService } from './apiService.js';
import { ChatService } from './chatService.js';
import { Utils } from './utils.js';

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
    source: string;
    parameters: Record<string, any>;
}

interface ChatSession {
    id: string;
    sessionId?: string;  // Backend session ID (optional for backward compatibility)
    title: string;
    messages: Message[];
    createdAt: Date;
    debugPanelOpen?: boolean;  // Debug panel state per session
    debugEnabled?: boolean;    // Debug enabled state per session
}

interface DebugEvent {
    event_type: string;
    message: string;
    data: Record<string, any>;
    timestamp: string;
    session_id?: string;
}

interface DebugInfo {
    events: DebugEvent[];
    enabled: boolean;
}

class ChatApp {
    // DOM elements
    private messagesContainer: HTMLElement;
    private messageInput: HTMLTextAreaElement;
    private sendBtn: HTMLButtonElement;
    private chatHistory: HTMLElement;
    private newChatBtn: HTMLButtonElement;
    private toolsHeader: HTMLElement;
    private toolsList: HTMLElement;
    private debugPanelToggle: HTMLButtonElement;
    private debugPanelOverlay: HTMLElement;
    private debugEventsContainer: HTMLElement;
    private debugClearBtn: HTMLButtonElement;
    private debugPanelClose: HTMLButtonElement;
    private debugFullscreenOverlay: HTMLElement;
    private debugFullscreenData: HTMLElement;
    private debugFullscreenTitle: HTMLElement;
    private debugFullscreenClose: HTMLButtonElement;
    
    // Services
    private apiService: ApiService;
    private chatService: ChatService;
    
    // UI state
    private currentSession: ChatSession | null = null;
    private tools: Tool[] = [];
    private debugEventsList: DebugEvent[] = [];
    private isCreatingSession: boolean = false;
    private isLoadingTools: boolean = false;
    private isSendingMessage: boolean = false;
    private isVerifyingSession: boolean = false;
    private toolCategoryStates: Record<string, boolean> = {}; // Track collapse state per source

    constructor() {
        // Initialize DOM elements
        this.messagesContainer = document.getElementById('messagesContainer') as HTMLElement;
        this.messageInput = document.getElementById('messageInput') as HTMLTextAreaElement;
        this.sendBtn = document.getElementById('sendBtn') as HTMLButtonElement;
        this.chatHistory = document.getElementById('chatHistory') as HTMLElement;
        this.newChatBtn = document.getElementById('newChatBtn') as HTMLButtonElement;
        this.toolsHeader = document.getElementById('toolsHeader') as HTMLElement;
        this.toolsList = document.getElementById('toolsList') as HTMLElement;
        
        // Debug elements
        this.debugPanelToggle = document.getElementById('debugPanelToggle') as HTMLButtonElement;
        this.debugPanelOverlay = document.getElementById('debugPanelOverlay') as HTMLElement;
        this.debugEventsContainer = document.getElementById('debugEvents') as HTMLElement;
        this.debugClearBtn = document.getElementById('debugClearBtn') as HTMLButtonElement;
        this.debugPanelClose = document.getElementById('debugPanelClose') as HTMLButtonElement;
        
        // Debug fullscreen elements
        this.debugFullscreenOverlay = document.getElementById('debugFullscreenOverlay') as HTMLElement;
        this.debugFullscreenData = document.getElementById('debugFullscreenData') as HTMLElement;
        this.debugFullscreenTitle = document.getElementById('debugFullscreenTitle') as HTMLElement;
        this.debugFullscreenClose = document.getElementById('debugFullscreenClose') as HTMLButtonElement;

        // Initialize services
        this.apiService = new ApiService();
        this.chatService = new ChatService();

        this.init();
    }

    private async init(): Promise<void> {
        this.setupEventListeners();
        
        const sessions = this.chatService.getSessions();
        console.log('ChatApp initialized with', sessions.length, 'sessions loaded.');

        // Only create a new session if no sessions exist
        if (this.chatService.shouldCreateNewSession()) {
            await this.createNewSession();
        } else {
            // Load the most recent session
            this.currentSession = this.chatService.getMostRecentSession();
            
            console.log('Loading existing session:', this.currentSession?.sessionId);
            // If the session has a backend sessionId, verify it exists
            if (this.currentSession?.sessionId) {
                this.isVerifyingSession = true;
                this.updateSendButtonState();
                this.showSessionVerificationLoading();
                await this.verifyBackendSession(this.currentSession.sessionId);
                this.isVerifyingSession = false;
                this.updateSendButtonState();
                this.hideSessionVerificationLoading();
            }
            
            if (this.currentSession) {
                await this.loadSession(this.currentSession.id);
            }
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

        this.newChatBtn.addEventListener('click', () => {
            if (!this.isCreatingSession) {
                this.createNewSession();
            }
        });

        this.toolsHeader.addEventListener('click', () => this.toggleToolsSection());
        
        // Debug event listeners
        this.debugPanelToggle.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent triggering tools section toggle
            this.toggleDebugPanel();
        });
        this.debugPanelClose.addEventListener('click', () => this.closeDebugPanel());
        this.debugClearBtn.addEventListener('click', () => this.clearDebugEvents());
        
        // Debug fullscreen event listeners
        this.debugFullscreenClose.addEventListener('click', () => this.closeDebugFullscreen());
        this.debugFullscreenOverlay.addEventListener('click', (e) => {
            if (e.target === this.debugFullscreenOverlay) {
                this.closeDebugFullscreen();
            }
        });
        
        // Keyboard shortcut for closing fullscreen
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.debugFullscreenOverlay.classList.contains('active')) {
                this.closeDebugFullscreen();
            }
        });
    }

    private adjustTextareaHeight(): void {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    private updateSendButtonState(): void {
        const hasContent = this.messageInput.value.trim().length > 0;
        const hasActiveSession = this.currentSession !== null;
        const isLoading = this.isLoadingTools || this.isSendingMessage || this.isCreatingSession || this.isVerifyingSession;
        
        this.sendBtn.disabled = !hasContent || !hasActiveSession || isLoading;
        this.messageInput.disabled = isLoading;
        
        // Add visual feedback for loading state
        if (isLoading) {
            this.messageInput.placeholder = 'Please wait...';
            this.messageInput.classList.add('loading');
        } else {
            this.messageInput.placeholder = 'Type your message...';
            this.messageInput.classList.remove('loading');
        }
    }

    private updateNewChatButtonState(): void {
        const button = this.newChatBtn;
        const icon = button.querySelector('svg');
        const span = button.querySelector('span');
        
        if (this.isCreatingSession) {
            button.disabled = true;
            button.classList.add('loading');
            if (icon) {
                icon.style.display = 'none';
            }
            if (span) {
                span.textContent = 'Creating...';
            }
        } else {
            button.disabled = false;
            button.classList.remove('loading');
            if (icon) {
                icon.style.display = 'block';
            }
            if (span) {
                span.textContent = 'New chat';
            }
        }
    }

    private async sendMessage(): Promise<void> {
        const content = this.messageInput.value.trim();
        if (!content || !this.currentSession) return;

        // Validate message using the service
        const validation = this.chatService.validateMessage(content);
        if (!validation.isValid) {
            this.showError(validation.error || 'Invalid message');
            return;
        }

        this.isSendingMessage = true;
        this.updateSendButtonState();

        // If the current session doesn't have a backend session ID, create one
        if (!this.currentSession.sessionId) {
            console.log('Creating backend session for existing frontend session...');
            try {
                const backendSessionId = await this.apiService.createNewSession();
                this.chatService.updateSessionBackendId(this.currentSession, backendSessionId);
                console.log(`Created backend session: ${backendSessionId}`);
                // Reload tools for the new session
                await this.loadTools();
            } catch (error) {
                console.error('Failed to create backend session:', error);
                this.showError('Failed to create backend session. Please try again.');
                this.isSendingMessage = false;
                this.updateSendButtonState();
                return;
            }
        }

        // Create and add user message
        const userMessage = this.chatService.createMessage(content, 'user');
        this.chatService.addMessage(this.currentSession, userMessage);
        this.displayMessage(userMessage);
        this.renderChatHistory();
        
        this.messageInput.value = '';
        this.adjustTextareaHeight();
        this.updateSendButtonState();
        this.showTypingIndicator();

        try {
            console.log(`Sending message to session: ${this.currentSession.sessionId}`);
            const apiResponse = await this.apiService.callChatAPI(content, this.currentSession.sessionId!);
            this.hideTypingIndicator();

            const assistantMessage = this.chatService.createMessage(
                apiResponse.response, 
                'assistant', 
                apiResponse.usedTools
            );
            
            this.chatService.addMessage(this.currentSession, assistantMessage);
            this.displayMessage(assistantMessage);
            this.renderChatHistory();
            
            // Load debug events after message processing
            if (this.getCurrentDebugEnabled()) {
                this.loadDebugEvents();
            }
        } catch (error) {
            this.hideTypingIndicator();
            this.showError('Failed to get response. Please try again.');
            console.error('API Error:', error);
        } finally {
            this.isSendingMessage = false;
            this.updateSendButtonState();
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

    private async createNewSession(): Promise<void> {
        if (this.isCreatingSession) return;
        
        this.isCreatingSession = true;
        this.updateNewChatButtonState();
        this.updateSendButtonState();
        
        // Show loading state immediately
        this.clearMessages();
        
        try {
            // Create a new backend session
            const backendSessionId = await this.apiService.createNewSession();
            
            // Create the session using the service
            const session = this.chatService.createSession(backendSessionId);
            this.currentSession = session;
            this.renderChatHistory();
            
            // Re-enable input for the new session
            this.enableInput();
            
            // Reload tools for the new session
            await this.loadTools();
            // Restore debug state for the new session
            await this.restoreDebugState();
            
            // Focus input after everything is loaded
            this.messageInput.focus();
        } catch (error) {
            console.error('Failed to create new session:', error);
            this.showError('Failed to create new chat session. Please try again.');
        } finally {
            this.isCreatingSession = false;
            this.updateNewChatButtonState();
            this.updateSendButtonState();
            // Clear the loading message and show the normal welcome message
            this.clearMessages();
        }
    }

    private clearMessages(): void {
        if (this.isCreatingSession) {
            this.messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <div class="session-loading">
                        <div class="loading-spinner"></div>
                        <h1>Setting up your new chat...</h1>
                        <p>Initializing tools and preparing the session for you.</p>
                    </div>
                </div>
            `;
        } else if (!this.currentSession) {
            this.showEmptyState();
        } else {
            this.messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <h1>AI Agent</h1>
                    <p>How can I help you today?</p>
                </div>
            `;
        }
    }



    private renderChatHistory(): void {
        this.chatHistory.innerHTML = '';
        
        const sessions = this.chatService.getSessions();
        sessions.forEach(session => {
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
                </svg>
            `;
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

    private async loadSession(sessionId: string): Promise<void> {
        const session = this.chatService.getSessions().find(s => s.id === sessionId);
        if (!session) return;

        this.currentSession = session;
        this.clearMessages();
        
        session.messages.forEach(message => {
            this.displayMessage(message);
        });

        this.renderChatHistory();
        
        // Re-enable input for the loaded session
        this.enableInput();
        
        // Load tools for the current session
        await this.loadTools();
        
        // Restore debug panel state for this session
        await this.restoreDebugState();
    }

    private async restoreDebugState(): Promise<void> {
        if (!this.currentSession) return;
        
        const debugPanelShouldBeOpen = this.getCurrentDebugPanelState();
        
        // Update UI to match session state
        if (debugPanelShouldBeOpen) {
            this.debugPanelOverlay.classList.add('active');
            this.debugPanelToggle.classList.add('active');
            document.body.classList.add('debug-panel-open');
            
            // Load debug events and ensure debug mode is enabled
            await this.setDebugMode(true);
            await this.loadDebugEvents();
        } else {
            this.debugPanelOverlay.classList.remove('active');
            this.debugPanelToggle.classList.remove('active');
            document.body.classList.remove('debug-panel-open');
            
            // Ensure debug mode reflects session state
            const sessionDebugEnabled = this.getCurrentDebugEnabled();
            if (sessionDebugEnabled) {
                await this.setDebugMode(true);
            }
        }
    }



    private async deleteSession(sessionId: string): Promise<void> {
        const session = this.chatService.getSessionById(sessionId);
        if (!session) return;
        
        console.log(`Deleting session: frontend ID=${session.id}, backend ID=${session.sessionId}`);
        
        try {
            // Delete the backend session
            if (session.sessionId) {
                await this.apiService.deleteSession(session.sessionId);
                console.log(`Successfully deleted backend session ${session.sessionId}`);
            } else {
                console.log('No backend session ID to delete');
            }
        } catch (error) {
            console.error('Failed to delete backend session:', error);
            // Continue with frontend cleanup even if backend deletion fails
        }
        
        // Remove the session using the service
        const deletedSession = this.chatService.deleteSession(sessionId);
        
        // If we deleted the current session, switch to another one or show empty state
        if (this.currentSession?.id === sessionId) {
            const remainingSessions = this.chatService.getSessions();
            if (remainingSessions.length > 0) {
                // Load the first available session
                this.currentSession = remainingSessions[0];
                await this.loadSession(this.currentSession.id);
            } else {
                // No sessions left, show empty state
                this.currentSession = null;
                this.showEmptyState();
            }
        }
        
        this.renderChatHistory();
    }

    // Tool management methods
    private async loadTools(): Promise<void> {
        if (!this.currentSession?.sessionId) {
            console.log('No session ID available for loading tools');
            this.tools = [];
            this.renderTools();
            return;
        }

        this.isLoadingTools = true;
        this.renderToolsLoading();
        this.updateSendButtonState();

        try {
            this.tools = await this.apiService.loadTools(this.currentSession.sessionId);
            console.log(`Loaded ${this.tools.length} tools:`, this.tools.map(t => t.name));
        } catch (error) {
            console.error('Failed to load tools:', error);
            this.tools = [];
        } finally {
            this.isLoadingTools = false;
            this.renderTools();
            this.updateSendButtonState();
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

    private renderToolsLoading(): void {
        this.toolsList.innerHTML = `
            <div class="tools-loading">
                <div class="loading-spinner"></div>
                <span>Loading tools...</span>
            </div>
        `;
        
        // Update the tools configuration text to show loading state
        const toolsLabelSpan = this.toolsHeader.querySelector('.tools-label span');
        if (toolsLabelSpan) {
            toolsLabelSpan.textContent = 'Tools Configuration [Loading...]';
        }
    }

    private renderTools(): void {
        console.log('renderTools() called');
        this.toolsList.innerHTML = '';
        
        // Check if there's no active session
        if (!this.currentSession) {
            this.toolsList.innerHTML = `
                <div class="tools-no-session">
                    <div class="tools-no-session-message">
                        No active session. Create a new chat to configure tools.
                    </div>
                </div>
            `;
            
            // Update the tools configuration text to show no session state
            const toolsLabelSpan = this.toolsHeader.querySelector('.tools-label span');
            if (toolsLabelSpan) {
                toolsLabelSpan.textContent = 'Tools Configuration [No Session]';
            }
            return;
        }
        
        const enabledCount = this.tools.filter(tool => tool.enabled).length;
        const totalCount = this.tools.length;
        
        // Update the tools configuration text to show active/total format
        const toolsLabelSpan = this.toolsHeader.querySelector('.tools-label span');
        if (toolsLabelSpan) {
            toolsLabelSpan.textContent = `Tools Configuration [${enabledCount}/${totalCount}]`;
        }
        
        // Group tools by source
        const toolsBySource = this.tools.reduce((groups, tool) => {
            const source = tool.source || 'default';
            if (!groups[source]) {
                groups[source] = [];
            }
            groups[source].push(tool);
            return groups;
        }, {} as Record<string, Tool[]>);
        
        // Sort sources - 'default' first, then alphabetically
        const sortedSources = Object.keys(toolsBySource).sort((a, b) => {
            if (a === 'default') return -1;
            if (b === 'default') return 1;
            return a.localeCompare(b);
        });
        
        sortedSources.forEach(source => {
            console.log('Creating category for source:', source);
            const tools = toolsBySource[source];
            const sortedTools = [...tools].sort((a, b) => a.name.localeCompare(b.name));
            
            // Check if this category should be expanded (default to true for new categories)
            const isExpanded = this.toolCategoryStates[source] !== false;
            
            // Create source category
            const sourceCategory = document.createElement('div');
            sourceCategory.className = `tool-source-category ${isExpanded ? 'expanded' : ''}`;
            sourceCategory.dataset.source = source; // Add data attribute for identification
            
            // Source header
            const sourceHeader = document.createElement('div');
            sourceHeader.className = 'tool-source-header';
            
            const sourceExpand = document.createElement('div');
            sourceExpand.className = 'tool-source-expand';
            sourceExpand.innerHTML = `
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="transform: rotate(${isExpanded ? '90deg' : '0deg'});">
                    <polyline points="9,18 15,12 9,6"></polyline>
                </svg>
            `;
            
            const sourceTitle = document.createElement('div');
            sourceTitle.className = 'tool-source-title';
            sourceTitle.textContent = source === 'default' ? 'Built-in Tools' : `${source.charAt(0).toUpperCase() + source.slice(1)} Tools`;
            
            const sourceEnabledCount = tools.filter(tool => tool.enabled).length;
            const sourceTotalCount = tools.length;
            
            const sourceAllEnabled = sourceEnabledCount === sourceTotalCount;
            
            const sourceCounter = document.createElement('div');
            sourceCounter.className = 'tool-source-counter';
            sourceCounter.textContent = `${sourceEnabledCount}/${sourceTotalCount}`;
            
            const sourceToggle = document.createElement('div');
            sourceToggle.className = `tool-source-toggle ${sourceAllEnabled ? 'enabled' : ''}`;
            sourceToggle.title = `Toggle all ${source} tools`;
            sourceToggle.addEventListener('click', (e) => {
                e.stopPropagation();
                // Calculate current state dynamically instead of using closure variable
                const currentSourceTools = this.tools.filter(tool => (tool.source || 'default') === source);
                const currentSourceEnabledCount = currentSourceTools.filter(tool => tool.enabled).length;
                const currentSourceAllEnabled = currentSourceEnabledCount === currentSourceTools.length;
                console.log(`Toggling all tools for source: ${source}, current state: ${currentSourceAllEnabled}`);
                this.toggleSourceTools(source, !currentSourceAllEnabled);
            });
            
            sourceHeader.appendChild(sourceExpand);
            sourceHeader.appendChild(sourceTitle);
            sourceHeader.appendChild(sourceCounter);
            sourceHeader.appendChild(sourceToggle);
            
            console.log('Adding event listener for source:', source);
            
            // Make header clickable to expand/collapse
            sourceHeader.addEventListener('click', (e) => {
                console.log('Header clicked for source:', source, 'Event target:', e.target);
                // Don't trigger if clicking on the toggle button
                if (e.target === sourceToggle || sourceToggle.contains(e.target as Node)) {
                    console.log('Click was on toggle button, ignoring');
                    return;
                }
                console.log('Calling toggleSourceCategory for:', source);
                this.toggleSourceCategory(sourceCategory);
            });
            
            console.log('Event listener added for source:', source, 'Header element:', sourceHeader);
            
            // Tools list for this source
            const sourceToolsList = document.createElement('div');
            sourceToolsList.className = 'tool-source-tools';
            sourceToolsList.style.display = isExpanded ? 'block' : 'none';
            
            sortedTools.forEach(tool => {
                const toolItem = document.createElement('div');
                toolItem.className = `tool-item ${tool.enabled ? 'enabled' : ''}`;
                
                const toolName = document.createElement('div');
                toolName.className = 'tool-name';
                toolName.textContent = tool.name;
                
                const toolDescription = document.createElement('div');
                toolDescription.className = 'tool-description';
                toolDescription.textContent = tool.description;
                toolDescription.title = tool.description;
                
                const toolToggle = document.createElement('div');
                toolToggle.className = `tool-toggle ${tool.enabled ? 'enabled' : ''}`;
                toolToggle.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.toggleTool(tool.name, !tool.enabled);
                });
                
                toolItem.appendChild(toolName);
                toolItem.appendChild(toolDescription);
                toolItem.appendChild(toolToggle);
                
                sourceToolsList.appendChild(toolItem);
            });
            
            sourceCategory.appendChild(sourceHeader);
            sourceCategory.appendChild(sourceToolsList);
            this.toolsList.appendChild(sourceCategory);
        });
    }

    private toggleSourceCategory(sourceCategory: HTMLElement): void {
        const source = sourceCategory.dataset.source;
        if (!source) return;
        
        console.log('toggleSourceCategory called for:', source);
        console.log('Category element:', sourceCategory);
        console.log('Current classes:', sourceCategory.className);
        
        const isExpanded = sourceCategory.classList.contains('expanded');
        const newState = !isExpanded;
        
        console.log('Current state:', isExpanded, 'New state:', newState);
        
        // Update the state tracking
        this.toolCategoryStates[source] = newState;
        
        const sourceHeader = sourceCategory.querySelector('.tool-source-header') as HTMLElement;
        const sourceToolsList = sourceCategory.querySelector('.tool-source-tools') as HTMLElement;
        const expandIcon = sourceHeader.querySelector('.tool-source-expand svg') as SVGElement;
        
        console.log('Elements found:', {
            sourceHeader: !!sourceHeader,
            sourceToolsList: !!sourceToolsList,
            expandIcon: !!expandIcon
        });
        
        if (newState) {
            sourceCategory.classList.add('expanded');
            sourceToolsList.style.display = 'block';
            expandIcon.style.transform = 'rotate(90deg)';
        } else {
            sourceCategory.classList.remove('expanded');
            sourceToolsList.style.display = 'none';
            expandIcon.style.transform = 'rotate(0deg)';
        }
        
        console.log('After toggle - classes:', sourceCategory.className);
        console.log('Display style:', sourceToolsList.style.display);
        console.log('State tracking:', this.toolCategoryStates);
    }

    private async toggleTool(toolName: string, enabled: boolean): Promise<void> {
        if (!this.currentSession?.sessionId) {
            console.error('No active session for tool toggle');
            return;
        }

        try {
            await this.apiService.toggleTool(this.currentSession.sessionId, toolName, enabled);
            
            // Update the local tool state
            const tool = this.tools.find(t => t.name === toolName);
            if (tool) {
                tool.enabled = enabled;
                this.updateToolsUI();
            }
            console.log(`Successfully toggled tool ${toolName} to ${enabled}`);
        } catch (error) {
            console.error('Error toggling tool:', error);
        }
    }

    private async toggleAllTools(enabled: boolean): Promise<void> {
        if (!this.currentSession?.sessionId) {
            console.error('No active session for tool toggle');
            return;
        }

        try {
            await this.apiService.toggleAllTools(this.currentSession.sessionId, enabled);
            
            // Update all local tool states
            this.tools.forEach(tool => {
                tool.enabled = enabled;
            });
            
            this.updateToolsUI();
        } catch (error) {
            console.error(`Error ${enabled ? 'enabling' : 'disabling'} all tools:`, error);
        }
    }

    private updateToolsUI(): void {
        // Update the main tools counter
        const enabledCount = this.tools.filter(tool => tool.enabled).length;
        const totalCount = this.tools.length;
        
        const toolsLabelSpan = this.toolsHeader.querySelector('.tools-label span');
        if (toolsLabelSpan) {
            toolsLabelSpan.textContent = `Tools Configuration [${enabledCount}/${totalCount}]`;
        }
        
        // Update each source category's counters and toggle states
        const sourceCategories = this.toolsList.querySelectorAll('.tool-source-category');
        sourceCategories.forEach(category => {
            const source = (category as HTMLElement).dataset.source;
            if (!source) return;
            
            // Preserve the current collapse/expand state
            const currentlyExpanded = (category as HTMLElement).classList.contains('expanded');
            const savedState = this.toolCategoryStates[source];
            
            // If there's a mismatch between DOM and saved state, fix it
            if (savedState !== undefined && currentlyExpanded !== savedState) {
                const sourceToolsList = category.querySelector('.tool-source-tools') as HTMLElement;
                const expandIcon = category.querySelector('.tool-source-expand svg') as SVGElement;
                
                if (savedState) {
                    (category as HTMLElement).classList.add('expanded');
                    if (sourceToolsList) sourceToolsList.style.display = 'block';
                    if (expandIcon) expandIcon.style.transform = 'rotate(90deg)';
                } else {
                    (category as HTMLElement).classList.remove('expanded');
                    if (sourceToolsList) sourceToolsList.style.display = 'none';
                    if (expandIcon) expandIcon.style.transform = 'rotate(0deg)';
                }
            }
            
            const sourceTools = this.tools.filter(tool => (tool.source || 'default') === source);
            const sourceEnabledCount = sourceTools.filter(tool => tool.enabled).length;
            const sourceTotalCount = sourceTools.length;
            const sourceAllEnabled = sourceEnabledCount === sourceTotalCount;
            
            // Update counter
            const counter = category.querySelector('.tool-source-counter');
            if (counter) {
                counter.textContent = `${sourceEnabledCount}/${sourceTotalCount}`;
            }
            
            // Update source toggle
            const sourceToggle = category.querySelector('.tool-source-toggle');
            if (sourceToggle) {
                if (sourceAllEnabled) {
                    sourceToggle.classList.add('enabled');
                } else {
                    sourceToggle.classList.remove('enabled');
                }
            }
            
            // Update individual tool toggles and states
            const toolItems = category.querySelectorAll('.tool-item');
            toolItems.forEach(toolItem => {
                const toolNameEl = toolItem.querySelector('.tool-name');
                if (!toolNameEl) return;
                
                const toolName = toolNameEl.textContent;
                const tool = this.tools.find(t => t.name === toolName);
                if (!tool) return;
                
                const toolToggle = toolItem.querySelector('.tool-toggle');
                if (toolToggle) {
                    if (tool.enabled) {
                        toolToggle.classList.add('enabled');
                        toolItem.classList.add('enabled');
                    } else {
                        toolToggle.classList.remove('enabled');
                        toolItem.classList.remove('enabled');
                    }
                }
            });
        });
    }

    private async toggleSourceTools(source: string, enabled: boolean): Promise<void> {
        if (!this.currentSession?.sessionId) {
            console.error('No active session for tool toggle');
            return;
        }

        try {
            await this.apiService.toggleSourceTools(this.currentSession.sessionId, source, enabled);
            
            // Update local tool states for this source
            const sourceTools = this.tools.filter(tool => (tool.source || 'default') === source);
            sourceTools.forEach(tool => {
                tool.enabled = enabled;
            });
            
            this.updateToolsUI();
        } catch (error) {
            console.error(`Error ${enabled ? 'enabling' : 'disabling'} tools for source ${source}:`, error);
        }
    }

    private async toggleDebugPanel(): Promise<void> {
        const currentState = this.getCurrentDebugPanelState();
        const newState = !currentState;
        this.setCurrentDebugPanelState(newState);
        
        if (newState) {
            this.debugPanelOverlay.classList.add('active');
            this.debugPanelToggle.classList.add('active');
            document.body.classList.add('debug-panel-open');
            
            // Automatically enable debug mode when panel opens
            await this.setDebugMode(true);
            this.loadDebugEvents();
        } else {
            this.debugPanelOverlay.classList.remove('active');
            this.debugPanelToggle.classList.remove('active');
            document.body.classList.remove('debug-panel-open');
            
            // Automatically disable debug mode when panel closes
            await this.setDebugMode(false);
        }
    }

    private async closeDebugPanel(): Promise<void> {
        this.setCurrentDebugPanelState(false);
        this.debugPanelOverlay.classList.remove('active');
        this.debugPanelToggle.classList.remove('active');
        document.body.classList.remove('debug-panel-open');
        
        // Automatically disable debug mode when panel closes
        await this.setDebugMode(false);
    }

    private async setDebugMode(enabled: boolean): Promise<void> {
        if (!this.currentSession?.sessionId) {
            console.error('No active session for debug mode');
            return;
        }

        try {
            await this.apiService.setDebugMode(this.currentSession.sessionId, enabled);
            this.setCurrentDebugEnabled(enabled);
            this.updateDebugUI();
        } catch (error) {
            console.error('Error setting debug mode:', error);
        }
    }

    private async clearDebugEvents(): Promise<void> {
        if (!this.currentSession?.sessionId) {
            console.error('No active session for debug events');
            return;
        }

        try {
            await this.apiService.clearDebugEvents(this.currentSession.sessionId);
            this.debugEventsList = [];
            this.renderDebugEvents();
        } catch (error) {
            console.error('Error clearing debug events:', error);
        }
    }

    private async loadDebugEvents(): Promise<void> {
        if (!this.currentSession?.sessionId) {
            console.error('No active session for debug events');
            return;
        }

        try {
            const result = await this.apiService.loadDebugEvents(this.currentSession.sessionId);
            this.debugEventsList = result.events;
            this.setCurrentDebugEnabled(result.enabled);
            this.updateDebugUI();
            this.renderDebugEvents();
        } catch (error) {
            console.error('Error loading debug events:', error);
        }
    }

    private updateDebugUI(): void {
        if (!this.currentSession) {
            this.debugEventsContainer.innerHTML = `
                <div class="debug-disabled-message">
                    No active session. Create a new chat to enable debug mode.
                </div>
            `;
            return;
        }
        
        if (!this.getCurrentDebugEnabled()) {
            this.debugEventsContainer.innerHTML = `
                <div class="debug-disabled-message">
                    Debug mode is automatically enabled when this panel is open.
                </div>
            `;
        }
    }

    private renderDebugEvents(): void {
        if (!this.currentSession) {
            this.updateDebugUI();
            return;
        }
        
        if (!this.getCurrentDebugEnabled()) {
            this.updateDebugUI();
            return;
        }

        if (this.debugEventsList.length === 0) {
            this.debugEventsContainer.innerHTML = `
                <div class="debug-disabled-message">
                    No debug events captured yet. Send a message to see the communication flow.
                </div>
            `;
            return;
        }

        const eventsHtml = this.debugEventsList
            .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
            .map((event, index) => {
                const timestamp = new Date(event.timestamp).toLocaleTimeString();
                const colorizedData = this.applyDebugColorScheme(event.data);
                
                // Properly escape HTML characters
                const escapedMessage = Utils.escapeHtml(event.message);
                
                return `
                    <div class="debug-event">
                        <div class="debug-event-header">
                            <span class="debug-event-type ${event.event_type}">${event.event_type}</span>
                            <span class="debug-event-timestamp">${timestamp}</span>
                            <button class="debug-event-fullscreen-btn" onclick="window.chatApp.openDebugFullscreen(${index})">
                                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
                                </svg>
                                Expand
                            </button>
                        </div>
                        <div class="debug-event-message">${escapedMessage}</div>
                        <div class="debug-event-data">${colorizedData}</div>
                    </div>
                `;
            })
            .join('');

        this.debugEventsContainer.innerHTML = eventsHtml;
        this.debugEventsContainer.scrollTop = this.debugEventsContainer.scrollHeight;
    }

    private applyDebugColorScheme(data: Record<string, any>): string {
        // Apply color scheme directly - truncation is now handled by backend
        return this.colorizeDebugJsonData(data, 0);
    }

    private colorizeDebugJsonData(obj: any, depth: number = 0, keyPath: string = '', rootColorMetadata: Record<string, string> = {}): string {
        const indent = '  '.repeat(depth);
        
        if (obj === null) {
            return '<span class="debug-color-grey">null</span>';
        }
        
        if (typeof obj === 'string') {
            if (obj.endsWith('...[truncated]')) {
                const mainText = obj.substring(0, obj.length - 14); // Remove "...[truncated]"
                return `"<span class="debug-color-white">${Utils.escapeHtml(mainText)}</span><span class="debug-truncated">...[truncated]</span>"`;
            }
            return `"<span class="debug-color-white">${Utils.escapeHtml(obj)}</span>"`;
        }
        
        if (typeof obj === 'number' || typeof obj === 'boolean') {
            return `<span class="debug-color-yellow">${obj}</span>`;
        }
        
        if (Array.isArray(obj)) {
            if (obj.length === 0) return '[]';
            
            const items = obj.map(item => {
                if (typeof item === 'string' && item.endsWith('...[truncated]')) {
                    const mainText = item.substring(0, item.length - 14);
                    return `${indent}  "<span class="debug-color-white">${Utils.escapeHtml(mainText)}</span><span class="debug-truncated">...[truncated]</span>"`;
                }
                return `${indent}  ${this.colorizeDebugJsonData(item, depth + 1, keyPath, rootColorMetadata)}`;
            });
            
            return `[\n${items.join(',\n')}\n${indent}]`;
        }
        
        if (typeof obj === 'object' && obj !== null) {
            const entries = Object.entries(obj);
            if (entries.length === 0) return '{}';
            
            // If this is the root object, extract color metadata
            const colorMetadata = depth === 0 ? (obj._debug_colors || {}) : rootColorMetadata;
            
            const items = entries
                .filter(([key]) => key !== '_debug_colors') // Don't display color metadata
                .map(([key, value]) => {
                    // Build the full key path for nested lookups
                    const currentKeyPath = keyPath ? `${keyPath}_${key}` : key;
                    
                    // Check for color using the full path
                    const color = colorMetadata[`_${currentKeyPath}_color`];
                    
                    let keyHtml;
                    if (color) {
                        keyHtml = `<span class="debug-key debug-color-${color}">"${Utils.escapeHtml(key)}"</span>`;
                    } else {
                        keyHtml = `<span class="debug-key">"${Utils.escapeHtml(key)}"</span>`;
                    }
                    
                    const valueHtml = this.colorizeDebugJsonData(value, depth + 1, currentKeyPath, colorMetadata);
                    return `${indent}  ${keyHtml}: ${valueHtml}`;
                });
            
            return `{\n${items.join(',\n')}\n${indent}}`;
        }
        
        return Utils.escapeHtml(String(obj));
    }

    private findRootColorMetadata(obj: any): Record<string, string> {
        // Recursively traverse up to find the root _debug_colors metadata
        if (obj && typeof obj === 'object' && obj._debug_colors) {
            return obj._debug_colors;
        }
        
        // If this object doesn't have color metadata, check if any parent object does
        // This is handled by ensuring we always pass the root color metadata down
        return {};
    }

    public openDebugFullscreen(eventIndex: number): void {
        const event = this.debugEventsList[eventIndex];
        if (!event) return;
        
        const timestamp = new Date(event.timestamp).toLocaleString();
        this.debugFullscreenTitle.textContent = `${event.event_type} - ${timestamp}`;
        
        const colorizedData = this.applyDebugColorScheme(event.data);
        this.debugFullscreenData.innerHTML = colorizedData;
        
        this.debugFullscreenOverlay.classList.add('active');
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }

    private closeDebugFullscreen(): void {
        this.debugFullscreenOverlay.classList.remove('active');
        document.body.style.overflow = ''; // Restore scrolling
    }



    // Debug state management per session
    private getCurrentDebugPanelState(): boolean {
        return this.currentSession?.debugPanelOpen || false;
    }

    private setCurrentDebugPanelState(open: boolean): void {
        if (this.currentSession) {
            this.currentSession.debugPanelOpen = open;
            
        }
    }

    private getCurrentDebugEnabled(): boolean {
        return this.currentSession?.debugEnabled || false;
    }

    private setCurrentDebugEnabled(enabled: boolean): void {
        if (this.currentSession) {
            this.currentSession.debugEnabled = enabled;
            
        }
    }

    private showEmptyState(): void {
        this.messagesContainer.innerHTML = `
            <div class="welcome-message empty-state">
                <h1>AI Agent</h1>
                <p>No active chat sessions.</p>
                <p>Click <span class="new-chat-link" id="newChatLink">New chat</span> to start a conversation.</p>
            </div>
        `;
        
        // Add click handler for the new chat link
        const newChatLink = document.getElementById('newChatLink');
        if (newChatLink) {
            newChatLink.addEventListener('click', () => {
                this.createNewSession();
            });
        }
        
        this.updateSendButtonState();
        this.messageInput.disabled = true;
        this.messageInput.placeholder = "Create a new chat to start messaging...";
        
        // Clear tools and debug state for no active session
        this.tools = [];
        this.debugEventsList = [];
        this.renderTools();
        this.updateDebugUI();
        
        // Close debug panel if it's open
        this.debugPanelOverlay.classList.remove('active');
        this.debugPanelToggle.classList.remove('active');
        document.body.classList.remove('debug-panel-open');
    }

    private enableInput(): void {
        this.messageInput.disabled = false;
        this.messageInput.placeholder = "Message AI Agent...";
        this.updateSendButtonState();
    }

    private async verifyBackendSession(sessionId: string): Promise<void> {
        try {
            console.log(`Verifying backend session: ${sessionId}`);
            const isValid = await this.apiService.verifySession(sessionId);

            if (isValid) {
                console.log(`Backend session ${sessionId} verified and reinitialized`);
                // Session exists and is reinitialized
                return;
            } else {
                console.warn(`Backend session ${sessionId} not found, will create new session when needed`);
                // Clear the sessionId since backend session doesn't exist
                if (this.currentSession) {
                    this.chatService.updateSessionBackendId(this.currentSession, undefined);
                }
            }
        } catch (error) {
            console.error(`Failed to verify backend session ${sessionId}:`, error);
            // Clear the sessionId since we can't verify
            if (this.currentSession) {
                this.chatService.updateSessionBackendId(this.currentSession, undefined);
            }
        }
    }

    private showSessionVerificationLoading(): void {
        this.messagesContainer.innerHTML = `
            <div class="welcome-message">
                <div class="session-verification-loading">
                    <div class="loading-spinner"></div>
                    <h1>Verifying session...</h1>
                    <p>Checking if your previous session is still available.</p>
                </div>
            </div>
        `;
    }

    private hideSessionVerificationLoading(): void {
        // Clear the loading message - it will be replaced by the actual session content
        const loadingEl = this.messagesContainer.querySelector('.session-verification-loading');
        if (loadingEl) {
            loadingEl.parentElement?.remove();
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const chatApp = new ChatApp();
    // Make it globally accessible for onclick handlers
    (window as any).chatApp = chatApp;
});
