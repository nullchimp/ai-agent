import { Message } from './types';
import { ApiManager } from './libs/api';
import { SessionManager } from './libs/session';
import { ToolsManager } from './libs/tools';
import { DebugManager } from './libs/debug';
import { ChatManager } from './libs/chat';
import { AuthManager } from './libs/auth';

// =================================================================================
// MAIN CHAT APP
// =================================================================================
export class AgentApp {
    public debugManager: DebugManager;
    private apiManager: ApiManager;
    private authManager: AuthManager;
    private sessionManager: SessionManager;
    private toolsManager: ToolsManager;
    private uiManager: ChatManager;

    private messageInput: HTMLTextAreaElement;
    private sendBtn: HTMLButtonElement;
    private newChatBtn: HTMLButtonElement;
    private loginContainer: HTMLElement | null;
    private appContainer: HTMLElement | null;
    private loginForm: HTMLFormElement | null;
    private loginError: HTMLElement | null;

    private isSendingMessage: boolean = false;
    private isCreatingSession: boolean = false;
    private isVerifyingSession: boolean = false;

    constructor() {
        this.messageInput = document.getElementById('messageInput') as HTMLTextAreaElement;
        this.sendBtn = document.getElementById('sendBtn') as HTMLButtonElement;
        this.newChatBtn = document.getElementById('newChatBtn') as HTMLButtonElement;
        this.loginContainer = document.getElementById('loginContainer');
        this.appContainer = document.getElementById('appContainer');
        this.loginForm = document.getElementById('loginForm') as HTMLFormElement;
        this.loginError = document.getElementById('loginError');

        this.authManager = new AuthManager();
        this.apiManager = new ApiManager();
        this.uiManager = new ChatManager();
        this.sessionManager = new SessionManager(this.apiManager, () => this.onSessionChanged());
        this.toolsManager = new ToolsManager(this.apiManager, this.sessionManager);
        this.debugManager = new DebugManager(this.apiManager, this.sessionManager);

        this.init();
    }

    private async init(): Promise<void> {
        if (!this.authManager.isAuthenticated()) {
            this.showLoginScreen();
            return;
        }

        this.showAppScreen();
        this.setupEventListeners();
        
        this.isVerifyingSession = true;
        this.updateButtonStates();
        this.uiManager.showLoadingState('Loading your sessions...', 'Fetching your chat history from the database.');
        
        await this.sessionManager.loadUserSessions();
        
        this.isVerifyingSession = false;
        
        if (this.sessionManager.sessions.length === 0) {
            await this.createNewSession();
        } else {
            await this.sessionManager.verifyCurrentSession();
            await this.onSessionChanged();
        }
        
        this.sessionManager.renderChatHistory();
    }

    private showLoginScreen(): void {
        if (this.loginContainer) this.loginContainer.style.display = 'flex';
        if (this.appContainer) this.appContainer.style.display = 'none';
        
        if (this.loginForm) {
            this.loginForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleLogin();
            });
        }
    }

    private showAppScreen(): void {
        if (this.loginContainer) this.loginContainer.style.display = 'none';
        if (this.appContainer) this.appContainer.style.display = 'flex';
    }

    private async handleLogin(): Promise<void> {
        const tokenInput = document.getElementById('userToken') as HTMLInputElement;
        const userToken = tokenInput?.value.trim();

        if (!userToken) {
            this.showLoginError('Please enter a user token');
            return;
        }

        try {
            await this.authManager.login(userToken);
            this.showAppScreen();
            await this.init();
        } catch (error) {
            console.error('Login failed:', error);
            this.showLoginError('Invalid user token. Please try again.');
        }
    }

    private showLoginError(message: string): void {
        if (this.loginError) {
            this.loginError.textContent = message;
            this.loginError.style.display = 'block';
        }
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
            this.updateButtonStates();
        });
        this.newChatBtn.addEventListener('click', () => {
            if (!this.isCreatingSession) {
                this.createNewSession();
            }
        });
    }

    private async createNewSession(): Promise<void> {
        this.isCreatingSession = true;
        this.updateButtonStates();
        this.uiManager.showLoadingState('Setting up your new chat...', 'Initializing tools and preparing the session for you.');
        try {
            await this.sessionManager.createNewSession();
        } catch (error) {
            console.error('Failed to create new session:', error);
            this.uiManager.showError('Failed to create new chat session. Please try again.');
            this.handleEmptyState();
        } finally {
            this.isCreatingSession = false;
            this.updateButtonStates();
            this.messageInput.focus();
        }
    }

    private async sendMessage(): Promise<void> {
        const content = this.messageInput.value.trim();
        if (!content || !this.sessionManager.currentSession) return;

        this.isSendingMessage = true;
        this.updateButtonStates();

        if (!this.sessionManager.currentSession.sessionId) {
            console.log('Creating backend session for existing frontend session...');
            try {
                const sessionData = await this.apiManager.createNewBackendSession();
                this.sessionManager.currentSession.sessionId = sessionData.session_id;
                await this.toolsManager.loadTools();
            } catch (error) {
                this.uiManager.showError('Failed to create backend session. Please try again.');
                this.isSendingMessage = false;
                this.updateButtonStates();
                return;
            }
        }

        const userMessage: Message = { id: this.generateId(), content, role: 'user', timestamp: new Date() };
        this.sessionManager.addMessageToCurrentSession(userMessage);
        this.uiManager.displayMessage(userMessage);
        this.messageInput.value = '';
        this.adjustTextareaHeight();
        this.updateButtonStates();
        this.uiManager.showTypingIndicator();

        try {
            const apiResponse = await this.apiManager.ask(this.sessionManager.currentSession.sessionId!, content);
            this.uiManager.hideTypingIndicator();
            const assistantMessage: Message = {
                id: this.generateId(),
                content: apiResponse.response,
                role: 'assistant',
                timestamp: new Date(),
                usedTools: apiResponse.usedTools
            };
            this.sessionManager.addMessageToCurrentSession(assistantMessage);
            this.uiManager.displayMessage(assistantMessage);
            this.sessionManager.updateSessionTitle();
            if (this.sessionManager.currentSession.debugEnabled) {
                await this.debugManager.loadDebugEvents();
            }
        } catch (error) {
            this.uiManager.hideTypingIndicator();
            this.uiManager.showError('Failed to get response. Please try again.');
        } finally {
            this.isSendingMessage = false;
            this.updateButtonStates();
        }
    }

    private async onSessionChanged(): Promise<void> {
        this.uiManager.clearMessages();
        if (this.sessionManager.currentSession) {
            this.sessionManager.currentSession.messages.forEach(msg => this.uiManager.displayMessage(msg));
            if (this.sessionManager.currentSession.messages.length === 0) {
                this.uiManager.showWelcomeMessage();
            }
            await this.toolsManager.loadTools();
            await this.debugManager.restoreDebugState();
        } else {
            this.handleEmptyState();
        }
        this.updateButtonStates();
    }

    private handleEmptyState(): void {
        this.uiManager.showEmptyState(() => this.createNewSession());
        this.toolsManager.loadTools(); // This will render the 'no session' state
        this.debugManager.restoreDebugState(); // This will render the 'no session' state
    }

    private updateButtonStates(): void {
        const hasContent = this.messageInput.value.trim().length > 0;
        const hasActiveSession = this.sessionManager.currentSession !== null;
        const isLoading = this.isSendingMessage || this.isCreatingSession || this.isVerifyingSession;

        this.sendBtn.disabled = !hasContent || !hasActiveSession || isLoading;
        this.messageInput.disabled = isLoading || !hasActiveSession;
        this.messageInput.placeholder = isLoading ? 'Please wait...' : (hasActiveSession ? 'Type your message...' : 'Create a new chat to start messaging...');
        this.messageInput.classList.toggle('loading', isLoading);

        this.newChatBtn.disabled = this.isCreatingSession;
        this.newChatBtn.classList.toggle('loading', this.isCreatingSession);
        const newChatIcon = this.newChatBtn.querySelector('svg');
        const newChatSpan = this.newChatBtn.querySelector('span');
        if (newChatIcon) newChatIcon.style.display = this.isCreatingSession ? 'none' : 'block';
        if (newChatSpan) newChatSpan.textContent = this.isCreatingSession ? 'Creating...' : 'New chat';
    }

    private adjustTextareaHeight(): void {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    private generateId(): string {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
}

// =================================================================================
// APP INITIALIZATION
// =================================================================================
document.addEventListener('DOMContentLoaded', () => {
    const chatApp = new AgentApp();
    (window as any).chatApp = chatApp;
});
