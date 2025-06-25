import { DebugEvent } from './types';
import { Utils } from './utils';

export class DebugUIService {
    private debugPanelToggle: HTMLButtonElement;
    private debugPanelOverlay: HTMLElement;
    private debugEventsContainer: HTMLElement;
    private debugClearBtn: HTMLButtonElement;
    private debugPanelClose: HTMLButtonElement;
    private debugFullscreenOverlay: HTMLElement;
    private debugFullscreenData: HTMLElement;
    private debugFullscreenTitle: HTMLElement;
    private debugFullscreenClose: HTMLButtonElement;

    constructor(
        debugPanelToggle: HTMLButtonElement,
        debugPanelOverlay: HTMLElement,
        debugEventsContainer: HTMLElement,
        debugClearBtn: HTMLButtonElement,
        debugPanelClose: HTMLButtonElement,
        debugFullscreenOverlay: HTMLElement,
        debugFullscreenData: HTMLElement,
        debugFullscreenTitle: HTMLElement,
        debugFullscreenClose: HTMLButtonElement
    ) {
        this.debugPanelToggle = debugPanelToggle;
        this.debugPanelOverlay = debugPanelOverlay;
        this.debugEventsContainer = debugEventsContainer;
        this.debugClearBtn = debugClearBtn;
        this.debugPanelClose = debugPanelClose;
        this.debugFullscreenOverlay = debugFullscreenOverlay;
        this.debugFullscreenData = debugFullscreenData;
        this.debugFullscreenTitle = debugFullscreenTitle;
        this.debugFullscreenClose = debugFullscreenClose;
    }

    setupEventListeners(
        onToggleDebugPanel: () => Promise<void>,
        onCloseDebugPanel: () => Promise<void>,
        onClearDebugEvents: () => Promise<void>
    ): void {
        this.debugPanelToggle.addEventListener('click', onToggleDebugPanel);
        this.debugPanelClose.addEventListener('click', onCloseDebugPanel);
        this.debugClearBtn.addEventListener('click', onClearDebugEvents);
        
        this.debugFullscreenClose.addEventListener('click', () => {
            this.closeFullscreenDebug();
        });
        
        this.debugFullscreenOverlay.addEventListener('click', (e) => {
            if (e.target === this.debugFullscreenOverlay) {
                this.closeFullscreenDebug();
            }
        });
    }

    showDebugPanel(): void {
        this.debugPanelOverlay.classList.add('active');
        this.debugPanelToggle.classList.add('active');
        document.body.classList.add('debug-panel-open');
    }

    hideDebugPanel(): void {
        this.debugPanelOverlay.classList.remove('active');
        this.debugPanelToggle.classList.remove('active');
        document.body.classList.remove('debug-panel-open');
    }

    renderDebugEvents(debugEventsList: DebugEvent[]): void {
        this.debugEventsContainer.innerHTML = '';
        
        if (debugEventsList.length === 0) {
            const noEventsMsg = document.createElement('div');
            noEventsMsg.className = 'debug-no-events';
            noEventsMsg.textContent = 'No debug events yet. Send a message to see debug information.';
            this.debugEventsContainer.appendChild(noEventsMsg);
            return;
        }
        
        debugEventsList.forEach((event, index) => {
            const eventEl = document.createElement('div');
            eventEl.className = 'debug-event';
            
            const eventHeader = document.createElement('div');
            eventHeader.className = 'debug-event-header';
            
            const eventType = document.createElement('span');
            eventType.className = 'debug-event-type';
            eventType.textContent = event.event_type;
            
            const eventTime = document.createElement('span');
            eventTime.className = 'debug-event-time';
            eventTime.textContent = new Date(event.timestamp).toLocaleTimeString();
            
            eventHeader.appendChild(eventType);
            eventHeader.appendChild(eventTime);
            
            const eventData = document.createElement('div');
            eventData.className = 'debug-event-data';
            
            const previewData = JSON.stringify(event.data, null, 2);
            const truncatedData = previewData.length > 200 ? 
                previewData.substring(0, 200) + '...' : previewData;
            
            const dataPreview = document.createElement('pre');
            dataPreview.className = 'debug-data-preview';
            dataPreview.innerHTML = Utils.colorizeJsonData(truncatedData);
            
            if (previewData.length > 200) {
                const expandBtn = document.createElement('button');
                expandBtn.className = 'debug-expand-btn';
                expandBtn.textContent = 'View Full Data';
                expandBtn.addEventListener('click', () => {
                    this.showFullscreenDebug(event.event_type, event.data);
                });
                eventData.appendChild(expandBtn);
            }
            
            eventData.appendChild(dataPreview);
            eventEl.appendChild(eventHeader);
            eventEl.appendChild(eventData);
            
            this.debugEventsContainer.appendChild(eventEl);
        });
    }

    private showFullscreenDebug(title: string, data: any): void {
        this.debugFullscreenTitle.textContent = `Debug Event: ${title}`;
        
        const formattedData = Utils.applyColorSchemeToData(data);
        this.debugFullscreenData.innerHTML = formattedData;
        
        this.debugFullscreenOverlay.classList.add('active');
    }

    private closeFullscreenDebug(): void {
        this.debugFullscreenOverlay.classList.remove('active');
    }
}