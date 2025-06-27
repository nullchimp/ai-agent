import { DebugEvent } from './types';
import { ApiManager } from './api-manager';
import { SessionManager } from './session-manager';

export class DebugManager {
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

    public openDebugFullscreen(eventIndex: number): void {
        const event = this.debugEventsList[eventIndex];
        if (!event) return;
        const timestamp = new Date(event.timestamp).toLocaleString();
        this.debugFullscreenTitle.textContent = `${event.event_type} - ${timestamp}`;
        this.debugFullscreenData.innerHTML = this.colorizeJsonData(event.data);
        this.debugFullscreenOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
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
        }
    }

    private getCurrentDebugEnabled(): boolean {
        return this.sessionManager.currentSession?.debugEnabled || false;
    }

    private setCurrentDebugEnabled(enabled: boolean): void {
        if (this.sessionManager.currentSession) {
            this.sessionManager.currentSession.debugEnabled = enabled;
        }
    }
}
