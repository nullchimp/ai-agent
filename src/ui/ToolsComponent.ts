class ToolsComponent {
    private tools: Tool[] = [];
    private eventEmitter: EventEmitter;
    private apiBaseUrl: string;
    private currentSession: ChatSession | null = null;
    private isLoadingTools: boolean = false;
    private toolCategoryStates: Record<string, boolean> = {};

    // DOM elements
    private toolsHeader: HTMLElement;
    private toolsList: HTMLElement;

    constructor(eventEmitter: EventEmitter, apiBaseUrl: string) {
        this.eventEmitter = eventEmitter;
        this.apiBaseUrl = apiBaseUrl;
        
        this.toolsHeader = document.getElementById('toolsHeader') as HTMLElement;
        this.toolsList = document.getElementById('toolsList') as HTMLElement;

        this.setupEventListeners();
        this.loadToolCategoryStates();
    }

    private setupEventListeners(): void {
        this.toolsHeader.addEventListener('click', () => {
            this.toggleToolsSection();
        });

        // Listen for session changes
        this.eventEmitter.on('session-changed', ({ session }) => {
            this.currentSession = session;
            this.loadTools();
        });
    }

    private toggleToolsSection(): void {
        const toolsHeader = this.toolsHeader;
        const toolsList = this.toolsList;
        
        const isExpanded = toolsHeader.classList.contains('expanded');
        
        if (isExpanded) {
            toolsHeader.classList.remove('expanded');
            toolsList.classList.remove('expanded');
        } else {
            toolsHeader.classList.add('expanded');
            toolsList.classList.add('expanded');
        }
    }

    // Tool management methods
    async loadTools(): Promise<void> {
        if (!this.currentSession?.sessionId) {
            console.log('No session ID available for loading tools');
            this.tools = [];
            this.renderTools();
            return;
        }

        this.isLoadingTools = true;
        this.renderToolsLoading();

        const toolsUrl = `${this.apiBaseUrl}/${this.currentSession.sessionId}/tools`;
        console.log(`Loading tools from: ${toolsUrl}`);

        try {
            const response = await fetch(toolsUrl, {
                headers: {
                    'X-API-Key': 'test_12345'
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.tools = data.tools || [];
                console.log(`Loaded ${this.tools.length} tools:`, this.tools.map(t => t.name));
                this.eventEmitter.emit('tools-loaded', { tools: this.tools });
            } else {
                console.error(`Failed to load tools: ${response.status}`);
                this.tools = [];
            }
        } catch (error) {
            console.error('Failed to load tools:', error);
            this.tools = [];
        } finally {
            this.isLoadingTools = false;
            this.renderTools();
        }
    }

    private renderToolsLoading(): void {
        this.toolsList.innerHTML = `
            <div class="tools-loading">
                <div class="loading-spinner"></div>
                Loading tools...
            </div>
        `;
    }

    private renderTools(): void {
        if (!this.currentSession?.sessionId) {
            this.toolsList.innerHTML = `
                <div class="tools-no-session">
                    <div class="tools-no-session-message">Create a new chat to see available tools</div>
                </div>
            `;
            return;
        }

        if (this.tools.length === 0) {
            this.toolsList.innerHTML = `
                <div class="tools-no-session">
                    <div class="tools-no-session-message">No tools available for this session</div>
                </div>
            `;
            return;
        }

        // Group tools by source
        const toolsBySource = this.tools.reduce((acc, tool) => {
            const source = tool.source || 'default';
            if (!acc[source]) {
                acc[source] = [];
            }
            acc[source].push(tool);
            return acc;
        }, {} as Record<string, Tool[]>);

        this.toolsList.innerHTML = '';

        // Add disable all option
        const disableAllItem = document.createElement('div');
        disableAllItem.className = 'disable-all-item';
        disableAllItem.innerHTML = `
            <div class="disable-all-name">Disable All Tools</div>
            <div class="disable-all-description">Turn off all tools to chat without any tool usage</div>
            <div class="tool-toggle" data-tool="disable-all"></div>
        `;
        this.toolsList.appendChild(disableAllItem);

        // Create source categories
        Object.entries(toolsBySource).forEach(([source, sourceTools]) => {
            const sourceCategory = document.createElement('div');
            sourceCategory.className = 'tool-source-category';
            sourceCategory.dataset.source = source;

            const sourceHeader = document.createElement('div');
            sourceHeader.className = 'tool-source-header';
            
            const enabledCount = sourceTools.filter(tool => tool.enabled).length;
            const totalCount = sourceTools.length;
            
            sourceHeader.innerHTML = `
                <div class="tool-source-expand">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="9,18 15,12 9,6"></polyline>
                    </svg>
                </div>
                <div class="tool-source-title">${source}</div>
                <div class="tool-source-counter">${enabledCount}/${totalCount}</div>
                <div class="tool-source-toggle" data-source="${source}"></div>
            `;

            const sourceToolsList = document.createElement('div');
            sourceToolsList.className = 'tool-source-tools';
            sourceToolsList.style.display = 'none';

            sourceTools.forEach(tool => {
                const toolItem = document.createElement('div');
                toolItem.className = 'tool-item';
                if (tool.enabled) {
                    toolItem.classList.add('enabled');
                }

                toolItem.innerHTML = `
                    <div class="tool-name">${tool.name}</div>
                    <div class="tool-description">${tool.description}</div>
                    <div class="tool-toggle" data-tool="${tool.name}"></div>
                `;

                sourceToolsList.appendChild(toolItem);
            });

            sourceCategory.appendChild(sourceHeader);
            sourceCategory.appendChild(sourceToolsList);

            // Add click handlers
            sourceHeader.addEventListener('click', () => {
                this.toggleSourceCategory(sourceCategory);
            });

            sourceCategory.querySelector('.tool-source-toggle')?.addEventListener('click', (e) => {
                e.stopPropagation();
                const allEnabled = enabledCount === totalCount;
                this.toggleSourceTools(source, !allEnabled);
            });

            sourceToolsList.querySelectorAll('.tool-toggle').forEach(toggle => {
                toggle.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const toolName = (toggle as HTMLElement).dataset.tool;
                    if (toolName) {
                        const tool = this.tools.find(t => t.name === toolName);
                        if (tool) {
                            this.toggleTool(toolName, !tool.enabled);
                        }
                    }
                });
            });

            this.toolsList.appendChild(sourceCategory);
        });

        // Add disable all handler
        this.toolsList.querySelector('.tool-toggle[data-tool="disable-all"]')?.addEventListener('click', () => {
            this.toggleAllTools(false);
        });

        this.updateToolsUI();
    }

    private toggleSourceCategory(sourceCategory: HTMLElement): void {
        const source = sourceCategory.dataset.source;
        if (!source) return;

        const sourceToolsList = sourceCategory.querySelector('.tool-source-tools') as HTMLElement;
        const expandIcon = sourceCategory.querySelector('.tool-source-expand svg') as SVGElement;
        
        const isExpanded = sourceCategory.classList.contains('expanded');
        
        if (isExpanded) {
            sourceCategory.classList.remove('expanded');
            sourceToolsList.style.display = 'none';
            expandIcon.style.transform = 'rotate(0deg)';
            this.toolCategoryStates[source] = false;
        } else {
            sourceCategory.classList.add('expanded');
            sourceToolsList.style.display = 'block';
            expandIcon.style.transform = 'rotate(90deg)';
            this.toolCategoryStates[source] = true;
        }
        
        this.saveToolCategoryStates();
    }

    private async toggleTool(toolName: string, enabled: boolean): Promise<void> {
        if (!this.currentSession?.sessionId) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/${this.currentSession.sessionId}/tools/${toolName}/toggle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': 'test_12345'
                },
                body: JSON.stringify({ enabled })
            });

            if (response.ok) {
                const tool = this.tools.find(t => t.name === toolName);
                if (tool) {
                    tool.enabled = enabled;
                    this.updateToolsUI();
                }
            } else {
                console.error(`Failed to toggle tool ${toolName}:`, response.status);
            }
        } catch (error) {
            console.error(`Error toggling tool ${toolName}:`, error);
        }
    }

    private async toggleAllTools(enabled: boolean): Promise<void> {
        if (!this.currentSession?.sessionId) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/${this.currentSession.sessionId}/tools/toggle-all`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-API-Key': 'test_12345'
                },
                body: JSON.stringify({ enabled })
            });

            if (response.ok) {
                this.tools.forEach(tool => {
                    tool.enabled = enabled;
                });
                this.updateToolsUI();
            } else {
                console.error('Failed to toggle all tools:', response.status);
            }
        } catch (error) {
            console.error('Error toggling all tools:', error);
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
        if (!this.currentSession?.sessionId) return;

        const sourceTools = this.tools.filter(tool => (tool.source || 'default') === source);
        
        try {
            const promises = sourceTools.map(tool => this.toggleTool(tool.name, enabled));
            await Promise.all(promises);
        } catch (error) {
            console.error(`Error toggling source tools for ${source}:`, error);
        }
    }

    private loadToolCategoryStates(): void {
        const saved = localStorage.getItem('toolCategoryStates');
        if (saved) {
            try {
                this.toolCategoryStates = JSON.parse(saved);
            } catch (error) {
                console.error('Failed to parse saved tool category states:', error);
                this.toolCategoryStates = {};
            }
        }
    }

    private saveToolCategoryStates(): void {
        localStorage.setItem('toolCategoryStates', JSON.stringify(this.toolCategoryStates));
    }

    getIsLoadingTools(): boolean {
        return this.isLoadingTools;
    }

    getTools(): Tool[] {
        return this.tools;
    }
}