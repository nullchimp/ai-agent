// Import service modules
import { ApiService } from './apiService';
import { ChatService } from './chatService';
import { MessageUIService } from './messageUIService';
import { ToolUIService } from './toolUIService';
import { SessionUIService } from './sessionUIService';
import { DebugUIService } from './debugUIService';
import { Message, Tool, ChatSession, DebugEvent } from './types';

class ChatApp {
    // Services
    private apiService: ApiService;
    private chatService: ChatService;
    private messageUIService: MessageUIService;
    private toolUIService: ToolUIService;
    private sessionUIService: SessionUIService;
    private debugUIService: DebugUIService;
    
    // DOM elements
    private messageInput: HTMLTextAreaElement;
    private sendBtn: HTMLButtonElement;
    
    // UI state
    private currentSession: ChatSession | null = null;
    private tools: Tool[] = [];
    private debugEventsList: DebugEvent[] = [];
    private isCreatingSession: boolean = false;
    private isLoadingTools: boolean = false;
    private isSendingMessage: boolean = false;
    private isVerifyingSession: boolean = false;

    constructor() {
        // Initialize core DOM elements
        const messagesContainer = document.getElementById('messagesContainer') as HTMLElement;
        const chatHistory = document.getElementById('chatHistory') as HTMLElement;
        const newChatBtn = document.getElementById('newChatBtn') as HTMLButtonElement;
        const toolsHeader = document.getElementById('toolsHeader') as HTMLElement;
        const toolsList = document.getElementById('toolsList') as HTMLElement;
        
        this.messageInput = document.getElementById('messageInput') as HTMLTextAreaElement;
        this.sendBtn = document.getElementById('sendBtn') as HTMLButtonElement;
        
        // Debug elements
        const debugPanelToggle = document.getElementById('debugPanelToggle') as HTMLButtonElement;
        const debugPanelOverlay = document.getElementById('debugPanelOverlay') as HTMLElement;
        const debugEventsContainer = document.getElementById('debugEvents') as HTMLElement;
        const debugClearBtn = document.getElementById('debugClearBtn') as HTMLButtonElement;
        const debugPanelClose = document.getElementById('debugPanelClose') as HTMLButtonElement;
        const debugFullscreenOverlay = document.getElementById('debugFullscreenOverlay') as HTMLElement;
        const debugFullscreenData = document.getElementById('debugFullscreenData') as HTMLElement;
        const debugFullscreenTitle = document.getElementById('debugFullscreenTitle') as HTMLElement;
        const debugFullscreenClose = document.getElementById('debugFullscreenClose') as HTMLButtonElement;

        // Initialize services
        this.apiService = new ApiService();
        this.chatService = new ChatService();
        this.messageUIService = new MessageUIService(messagesContainer);
        this.toolUIService = new ToolUIService(toolsHeader, toolsList);
        this.sessionUIService = new SessionUIService(chatHistory, newChatBtn);
        this.debugUIService = new DebugUIService(
            debugPanelToggle, debugPanelOverlay, debugEventsContainer,
            debugClearBtn, debugPanelClose, debugFullscreenOverlay,
            debugFullscreenData, debugFullscreenTitle, debugFullscreenClose
        );

        this.init();
    }

    private async init(): Promise<void> {
        this.setupEventListeners();
        
        const sessions = this.chatService.getSessions();
        console.log('ChatApp initialized with', sessions.length, 'sessions loaded.');

        if (this.chatService.shouldCreateNewSession()) {
            await this.createNewSession();
        } else {
            this.currentSession = this.chatService.getMostRecentSession();
            
            console.log('Loading existing session:', this.currentSession?.sessionId);
            if (this.currentSession?.sessionId) {
                this.isVerifyingSession = true;
                this.updateSendButtonState();
                this.sessionUIService.showSessionVerificationLoading();
                await this.verifyBackendSession(this.currentSession.sessionId);
                this.isVerifyingSession = false;
                this.updateSendButtonState();
                this.sessionUIService.hideSessionVerificationLoading();
            }
            
            this.displayExistingMessages();
            await this.loadTools();
            await this.restoreDebugState();
        }
        
        this.sessionUIService.renderChatHistory(
            this.chatService.getSessions(),
            this.currentSession,
            this.loadSession.bind(this),
            this.deleteSession.bind(this)
        );
    }

    private setupEventListeners(): void {
        // Message input events
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
        
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // New chat button
        const newChatBtn = document.getElementById('newChatBtn') as HTMLButtonElement;
        newChatBtn.addEventListener('click', () => this.createNewSession());
        
        // Tools section
        this.toolUIService.setupToolsToggle();
        
        // Debug panel
        this.debugUIService.setupEventListeners(
            this.toggleDebugPanel.bind(this),
            this.closeDebugPanel.bind(this),
            this.clearDebugEvents.bind(this)
        );
    }

    private adjustTextareaHeight(): void {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    private updateSendButtonState(): void {
        const hasContent = this.messageInput.value.trim().length > 0;
        const hasSession = this.currentSession !== null;
        const isNotBusy = !this.isSendingMessage && !this.isCreatingSession && !this.isLoadingTools && !this.isVerifyingSession;
        
        this.sendBtn.disabled = !hasContent || !hasSession || !isNotBusy;
    }

    private async sendMessage(): Promise<void> {
        const content = this.messageInput.value.trim();
        if (!content || !this.currentSession) return;

        const validation = this.chatService.validateMessage(content);
        if (!validation.isValid) {
            this.messageUIService.showError(validation.error || 'Invalid message');
            return;
        }

        this.isSendingMessage = true;
        this.updateSendButtonState();

        if (!this.currentSession.sessionId) {
            console.log('Creating backend session for existing frontend session...');
            try {
                const backendSessionId = await this.apiService.createNewSession();
                this.chatService.updateSessionBackendId(this.currentSession, backendSessionId);
                console.log(`Created backend session: ${backendSessionId}`);
                await this.loadTools();
            } catch (error) {
                console.error('Failed to create backend session:', error);
                this.messageUIService.showError('Failed to create backend session. Please try again.');
                this.isSendingMessage = false;
                this.updateSendButtonState();
                return;
            }
        }

        const userMessage = this.chatService.createMessage(content, 'user');
        this.chatService.addMessage(this.currentSession, userMessage);
        this.messageUIService.displayMessage(userMessage);
        this.renderChatHistory();
        
        this.messageInput.value = '';
        this.adjustTextareaHeight();
        this.updateSendButtonState();
        this.messageUIService.showTypingIndicator();

        try {
            console.log(`Sending message to session: ${this.currentSession.sessionId}`);
            const apiResponse = await this.apiService.callChatAPI(content, this.currentSession.sessionId!);
            this.messageUIService.hideTypingIndicator();

            const assistantMessage = this.chatService.createMessage(
                apiResponse.response, 
                'assistant', 
                apiResponse.usedTools
            );
            
            this.chatService.addMessage(this.currentSession, assistantMessage);
            this.messageUIService.displayMessage(assistantMessage);
            this.renderChatHistory();
            
            if (this.getCurrentDebugEnabled()) {
                this.loadDebugEvents();
            }
        } catch (error) {
            this.messageUIService.hideTypingIndicator();
            this.messageUIService.showError('Failed to get response. Please try again.');
            console.error('API Error:', error);
        } finally {
            this.isSendingMessage = false;
            this.updateSendButtonState();
        }
    }

    private async createNewSession(): Promise<void> {
        if (this.isCreatingSession) return;
        
        this.isCreatingSession = true;
        this.sessionUIService.updateNewChatButtonState(true);
        this.updateSendButtonState();
        
        this.messageUIService.clearMessages();
        
        try {
            const backendSessionId = await this.apiService.createNewSession();
            this.currentSession = this.chatService.createSession(backendSessionId);
            
            console.log(`Created new session: frontend ID=${this.currentSession.id}, backend ID=${backendSessionId}`);
            
            this.renderChatHistory();
            this.enableInput();
            await this.loadTools();
            await this.restoreDebugState();
        } catch (error) {
            console.error('Failed to create new session:', error);
            this.messageUIService.showError('Failed to create new session. Please try again.');
            
            this.currentSession = this.chatService.createSession();
            this.renderChatHistory();
            this.enableInput();
        } finally {
            this.isCreatingSession = false;
            this.sessionUIService.updateNewChatButtonState(false);
            this.updateSendButtonState();
        }
    }

    private async loadSession(sessionId: string): Promise<void> {
        const session = this.chatService.getSessionById(sessionId);
        if (!session || session.id === this.currentSession?.id) return;
        
        this.currentSession = session;
        this.displayExistingMessages();
        this.renderChatHistory();
        this.enableInput();
        await this.loadTools();
        await this.restoreDebugState();
    }

    private displayExistingMessages(): void {
        if (!this.currentSession) return;
        
        if (this.currentSession.messages.length === 0) {
            this.messageUIService.clearMessages();
            return;
        }
        
        this.messageUIService.clearMessages();
        this.currentSession.messages.forEach(message => {
            this.messageUIService.displayMessage(message);
        });
    }

    private async deleteSession(sessionId: string): Promise<void> {
        const session = this.chatService.getSessionById(sessionId);
        if (!session) return;
        
        console.log(`Deleting session: frontend ID=${session.id}, backend ID=${session.sessionId}`);
        
        try {
            if (session.sessionId) {
                await this.apiService.deleteSession(session.sessionId);
                console.log(`Successfully deleted backend session ${session.sessionId}`);
            }
        } catch (error) {
            console.error('Failed to delete backend session:', error);
        }
        
        this.chatService.deleteSession(sessionId);
        
        if (this.currentSession?.id === sessionId) {
            const remainingSessions = this.chatService.getSessions();
            if (remainingSessions.length > 0) {
                this.currentSession = remainingSessions[0];
                await this.loadSession(this.currentSession.id);
            } else {
                this.currentSession = null;
                this.messageUIService.clearMessages();
            }
        }
        
        this.renderChatHistory();
    }

    private async loadTools(): Promise<void> {
        if (!this.currentSession?.sessionId) {
            console.log('No session ID available for loading tools');
            this.tools = [];
            this.toolUIService.renderTools(this.tools, false, this.apiService, null);
            return;
        }

        this.isLoadingTools = true;
        this.toolUIService.renderToolsLoading();
        this.updateSendButtonState();

        try {
            this.tools = await this.apiService.loadTools(this.currentSession.sessionId);
            console.log(`Loaded ${this.tools.length} tools:`, this.tools.map(t => t.name));
        } catch (error) {
            console.error('Failed to load tools:', error);
            this.tools = [];
        } finally {
            this.isLoadingTools = false;
            this.toolUIService.renderTools(this.tools, !!this.currentSession, this.apiService, this.currentSession?.sessionId || null);
            this.updateSendButtonState();
        }
    }

    private async restoreDebugState(): Promise<void> {
        if (!this.currentSession) return;
        
        const debugPanelShouldBeOpen = this.getCurrentDebugPanelState();
        
        if (debugPanelShouldBeOpen) {
            this.debugUIService.showDebugPanel();
            await this.setDebugMode(true);
            await this.loadDebugEvents();
        } else {
            this.debugUIService.hideDebugPanel();
            const sessionDebugEnabled = this.getCurrentDebugEnabled();
            if (sessionDebugEnabled) {
                await this.setDebugMode(true);
            }
        }
    }

    private async toggleDebugPanel(): Promise<void> {
        const currentState = this.getCurrentDebugPanelState();
        const newState = !currentState;
        this.setCurrentDebugPanelState(newState);
        
        if (newState) {
            this.debugUIService.showDebugPanel();
            await this.setDebugMode(true);
            this.loadDebugEvents();
        } else {
            this.debugUIService.hideDebugPanel();
            await this.setDebugMode(false);
        }
    }

    private async closeDebugPanel(): Promise<void> {
        this.setCurrentDebugPanelState(false);
        this.debugUIService.hideDebugPanel();
        await this.setDebugMode(false);
    }

    private async setDebugMode(enabled: boolean): Promise<void> {
        if (!this.currentSession?.sessionId) {
            console.log('No session ID available for debug mode');
            return;
        }

        try {
            await this.apiService.setDebugMode(this.currentSession.sessionId, enabled);
            this.setCurrentDebugEnabled(enabled);
            console.log(`Debug mode set to: ${enabled}`);
        } catch (error) {
            console.error('Failed to set debug mode:', error);
        }
    }

    private async clearDebugEvents(): Promise<void> {
        if (!this.currentSession?.sessionId) return;

        try {
            await this.apiService.clearDebugEvents(this.currentSession.sessionId);
            this.debugEventsList = [];
            this.debugUIService.renderDebugEvents(this.debugEventsList);
            console.log('Debug events cleared');
        } catch (error) {
            console.error('Failed to clear debug events:', error);
        }
    }

    private async loadDebugEvents(): Promise<void> {
        if (!this.currentSession?.sessionId) return;

        try {
            const debugInfo = await this.apiService.loadDebugEvents(this.currentSession.sessionId);
            this.debugEventsList = debugInfo.events || [];
            this.debugUIService.renderDebugEvents(this.debugEventsList);
            console.log(`Loaded ${this.debugEventsList.length} debug events`);
        } catch (error) {
            console.error('Failed to load debug events:', error);
            this.debugEventsList = [];
            this.debugUIService.renderDebugEvents(this.debugEventsList);
        }
    }

    private async verifyBackendSession(sessionId: string): Promise<void> {
        try {
            const isValid = await this.apiService.verifySession(sessionId);
            if (!isValid && this.currentSession) {
                console.log(`Backend session ${sessionId} is invalid, creating new one...`);
                const newBackendSessionId = await this.apiService.createNewSession();
                this.chatService.updateSessionBackendId(this.currentSession, newBackendSessionId);
                console.log(`Created replacement backend session: ${newBackendSessionId}`);
            }
        } catch (error) {
            console.error('Failed to verify backend session:', error);
        }
    }

    // Helper methods for session state
    private renderChatHistory(): void {
        this.sessionUIService.renderChatHistory(
            this.chatService.getSessions(),
            this.currentSession,
            this.loadSession.bind(this),
            this.deleteSession.bind(this)
        );
    }

    private enableInput(): void {
        this.messageInput.disabled = false;
        this.messageInput.focus();
    }

    private getCurrentDebugPanelState(): boolean {
        return this.currentSession?.debugPanelOpen || false;
    }

    private setCurrentDebugPanelState(state: boolean): void {
        if (this.currentSession) {
            this.currentSession.debugPanelOpen = state;
            this.chatService.saveChatHistory();
        }
    }

    private getCurrentDebugEnabled(): boolean {
        return this.currentSession?.debugEnabled || false;
    }

    private setCurrentDebugEnabled(enabled: boolean): void {
        if (this.currentSession) {
            this.currentSession.debugEnabled = enabled;
            this.chatService.saveChatHistory();
        }
    }
}

// Initialize the app
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});