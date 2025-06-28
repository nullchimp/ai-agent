import { Tool } from '../types';
import { ApiManager } from './api';
import { SessionManager } from './session';

export class ToolsManager {
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
