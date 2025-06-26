// =================================================================================
// I. INTERFACES & TYPE DECLARATIONS
// =================================================================================
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
    sessionId?: string;  // Backend session ID
    title: string;
    messages: Message[];
    createdAt: Date;
    debugPanelOpen?: boolean;
    debugEnabled?: boolean;
}

interface DebugEvent {
    event_type: string;
    message: string;
    data: Record<string, any>;
    timestamp: string;
    session_id?: string;
}

// =================================================================================
// II. API MANAGER
// =================================================================================
class ApiManager {
    private apiBaseUrl = 'http://localhost:5555/api';

    public async createNewBackendSession(): Promise<{ session_id: string }> {
        const response = await fetch(`${this.apiBaseUrl}/session/new`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        if (!response.ok) {
            throw new Error(`Failed to create session: ${response.status}`);
        }
        return response.json();
    }

    public async verifyBackendSession(sessionId: string): Promise<any> {
        const response = await fetch(`${this.apiBaseUrl}/session/${sessionId}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' }
        });
        if (response.ok) {
            return response.json();
        }
        throw new Error(`Backend session ${sessionId} not found`);
    }
    
    public async deleteBackendSession(sessionId: string): Promise<void> {
        const deleteUrl = `${this.apiBaseUrl}/session/${sessionId}`;
        console.log(`Deleting backend session at: ${deleteUrl}`);
        const response = await fetch(deleteUrl, { method: 'DELETE' });
        if (!response.ok && response.status !== 404) {
            console.warn(`Failed to delete backend session ${sessionId}: ${response.status}`);
        } else {
            console.log(`Successfully deleted backend session ${sessionId}`);
        }
    }

    public async ask(sessionId: string, message: string): Promise<{ response: string, usedTools: string[] }> {
        const apiUrl = `${this.apiBaseUrl}/${sessionId}/ask`;
        console.log(`Making API call to: ${apiUrl}`);
        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-API-Key': 'test_12345' },
                body: JSON.stringify({ query: message })
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
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

    public async loadTools(sessionId: string): Promise<Tool[]> {
        const toolsUrl = `${this.apiBaseUrl}/${sessionId}/tools`;
        console.log(`Loading tools from: ${toolsUrl}`);
        try {
            const response = await fetch(toolsUrl, { headers: { 'X-API-Key': 'test_12345' } });
            if (response.ok) {
                const data = await response.json();
                return data.tools || [];
            }
            console.error(`Failed to load tools: ${response.status}`);
        } catch (error) {
            console.error('Failed to load tools:', error);
        }
        return [];
    }

    public async toggleTool(sessionId: string, toolName: string, enabled: boolean): Promise<boolean> {
        const toggleUrl = `${this.apiBaseUrl}/${sessionId}/tools/toggle`;
        console.log(`Toggling tool ${toolName} to ${enabled} at: ${toggleUrl}`);
        try {
            const response = await fetch(toggleUrl, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-API-Key': 'test_12345' },
                body: JSON.stringify({ tool_name: toolName, enabled: enabled })
            });
            if (response.ok) {
                console.log(`Successfully toggled tool ${toolName} to ${enabled}`);
                return true;
            }
            console.error('Failed to toggle tool:', await response.text());
        } catch (error) {
            console.error('Error toggling tool:', error);
        }
        return false;
    }

    public async setDebugMode(sessionId: string, enabled: boolean): Promise<{ enabled: boolean } | null> {
        try {
            const response = await fetch(`${this.apiBaseUrl}/${sessionId}/debug/toggle`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-API-Key': 'test_12345' },
                body: JSON.stringify({ enabled: enabled })
            });
            if (response.ok) {
                return await response.json();
            }
            console.error('Failed to set debug mode:', await response.text());
        } catch (error) {
            console.error('Error setting debug mode:', error);
        }
        return null;
    }

    public async loadDebugEvents(sessionId: string): Promise<{ events: DebugEvent[], enabled: boolean } | null> {
        try {
            const response = await fetch(`${this.apiBaseUrl}/${sessionId}/debug`, {
                headers: { 'X-API-Key': 'test_12345' }
            });
            if (response.ok) {
                return await response.json();
            }
            console.error('Failed to load debug events:', await response.text());
        } catch (error) {
            console.error('Error loading debug events:', error);
        }
        return null;
    }

    public async clearDebugEvents(sessionId: string): Promise<boolean> {
        try {
            const response = await fetch(`${this.apiBaseUrl}/${sessionId}/debug`, {
                method: 'DELETE',
                headers: { 'X-API-Key': 'test_12345' }
            });
            if (response.ok) {
                return true;
            }
            console.error('Failed to clear debug events:', await response.text());
        } catch (error) {
            console.error('Error clearing debug events:', error);
        }
        return false;
    }
}

// =================================================================================
// III. SESSION MANAGER
// =================================================================================
class SessionManager {
    public sessions: ChatSession[] = [];
    public currentSession: ChatSession | null = null;
    private chatHistory: HTMLElement;

    constructor(private apiManager: ApiManager, private onSessionChanged: () => Promise<void>) {
        this.chatHistory = document.getElementById('chatHistory') as HTMLElement;
        this.loadChatHistory();
    }

    public async createNewSession(): Promise<ChatSession> {
        const sessionData = await this.apiManager.createNewBackendSession();
        const session: ChatSession = {
            id: this.generateId(),
            sessionId: sessionData.session_id,
            title: 'New Chat',
            messages: [],
            createdAt: new Date(),
            debugPanelOpen: false,
            debugEnabled: false
        };

        this.sessions.unshift(session);
        this.currentSession = session;
        this.saveChatHistory();
        this.renderChatHistory();
        await this.onSessionChanged();
        return session;
    }

    public async loadSession(sessionId: string): Promise<void> {
        const session = this.sessions.find(s => s.id === sessionId);
        if (!session) return;

        this.currentSession = session;
        this.renderChatHistory();
        await this.onSessionChanged();
    }

    public async deleteSession(sessionId: string): Promise<void> {
        const sessionIndex = this.sessions.findIndex(s => s.id === sessionId);
        if (sessionIndex === -1) return;

        const session = this.sessions[sessionIndex];
        if (session.sessionId) {
            try {
                await this.apiManager.deleteBackendSession(session.sessionId);
            } catch (error) {
                console.error('Failed to delete backend session:', error);
            }
        }

        this.sessions.splice(sessionIndex, 1);

        if (this.currentSession?.id === sessionId) {
            if (this.sessions.length > 0) {
                await this.loadSession(this.sessions[0].id);
            } else {
                this.currentSession = null;
                await this.onSessionChanged();
            }
        }

        this.saveChatHistory();
        this.renderChatHistory();
    }

    public updateSessionTitle(): void {
        if (!this.currentSession || this.currentSession.messages.length === 0) return;

        const firstUserMessage = this.currentSession.messages.find(m => m.role === 'user');
        if (firstUserMessage && this.currentSession.title === 'New Chat') {
            this.currentSession.title = firstUserMessage.content.substring(0, 50) +
                (firstUserMessage.content.length > 50 ? '...' : '');
            this.renderChatHistory();
            this.saveChatHistory();
        }
    }

    public addMessageToCurrentSession(message: Message): void {
        if (!this.currentSession) return;
        this.currentSession.messages.push(message);
        this.saveChatHistory();
    }

    public renderChatHistory(): void {
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

            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'chat-delete-btn';
            deleteBtn.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <polyline points="3,6 5,6 21,6"></polyline>
                    <path d="M19,6V20a2,2,0,0,1-2,2H7a2,2,0,0,1-2-2V6M8,6V4a2,2,0,0,1,2-2h4a2,2,0,0,1,2,2V6"></path>
                    <line x1="10" y1="11" x2="10" y2="17"></line>
                    <line x1="14" y1="11" x2="14" y2="17"></line>
                </svg>`;
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

    public async verifyCurrentSession(): Promise<void> {
        if (this.currentSession?.sessionId) {
            try {
                await this.apiManager.verifyBackendSession(this.currentSession.sessionId);
                console.log(`Backend session ${this.currentSession.sessionId} verified.`);
            } catch (error) {
                console.warn(`Backend session ${this.currentSession.sessionId} not found, will create new session when needed.`);
                this.currentSession.sessionId = undefined;
                this.saveChatHistory();
            }
        }
    }

    private saveChatHistory(): void {
        try {
            const sessionsToSave = this.sessions.map(s => ({ ...s }));
            localStorage.setItem('chatSessions', JSON.stringify(sessionsToSave));
        } catch (error) {
            console.error('Failed to save chat history:', error);
        }
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
                if (this.sessions.length > 0) {
                    this.currentSession = this.sessions[0];
                }
            } catch (error) {
                console.error('Failed to load chat history:', error);
                this.sessions = [];
            }
        }
    }

    private generateId(): string {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }
}

// =================================================================================
// IV. TOOLS MANAGER
// =================================================================================
class ToolsManager {
    private tools: Tool[] = [];
    private toolsHeader: HTMLElement;
    private toolsList: HTMLElement;
    private toolCategoryStates: Record<string, boolean> = {};

    constructor(private apiManager: ApiManager, private sessionManager: SessionManager) {
        this.toolsHeader = document.getElementById('toolsHeader') as HTMLElement;
        this.toolsList = document.getElementById('toolsList') as HTMLElement;
        this.toolsHeader.addEventListener('click', () => this.toggleToolsSection());
    }

    public async loadTools(): Promise<void> {
        if (!this.sessionManager.currentSession?.sessionId) {
            this.tools = [];
            this.renderTools();
            return;
        }
        this.renderToolsLoading();
        this.tools = await this.apiManager.loadTools(this.sessionManager.currentSession.sessionId);
        this.renderTools();
    }

    public async toggleTool(toolName: string, enabled: boolean): Promise<void> {
        if (!this.sessionManager.currentSession?.sessionId) return;
        const success = await this.apiManager.toggleTool(this.sessionManager.currentSession.sessionId, toolName, enabled);
        if (success) {
            const tool = this.tools.find(t => t.name === toolName);
            if (tool) {
                tool.enabled = enabled;
                this.updateToolsUI();
            }
        }
    }

    public async toggleSourceTools(source: string, enabled: boolean): Promise<void> {
        if (!this.sessionManager.currentSession?.sessionId) return;
        const sourceTools = this.tools.filter(tool => (tool.source || 'default') === source);
        for (const tool of sourceTools) {
            if (tool.enabled !== enabled) {
                await this.toggleTool(tool.name, enabled);
            }
        }
    }

    private toggleToolsSection(): void {
        const isExpanded = this.toolsHeader.classList.toggle('expanded');
        this.toolsList.classList.toggle('expanded', isExpanded);
    }

    private renderToolsLoading(): void {
        this.toolsList.innerHTML = `<div class="tools-loading"><div class="loading-spinner"></div><span>Loading tools...</span></div>`;
        const toolsLabelSpan = this.toolsHeader.querySelector('.tools-label span');
        if (toolsLabelSpan) toolsLabelSpan.textContent = 'Tools Configuration [Loading...]';
    }

    private renderTools(): void {
        this.toolsList.innerHTML = '';
        if (!this.sessionManager.currentSession) {
            this.toolsList.innerHTML = `<div class="tools-no-session"><div class="tools-no-session-message">No active session. Create a new chat to configure tools.</div></div>`;
            const toolsLabelSpan = this.toolsHeader.querySelector('.tools-label span');
            if (toolsLabelSpan) toolsLabelSpan.textContent = 'Tools Configuration [No Session]';
            return;
        }

        const enabledCount = this.tools.filter(tool => tool.enabled).length;
        const totalCount = this.tools.length;
        const toolsLabelSpan = this.toolsHeader.querySelector('.tools-label span');
        if (toolsLabelSpan) toolsLabelSpan.textContent = `Tools Configuration [${enabledCount}/${totalCount}]`;

        const toolsBySource = this.tools.reduce((groups, tool) => {
            const source = tool.source || 'default';
            if (!groups[source]) groups[source] = [];
            groups[source].push(tool);
            return groups;
        }, {} as Record<string, Tool[]>);

        const sortedSources = Object.keys(toolsBySource).sort((a, b) => {
            if (a === 'default') return -1;
            if (b === 'default') return 1;
            return a.localeCompare(b);
        });

        sortedSources.forEach(source => {
            const tools = toolsBySource[source];
            const isExpanded = this.toolCategoryStates[source] !== false;
            const sourceCategory = this.createToolCategory(source, tools, isExpanded);
            this.toolsList.appendChild(sourceCategory);
        });
    }

    private createToolCategory(source: string, tools: Tool[], isExpanded: boolean): HTMLElement {
        const sourceCategory = document.createElement('div');
        sourceCategory.className = `tool-source-category ${isExpanded ? 'expanded' : ''}`;
        sourceCategory.dataset.source = source;

        const sourceHeader = this.createToolCategoryHeader(source, tools, isExpanded);
        sourceCategory.appendChild(sourceHeader);

        const sourceToolsList = document.createElement('div');
        sourceToolsList.className = 'tool-source-tools';
        sourceToolsList.style.display = isExpanded ? 'block' : 'none';
        tools.sort((a, b) => a.name.localeCompare(b.name)).forEach(tool => {
            sourceToolsList.appendChild(this.createToolItem(tool));
        });
        sourceCategory.appendChild(sourceToolsList);

        return sourceCategory;
    }

    private createToolCategoryHeader(source: string, tools: Tool[], isExpanded: boolean): HTMLElement {
        const sourceHeader = document.createElement('div');
        sourceHeader.className = 'tool-source-header';
        const sourceEnabledCount = tools.filter(tool => tool.enabled).length;
        const sourceAllEnabled = sourceEnabledCount === tools.length;

        sourceHeader.innerHTML = `
            <div class="tool-source-expand">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="transform: rotate(${isExpanded ? '90deg' : '0deg'});">
                    <polyline points="9,18 15,12 9,6"></polyline>
                </svg>
            </div>
            <div class="tool-source-title">${source === 'default' ? 'Built-in Tools' : `${source.charAt(0).toUpperCase() + source.slice(1)} Tools`}</div>
            <div class="tool-source-counter">${sourceEnabledCount}/${tools.length}</div>
        `;

        const sourceToggle = document.createElement('div');
        sourceToggle.className = `tool-source-toggle ${sourceAllEnabled ? 'enabled' : ''}`;
        sourceToggle.title = `Toggle all ${source} tools`;
        sourceToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            const currentSourceTools = this.tools.filter(tool => (tool.source || 'default') === source);
            const currentSourceEnabledCount = currentSourceTools.filter(tool => tool.enabled).length;
            this.toggleSourceTools(source, currentSourceEnabledCount !== currentSourceTools.length);
        });
        sourceHeader.appendChild(sourceToggle);

        sourceHeader.addEventListener('click', (e) => {
            if (!sourceToggle.contains(e.target as Node)) {
                this.toggleSourceCategory(source);
            }
        });

        return sourceHeader;
    }

    private createToolItem(tool: Tool): HTMLElement {
        const toolItem = document.createElement('div');
        toolItem.className = `tool-item ${tool.enabled ? 'enabled' : ''}`;
        toolItem.innerHTML = `
            <div class="tool-name">${tool.name}</div>
            <div class="tool-description" title="${tool.description}">${tool.description}</div>
        `;
        const toolToggle = document.createElement('div');
        toolToggle.className = `tool-toggle ${tool.enabled ? 'enabled' : ''}`;
        toolToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleTool(tool.name, !tool.enabled);
        });
        toolItem.appendChild(toolToggle);
        return toolItem;
    }

    private toggleSourceCategory(source: string): void {
        this.toolCategoryStates[source] = !this.toolCategoryStates[source];
        this.updateToolsUI();
    }

    private updateToolsUI(): void {
        const enabledCount = this.tools.filter(tool => tool.enabled).length;
        const toolsLabelSpan = this.toolsHeader.querySelector('.tools-label span');
        if (toolsLabelSpan) toolsLabelSpan.textContent = `Tools Configuration [${enabledCount}/${this.tools.length}]`;

        const sourceCategories = this.toolsList.querySelectorAll('.tool-source-category');
        sourceCategories.forEach(categoryEl => {
            const category = categoryEl as HTMLElement;
            const source = category.dataset.source;
            if (!source) return;

            const isExpanded = this.toolCategoryStates[source] !== false;
            category.classList.toggle('expanded', isExpanded);
            const sourceToolsList = category.querySelector('.tool-source-tools') as HTMLElement;
            if (sourceToolsList) sourceToolsList.style.display = isExpanded ? 'block' : 'none';
            const expandIcon = category.querySelector('.tool-source-expand svg') as SVGElement;
            if (expandIcon) expandIcon.style.transform = `rotate(${isExpanded ? '90deg' : '0deg'})`;

            const sourceTools = this.tools.filter(tool => (tool.source || 'default') === source);
            const sourceEnabledCount = sourceTools.filter(tool => tool.enabled).length;
            const counter = category.querySelector('.tool-source-counter');
            if (counter) counter.textContent = `${sourceEnabledCount}/${sourceTools.length}`;

            const sourceToggle = category.querySelector('.tool-source-toggle');
            if (sourceToggle) sourceToggle.classList.toggle('enabled', sourceEnabledCount === sourceTools.length);

            sourceTools.forEach(tool => {
                const toolItem = Array.from(category.querySelectorAll('.tool-item')).find(item => item.querySelector('.tool-name')?.textContent === tool.name);
                if (toolItem) {
                    toolItem.classList.toggle('enabled', tool.enabled);
                    toolItem.querySelector('.tool-toggle')?.classList.toggle('enabled', tool.enabled);
                }
            });
        });
    }
}

// =================================================================================
// V. DEBUG MANAGER
// =================================================================================
class DebugManager {
    private debugEventsList: DebugEvent[] = [];
    private debugPanelToggle: HTMLButtonElement;
    private debugPanelOverlay: HTMLElement;
    private debugEventsContainer: HTMLElement;
    private debugClearBtn: HTMLButtonElement;
    private debugPanelClose: HTMLButtonElement;
    private debugFullscreenOverlay: HTMLElement;
    private debugFullscreenData: HTMLElement;
    private debugFullscreenTitle: HTMLElement;
    private debugFullscreenClose: HTMLButtonElement;

    constructor(private apiManager: ApiManager, private sessionManager: SessionManager) {
        this.debugPanelToggle = document.getElementById('debugPanelToggle') as HTMLButtonElement;
        this.debugPanelOverlay = document.getElementById('debugPanelOverlay') as HTMLElement;
        this.debugEventsContainer = document.getElementById('debugEvents') as HTMLElement;
        this.debugClearBtn = document.getElementById('debugClearBtn') as HTMLButtonElement;
        this.debugPanelClose = document.getElementById('debugPanelClose') as HTMLButtonElement;
        this.debugFullscreenOverlay = document.getElementById('debugFullscreenOverlay') as HTMLElement;
        this.debugFullscreenData = document.getElementById('debugFullscreenData') as HTMLElement;
        this.debugFullscreenTitle = document.getElementById('debugFullscreenTitle') as HTMLElement;
        this.debugFullscreenClose = document.getElementById('debugFullscreenClose') as HTMLButtonElement;
        this.setupEventListeners();
    }

    private setupEventListeners(): void {
        this.debugPanelToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDebugPanel();
        });
        this.debugPanelClose.addEventListener('click', () => this.closeDebugPanel());
        this.debugClearBtn.addEventListener('click', () => this.clearDebugEvents());
        this.debugFullscreenClose.addEventListener('click', () => this.closeDebugFullscreen());
        this.debugFullscreenOverlay.addEventListener('click', (e) => {
            if (e.target === this.debugFullscreenOverlay) this.closeDebugFullscreen();
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.debugFullscreenOverlay.classList.contains('active')) {
                this.closeDebugFullscreen();
            }
        });
    }

    public async restoreDebugState(): Promise<void> {
        if (!this.sessionManager.currentSession) return;
        const debugPanelShouldBeOpen = this.sessionManager.currentSession.debugPanelOpen;
        if (debugPanelShouldBeOpen) {
            this.debugPanelOverlay.classList.add('active');
            this.debugPanelToggle.classList.add('active');
            document.body.classList.add('debug-panel-open');
            await this.setDebugMode(true);
            await this.loadDebugEvents();
        } else {
            this.debugPanelOverlay.classList.remove('active');
            this.debugPanelToggle.classList.remove('active');
            document.body.classList.remove('debug-panel-open');
            if (this.sessionManager.currentSession.debugEnabled) {
                await this.setDebugMode(true);
            }
        }
    }

    public async loadDebugEvents(): Promise<void> {
        if (!this.sessionManager.currentSession?.sessionId) return;
        const result = await this.apiManager.loadDebugEvents(this.sessionManager.currentSession.sessionId);
        if (result) {
            this.debugEventsList = result.events;
            this.setCurrentDebugEnabled(result.enabled);
            this.updateDebugUI();
            this.renderDebugEvents();
        }
    }

    private async toggleDebugPanel(): Promise<void> {
        const newState = !this.getCurrentDebugPanelState();
        this.setCurrentDebugPanelState(newState);
        if (newState) {
            this.debugPanelOverlay.classList.add('active');
            this.debugPanelToggle.classList.add('active');
            document.body.classList.add('debug-panel-open');
            await this.setDebugMode(true);
            this.loadDebugEvents();
        } else {
            this.closeDebugPanel();
        }
    }

    private async closeDebugPanel(): Promise<void> {
        this.setCurrentDebugPanelState(false);
        this.debugPanelOverlay.classList.remove('active');
        this.debugPanelToggle.classList.remove('active');
        document.body.classList.remove('debug-panel-open');
        await this.setDebugMode(false);
    }

    private async setDebugMode(enabled: boolean): Promise<void> {
        if (!this.sessionManager.currentSession?.sessionId) return;
        const result = await this.apiManager.setDebugMode(this.sessionManager.currentSession.sessionId, enabled);
        if (result) {
            this.setCurrentDebugEnabled(result.enabled);
            this.updateDebugUI();
        }
    }

    private async clearDebugEvents(): Promise<void> {
        if (!this.sessionManager.currentSession?.sessionId) return;
        const success = await this.apiManager.clearDebugEvents(this.sessionManager.currentSession.sessionId);
        if (success) {
            this.debugEventsList = [];
            this.renderDebugEvents();
        }
    }

    private updateDebugUI(): void {
        if (!this.sessionManager.currentSession) {
            this.debugEventsContainer.innerHTML = `<div class="debug-disabled-message">No active session.</div>`;
            return;
        }
        if (!this.getCurrentDebugEnabled()) {
            this.debugEventsContainer.innerHTML = `<div class="debug-disabled-message">Debug mode is automatically enabled when this panel is open.</div>`;
        }
    }

    private renderDebugEvents(): void {
        if (!this.sessionManager.currentSession || !this.getCurrentDebugEnabled()) {
            this.updateDebugUI();
            return;
        }
        if (this.debugEventsList.length === 0) {
            this.debugEventsContainer.innerHTML = `<div class="debug-disabled-message">No debug events captured yet.</div>`;
            return;
        }
        const eventsHtml = this.debugEventsList
            .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
            .map((event, index) => this.createDebugEventElement(event, index))
            .join('');
        this.debugEventsContainer.innerHTML = eventsHtml;
        this.debugEventsContainer.scrollTop = this.debugEventsContainer.scrollHeight;
    }

    private createDebugEventElement(event: DebugEvent, index: number): string {
        const timestamp = new Date(event.timestamp).toLocaleTimeString();
        const colorizedData = this.colorizeJsonData(event.data);
        const escapedMessage = this.escapeHtml(event.message);
        return `
            <div class="debug-event">
                <div class="debug-event-header">
                    <span class="debug-event-type ${event.event_type}">${event.event_type}</span>
                    <span class="debug-event-timestamp">${timestamp}</span>
                    <button class="debug-event-fullscreen-btn" onclick="window.chatApp.debugManager.openDebugFullscreen(${index})">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
                        </svg>
                        Expand
                    </button>
                </div>
                <div class="debug-event-message">${escapedMessage}</div>
                <div class="debug-event-data">${colorizedData}</div>
            </div>`;
    }

    public openDebugFullscreen(eventIndex: number): void {
        const event = this.debugEventsList[eventIndex];
        if (!event) return;
        const timestamp = new Date(event.timestamp).toLocaleString();
        this.debugFullscreenTitle.textContent = `${event.event_type} - ${timestamp}`;
        this.debugFullscreenData.innerHTML = this.colorizeJsonData(event.data);
        this.debugFullscreenOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    private closeDebugFullscreen(): void {
        this.debugFullscreenOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    private colorizeJsonData(obj: any, depth: number = 0, keyPath: string = '', rootColorMetadata: Record<string, string> = {}): string {
        const indent = '  '.repeat(depth);
        if (obj === null) return '<span class="debug-color-grey">null</span>';
        if (typeof obj === 'string') {
            if (obj.endsWith('...[truncated]')) {
                const mainText = obj.substring(0, obj.length - 14);
                return `"<span class="debug-color-white">${this.escapeHtml(mainText)}</span><span class="debug-truncated">...[truncated]</span>"`;
            }
            return `"<span class="debug-color-white">${this.escapeHtml(obj)}</span>"`;
        }
        if (typeof obj === 'number' || typeof obj === 'boolean') {
            return `<span class="debug-color-yellow">${obj}</span>`;
        }
        if (Array.isArray(obj)) {
            if (obj.length === 0) return '[]';
            const items = obj.map(item => `${indent}  ${this.colorizeJsonData(item, depth + 1, keyPath, rootColorMetadata)}`);
            return `[\n${items.join(',\n')}\n${indent}]`;
        }
        if (typeof obj === 'object' && obj !== null) {
            const entries = Object.entries(obj);
            if (entries.length === 0) return '{}';
            const colorMetadata = depth === 0 ? (obj._debug_colors || {}) : rootColorMetadata;
            const items = entries
                .filter(([key]) => key !== '_debug_colors')
                .map(([key, value]) => {
                    const currentKeyPath = keyPath ? `${keyPath}_${key}` : key;
                    const color = colorMetadata[`_${currentKeyPath}_color`];
                    const keyHtml = color ? `<span class="debug-key debug-color-${color}">"${this.escapeHtml(key)}"</span>` : `<span class="debug-key">"${this.escapeHtml(key)}"</span>`;
                    return `${indent}  ${keyHtml}: ${this.colorizeJsonData(value, depth + 1, currentKeyPath, colorMetadata)}`;
                });
            return `{\n${items.join(',\n')}\n${indent}}`;
        }
        return this.escapeHtml(String(obj));
    }

    private escapeHtml(unsafe: string): string {
        return unsafe.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

    private getCurrentDebugPanelState(): boolean {
        return this.sessionManager.currentSession?.debugPanelOpen || false;
    }

    private setCurrentDebugPanelState(open: boolean): void {
        if (this.sessionManager.currentSession) {
            this.sessionManager.currentSession.debugPanelOpen = open;
            // This will be saved by the session manager
        }
    }

    private getCurrentDebugEnabled(): boolean {
        return this.sessionManager.currentSession?.debugEnabled || false;
    }

    private setCurrentDebugEnabled(enabled: boolean): void {
        if (this.sessionManager.currentSession) {
            this.sessionManager.currentSession.debugEnabled = enabled;
            // This will be saved by the session manager
        }
    }
}

// =================================================================================
// VI. CHAT UI MANAGER
// =================================================================================
class ChatUIManager {
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

// =================================================================================
// VII. MAIN CHAT APP
// =================================================================================
class ChatApp {
    public debugManager: DebugManager;
    private apiManager: ApiManager;
    private sessionManager: SessionManager;
    private toolsManager: ToolsManager;
    private uiManager: ChatUIManager;

    private messageInput: HTMLTextAreaElement;
    private sendBtn: HTMLButtonElement;
    private newChatBtn: HTMLButtonElement;

    private isSendingMessage: boolean = false;
    private isCreatingSession: boolean = false;
    private isVerifyingSession: boolean = false;

    constructor() {
        this.messageInput = document.getElementById('messageInput') as HTMLTextAreaElement;
        this.sendBtn = document.getElementById('sendBtn') as HTMLButtonElement;
        this.newChatBtn = document.getElementById('newChatBtn') as HTMLButtonElement;

        this.apiManager = new ApiManager();
        this.uiManager = new ChatUIManager();
        this.sessionManager = new SessionManager(this.apiManager, () => this.onSessionChanged());
        this.toolsManager = new ToolsManager(this.apiManager, this.sessionManager);
        this.debugManager = new DebugManager(this.apiManager, this.sessionManager);

        this.init();
    }

    private async init(): Promise<void> {
        this.setupEventListeners();
        if (this.sessionManager.sessions.length === 0) {
            await this.createNewSession();
        } else {
            this.isVerifyingSession = true;
            this.updateButtonStates();
            this.uiManager.showLoadingState('Verifying session...', 'Checking if your previous session is still available.');
            await this.sessionManager.verifyCurrentSession();
            this.isVerifyingSession = false;
            await this.onSessionChanged();
        }
        this.sessionManager.renderChatHistory();
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
// VIII. APP INITIALIZATION
// =================================================================================
document.addEventListener('DOMContentLoaded', () => {
    const chatApp = new ChatApp();
    (window as any).chatApp = chatApp;
});
