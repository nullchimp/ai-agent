class DebugComponent {
    private debugEventsList: DebugEvent[] = [];
    private eventEmitter: EventEmitter;
    private apiBaseUrl: string;
    private currentSession: ChatSession | null = null;
    private sessionComponent: SessionComponent;

    // DOM elements
    private debugPanelToggle: HTMLButtonElement;
    private debugPanelOverlay: HTMLElement;
    private debugEventsContainer: HTMLElement;
    private debugClearBtn: HTMLButtonElement;
    private debugPanelClose: HTMLButtonElement;
    private debugFullscreenOverlay: HTMLElement;
    private debugFullscreenData: HTMLElement;
    private debugFullscreenTitle: HTMLElement;
    private debugFullscreenClose: HTMLButtonElement;

    constructor(eventEmitter: EventEmitter, apiBaseUrl: string, sessionComponent: SessionComponent) {
        this.eventEmitter = eventEmitter;
        this.apiBaseUrl = apiBaseUrl;
        this.sessionComponent = sessionComponent;
        
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

        this.setupEventListeners();
    }

    private setupEventListeners(): void {
        // Debug event listeners
        this.debugPanelToggle.addEventListener('click', () => {
            this.toggleDebugPanel();
        });

        this.debugClearBtn.addEventListener('click', () => {
            this.clearDebugEvents();
        });

        this.debugPanelClose.addEventListener('click', () => {
            this.closeDebugPanel();
        });

        // Debug fullscreen event listeners
        this.debugFullscreenClose.addEventListener('click', () => {
            this.closeDebugFullscreen();
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.debugFullscreenOverlay.classList.contains('active')) {
                this.closeDebugFullscreen();
            }
        });

        // Listen for session changes
        this.eventEmitter.on('session-changed', ({ session }) => {
            this.currentSession = session;
            this.restoreDebugState();
        });
    }

    async restoreDebugState(): Promise<void> {
        const debugPanelOpen = this.sessionComponent.getCurrentDebugPanelState();
        const debugEnabled = this.sessionComponent.getCurrentDebugEnabled();
        
        // Restore debug panel state
        if (debugPanelOpen) {
            this.debugPanelOverlay.classList.add('active');
            this.debugPanelToggle.classList.add('active');
            document.body.classList.add('debug-panel-open');
        } else {
            this.debugPanelOverlay.classList.remove('active');
            this.debugPanelToggle.classList.remove('active');
            document.body.classList.remove('debug-panel-open');
        }
        
        // Update debug toggle button
        const debugToggleBtn = this.debugPanelOverlay.querySelector('.debug-toggle-btn') as HTMLButtonElement;
        if (debugToggleBtn) {
            if (debugEnabled) {
                debugToggleBtn.classList.add('enabled');
                debugToggleBtn.textContent = 'Debug: ON';
            } else {
                debugToggleBtn.classList.remove('enabled');
                debugToggleBtn.textContent = 'Debug: OFF';
            }
        }
        
        // Load debug events if debug is enabled
        if (debugEnabled) {
            await this.loadDebugEvents();
        } else {
            this.updateDebugUI();
        }

        // Emit debug state changed event
        this.eventEmitter.emit('debug-state-changed', { 
            enabled: debugEnabled, 
            panelOpen: debugPanelOpen 
        });
    }

    private async toggleDebugPanel(): Promise<void> {
        const isOpen = this.debugPanelOverlay.classList.contains('active');
        
        if (isOpen) {
            await this.closeDebugPanel();
        } else {
            this.debugPanelOverlay.classList.add('active');
            this.debugPanelToggle.classList.add('active');
            document.body.classList.add('debug-panel-open');
            
            this.sessionComponent.setCurrentDebugPanelState(true);
            
            // Load debug events when opening
            if (this.sessionComponent.getCurrentDebugEnabled()) {
                await this.loadDebugEvents();
            } else {
                this.updateDebugUI();
            }
        }
    }

    private async closeDebugPanel(): Promise<void> {
        this.debugPanelOverlay.classList.remove('active');
        this.debugPanelToggle.classList.remove('active');
        document.body.classList.remove('debug-panel-open');
        
        this.sessionComponent.setCurrentDebugPanelState(false);
    }

    private async setDebugMode(enabled: boolean): Promise<void> {
        if (!this.currentSession?.sessionId) {
            console.log('No session ID available for setting debug mode');
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/${this.currentSession.sessionId}/debug/toggle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': 'test_12345'
                },
                body: JSON.stringify({ enabled })
            });

            if (response.ok) {
                this.sessionComponent.setCurrentDebugEnabled(enabled);
                
                const debugToggleBtn = this.debugPanelOverlay.querySelector('.debug-toggle-btn') as HTMLButtonElement;
                if (debugToggleBtn) {
                    if (enabled) {
                        debugToggleBtn.classList.add('enabled');
                        debugToggleBtn.textContent = 'Debug: ON';
                    } else {
                        debugToggleBtn.classList.remove('enabled');
                        debugToggleBtn.textContent = 'Debug: OFF';
                    }
                }
                
                await this.loadDebugEvents();
            } else {
                console.error('Failed to set debug mode:', response.status);
            }
        } catch (error) {
            console.error('Error setting debug mode:', error);
        }
    }

    private async clearDebugEvents(): Promise<void> {
        if (!this.currentSession?.sessionId) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/${this.currentSession.sessionId}/debug/clear`, {
                method: 'POST',
                headers: {
                    'X-API-Key': 'test_12345'
                }
            });

            if (response.ok) {
                this.debugEventsList = [];
                this.updateDebugUI();
            } else {
                console.error('Failed to clear debug events:', response.status);
            }
        } catch (error) {
            console.error('Error clearing debug events:', error);
        }
    }

    async loadDebugEvents(): Promise<void> {
        if (!this.currentSession?.sessionId) {
            this.debugEventsList = [];
            this.updateDebugUI();
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/${this.currentSession.sessionId}/debug/events`, {
                headers: {
                    'X-API-Key': 'test_12345'
                }
            });

            if (response.ok) {
                const data: DebugInfo = await response.json();
                this.debugEventsList = data.events || [];
                this.updateDebugUI();
            } else {
                console.error('Failed to load debug events:', response.status);
                this.debugEventsList = [];
                this.updateDebugUI();
            }
        } catch (error) {
            console.error('Error loading debug events:', error);
            this.debugEventsList = [];
            this.updateDebugUI();
        }
    }

    private updateDebugUI(): void {
        if (!this.sessionComponent.getCurrentDebugEnabled()) {
            this.debugEventsContainer.innerHTML = `
                <div class="debug-disabled-message">
                    Debug mode is disabled. Enable it to see debug events.
                </div>
            `;
            return;
        }

        if (this.debugEventsList.length === 0) {
            this.debugEventsContainer.innerHTML = `
                <div class="debug-disabled-message">
                    No debug events captured yet.
                </div>
            `;
            return;
        }

        this.renderDebugEvents();
    }

    private renderDebugEvents(): void {
        this.debugEventsContainer.innerHTML = '';
        
        this.debugEventsList.forEach((event, index) => {
            const eventEl = document.createElement('div');
            eventEl.className = 'debug-event';
            
            const header = document.createElement('div');
            header.className = 'debug-event-header';
            
            const eventType = document.createElement('span');
            eventType.className = `debug-event-type ${event.event_type}`;
            eventType.textContent = event.event_type.replace(/_/g, ' ');
            
            const timestamp = document.createElement('span');
            timestamp.className = 'debug-event-timestamp';
            timestamp.textContent = new Date(event.timestamp).toLocaleTimeString();
            
            const fullscreenBtn = document.createElement('button');
            fullscreenBtn.className = 'debug-event-fullscreen-btn';
            fullscreenBtn.innerHTML = '⤢';
            fullscreenBtn.title = 'View fullscreen';
            fullscreenBtn.onclick = () => this.showDebugFullscreen(event);
            
            header.appendChild(eventType);
            header.appendChild(timestamp);
            header.appendChild(fullscreenBtn);
            
            const content = document.createElement('div');
            content.className = 'debug-event-content';
            
            const message = document.createElement('div');
            message.className = 'debug-event-message';
            message.textContent = event.message;
            
            content.appendChild(message);
            
            if (event.data && Object.keys(event.data).length > 0) {
                const dataEl = document.createElement('div');
                dataEl.className = 'debug-event-data';
                dataEl.innerHTML = this.applyColorSchemeToData(event.data);
                content.appendChild(dataEl);
            }
            
            eventEl.appendChild(header);
            eventEl.appendChild(content);
            
            this.debugEventsContainer.appendChild(eventEl);
        });
        
        // Scroll to bottom
        this.debugEventsContainer.scrollTop = this.debugEventsContainer.scrollHeight;
    }

    private applyColorSchemeToData(data: Record<string, any>): string {
        const rootColorMetadata = this.findRootColorMetadata(data);
        return this.colorizeJsonData(data, 0, '', rootColorMetadata);
    }

    private colorizeJsonData(obj: any, depth: number = 0, keyPath: string = '', rootColorMetadata: Record<string, string> = {}): string {
        const indent = '  '.repeat(depth);
        
        if (obj === null) return '<span class="debug-color-grey">null</span>';
        if (obj === undefined) return '<span class="debug-color-grey">undefined</span>';
        
        if (typeof obj === 'string') {
            // Check if this is a truncated string
            if (obj.includes('... (truncated)')) {
                return `<span class="debug-truncated">"${this.escapeHtml(obj)}"</span>`;
            }
            
            // Apply color based on root metadata
            const colorClass = rootColorMetadata[keyPath] || 'debug-color-white';
            return `<span class="${colorClass}">"${this.escapeHtml(obj)}"</span>`;
        }
        
        if (typeof obj === 'number') {
            return `<span class="debug-color-cyan">${obj}</span>`;
        }
        
        if (typeof obj === 'boolean') {
            return `<span class="debug-color-yellow">${obj}</span>`;
        }
        
        if (Array.isArray(obj)) {
            if (obj.length === 0) return '[]';
            
            const items = obj.map((item, index) => {
                const itemPath = keyPath ? `${keyPath}[${index}]` : `[${index}]`;
                return `${indent}  ${this.colorizeJsonData(item, depth + 1, itemPath, rootColorMetadata)}`;
            }).join(',\n');
            
            return `[\n${items}\n${indent}]`;
        }
        
        if (typeof obj === 'object') {
            const keys = Object.keys(obj);
            if (keys.length === 0) return '{}';
            
            const items = keys.map(key => {
                const value = obj[key];
                const valuePath = keyPath ? `${keyPath}.${key}` : key;
                const colorizedValue = this.colorizeJsonData(value, depth + 1, valuePath, rootColorMetadata);
                return `${indent}  <span class="debug-key debug-color-blue">"${this.escapeHtml(key)}"</span>: ${colorizedValue}`;
            }).join(',\n');
            
            return `{\n${items}\n${indent}}`;
        }
        
        return String(obj);
    }

    private findRootColorMetadata(obj: any): Record<string, string> {
        const colorMap: Record<string, string> = {};
        
        if (typeof obj === 'object' && obj !== null) {
            // Look for color metadata at the root level
            const colorFields = ['color', 'type', 'level', 'status', 'result'];
            
            colorFields.forEach(field => {
                if (obj[field]) {
                    const value = String(obj[field]).toLowerCase();
                    if (value.includes('error')) colorMap[field] = 'debug-color-red';
                    else if (value.includes('success')) colorMap[field] = 'debug-color-green';
                    else if (value.includes('warning')) colorMap[field] = 'debug-color-yellow';
                    else if (value.includes('info')) colorMap[field] = 'debug-color-blue';
                    else colorMap[field] = 'debug-color-white';
                }
            });
        }
        
        return colorMap;
    }

    private showDebugFullscreen(event: DebugEvent): void {
        this.debugFullscreenTitle.textContent = `${event.event_type.replace(/_/g, ' ')} - ${new Date(event.timestamp).toLocaleString()}`;
        this.debugFullscreenData.textContent = JSON.stringify(event.data, null, 2);
        this.debugFullscreenOverlay.classList.add('active');
    }

    private closeDebugFullscreen(): void {
        this.debugFullscreenOverlay.classList.remove('active');
    }

    private escapeHtml(unsafe: string): string {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Public methods to interact with debug functionality
    getCurrentDebugEnabled(): boolean {
        return this.sessionComponent.getCurrentDebugEnabled();
    }

    async toggleDebugMode(): Promise<void> {
        const currentState = this.sessionComponent.getCurrentDebugEnabled();
        await this.setDebugMode(!currentState);
    }
}