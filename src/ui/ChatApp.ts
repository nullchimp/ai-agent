class ChatApp {
    private eventEmitter: EventEmitter;
    private apiBaseUrl: string = '/api';
    
    // Components
    private sessionComponent: SessionComponent;
    private toolsComponent: ToolsComponent;
    private debugComponent: DebugComponent;
    private chatComponent: ChatComponent;

    constructor() {
        this.eventEmitter = new EventEmitter();
        
        // Initialize components in correct order
        this.sessionComponent = new SessionComponent(this.eventEmitter, this.apiBaseUrl);
        this.toolsComponent = new ToolsComponent(this.eventEmitter, this.apiBaseUrl);
        this.debugComponent = new DebugComponent(this.eventEmitter, this.apiBaseUrl, this.sessionComponent);
        this.chatComponent = new ChatComponent(
            this.eventEmitter,
            this.apiBaseUrl,
            this.sessionComponent,
            this.toolsComponent,
            this.debugComponent
        );

        this.setupComponentCommunication();
    }

    private setupComponentCommunication(): void {
        // When session changes, update all components
        this.eventEmitter.on('session-changed', ({ session }) => {
            // Update button states when session changes
            this.chatComponent.updateButtonStates();
        });

        // When tools are loaded, update button states
        this.eventEmitter.on('tools-loaded', ({ tools }) => {
            this.chatComponent.updateButtonStates();
        });

        // When debug state changes, update any necessary UI
        this.eventEmitter.on('debug-state-changed', ({ enabled, panelOpen }) => {
            // Could update debug toggle button appearance here if needed
            console.log(`Debug state changed: enabled=${enabled}, panelOpen=${panelOpen}`);
        });

        // When a message is sent, focus back on input
        this.eventEmitter.on('message-sent', ({ message }) => {
            this.chatComponent.focusInput();
        });

        // When typing indicator changes
        this.eventEmitter.on('typing-indicator', ({ show }) => {
            // Could update UI to show typing indicator in other places
        });
    }

    async init(): Promise<void> {
        console.log('ChatApp initializing...');
        
        try {
            // Initialize session component first (handles session loading/creation)
            await this.sessionComponent.init();
            
            // Focus input after everything is loaded
            this.chatComponent.focusInput();
            
            console.log('ChatApp initialized successfully');
        } catch (error) {
            console.error('Failed to initialize ChatApp:', error);
        }
    }

    // Public API for external access if needed
    getSessionComponent(): SessionComponent {
        return this.sessionComponent;
    }

    getToolsComponent(): ToolsComponent {
        return this.toolsComponent;
    }

    getDebugComponent(): DebugComponent {
        return this.debugComponent;
    }

    getChatComponent(): ChatComponent {
        return this.chatComponent;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    const app = new ChatApp();
    await app.init();
    
    // Make app globally available for debugging
    (window as any).chatApp = app;
});