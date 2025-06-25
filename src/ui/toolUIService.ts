import { Tool } from './types';
import { ApiService } from './apiService';

export class ToolUIService {
    private toolsHeader: HTMLElement;
    private toolsList: HTMLElement;
    private toolCategoryStates: Record<string, boolean> = {};

    constructor(toolsHeader: HTMLElement, toolsList: HTMLElement) {
        this.toolsHeader = toolsHeader;
        this.toolsList = toolsList;
    }

    setupToolsToggle(): void {
        this.toolsHeader.addEventListener('click', () => {
            this.toggleToolsSection();
        });
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

    renderToolsLoading(): void {
        this.toolsList.innerHTML = `
            <div class="tools-loading">
                <div class="loading-spinner"></div>
                <span>Loading tools...</span>
            </div>
        `;
        
        const toolsLabelSpan = this.toolsHeader.querySelector('.tools-label span');
        if (toolsLabelSpan) {
            toolsLabelSpan.textContent = 'Tools Configuration [Loading...]';
        }
    }

    renderTools(tools: Tool[], hasActiveSession: boolean, apiService: ApiService, sessionId: string | null): void {
        console.log('renderTools() called');
        this.toolsList.innerHTML = '';
        
        if (!hasActiveSession) {
            this.toolsList.innerHTML = `
                <div class="tools-no-session">
                    <div class="tools-no-session-message">
                        No active session. Create a new chat to configure tools.
                    </div>
                </div>
            `;
            
            const toolsLabelSpan = this.toolsHeader.querySelector('.tools-label span');
            if (toolsLabelSpan) {
                toolsLabelSpan.textContent = 'Tools Configuration [No Session]';
            }
            return;
        }
        
        const enabledCount = tools.filter(tool => tool.enabled).length;
        const totalCount = tools.length;
        
        const toolsLabelSpan = this.toolsHeader.querySelector('.tools-label span');
        if (toolsLabelSpan) {
            toolsLabelSpan.textContent = `Tools Configuration [${enabledCount}/${totalCount}]`;
        }
        
        const toolsBySource = tools.reduce((groups, tool) => {
            const source = tool.source || 'default';
            if (!groups[source]) {
                groups[source] = [];
            }
            groups[source].push(tool);
            return groups;
        }, {} as Record<string, Tool[]>);
        
        const sortedSources = Object.keys(toolsBySource).sort((a, b) => {
            if (a === 'default') return -1;
            if (b === 'default') return 1;
            return a.localeCompare(b);
        });
        
        sortedSources.forEach(source => {
            console.log('Creating category for source:', source);
            const sourceTools = toolsBySource[source];
            const sortedTools = [...sourceTools].sort((a, b) => a.name.localeCompare(b.name));
            
            const isExpanded = this.toolCategoryStates[source] !== false;
            
            const sourceCategory = document.createElement('div');
            sourceCategory.className = `tool-source-category ${isExpanded ? 'expanded' : ''}`;
            sourceCategory.dataset.source = source;
            
            const sourceHeader = document.createElement('div');
            sourceHeader.className = 'tool-source-header';
            
            const sourceToggle = document.createElement('div');
            sourceToggle.className = 'tool-source-toggle';
            sourceToggle.innerHTML = '<div class="toggle-switch"></div>';
            
            const sourceEnabledCount = sourceTools.filter(tool => tool.enabled).length;
            const sourceTotalCount = sourceTools.length;
            const sourceAllEnabled = sourceEnabledCount === sourceTotalCount;
            
            if (sourceAllEnabled) {
                sourceToggle.classList.add('enabled');
            }
            
            sourceToggle.addEventListener('click', async (e) => {
                e.stopPropagation();
                const newEnabled = !sourceToggle.classList.contains('enabled');
                if (sessionId) {
                    await apiService.toggleSourceTools(sessionId, source, newEnabled);
                    
                    sourceTools.forEach(tool => {
                        tool.enabled = newEnabled;
                    });
                    
                    this.updateToolsUI(tools);
                }
            });
            
            const sourceLabel = document.createElement('div');
            sourceLabel.className = 'tool-source-label';
            sourceLabel.textContent = source === 'default' ? 'Built-in Tools' : source;
            
            const sourceCounter = document.createElement('div');
            sourceCounter.className = 'tool-source-counter';
            sourceCounter.textContent = `${sourceEnabledCount}/${sourceTotalCount}`;
            
            const sourceExpand = document.createElement('div');
            sourceExpand.className = 'tool-source-expand';
            sourceExpand.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 16 16" style="transform: rotate(${isExpanded ? '90' : '0'}deg);">
                    <path d="M6 12l4-4-4-4" stroke="currentColor" stroke-width="2" fill="none"/>
                </svg>
            `;
            
            sourceHeader.appendChild(sourceToggle);
            sourceHeader.appendChild(sourceLabel);
            sourceHeader.appendChild(sourceCounter);
            sourceHeader.appendChild(sourceExpand);
            
            sourceHeader.addEventListener('click', () => {
                this.toggleSourceCategory(source);
            });
            
            const sourceToolsList = document.createElement('div');
            sourceToolsList.className = 'tool-source-tools';
            sourceToolsList.style.display = isExpanded ? 'block' : 'none';
            
            sortedTools.forEach(tool => {
                const toolItem = document.createElement('div');
                toolItem.className = `tool-item ${tool.enabled ? 'enabled' : ''}`;
                
                const toolToggle = document.createElement('div');
                toolToggle.className = `tool-toggle ${tool.enabled ? 'enabled' : ''}`;
                toolToggle.innerHTML = '<div class="toggle-switch"></div>';
                
                toolToggle.addEventListener('click', async () => {
                    const newEnabled = !tool.enabled;
                    if (sessionId) {
                        await apiService.toggleTool(sessionId, tool.name, newEnabled);
                        tool.enabled = newEnabled;
                        this.updateToolsUI(tools);
                    }
                });
                
                const toolName = document.createElement('div');
                toolName.className = 'tool-name';
                toolName.textContent = tool.name;
                
                const toolDescription = document.createElement('div');
                toolDescription.className = 'tool-description';
                toolDescription.textContent = tool.description || 'No description available';
                
                toolItem.appendChild(toolToggle);
                toolItem.appendChild(toolName);
                toolItem.appendChild(toolDescription);
                
                sourceToolsList.appendChild(toolItem);
            });
            
            sourceCategory.appendChild(sourceHeader);
            sourceCategory.appendChild(sourceToolsList);
            this.toolsList.appendChild(sourceCategory);
        });
    }

    private toggleSourceCategory(source: string): void {
        const sourceCategories = this.toolsList.querySelectorAll('.tool-source-category');
        const sourceCategory = Array.from(sourceCategories).find(category => 
            (category as HTMLElement).dataset.source === source
        ) as HTMLElement;
        
        if (!sourceCategory) return;
        
        console.log('Toggling category for source:', source);
        console.log('Current classes:', sourceCategory.className);
        
        const isExpanded = sourceCategory.classList.contains('expanded');
        const newState = !isExpanded;
        
        console.log('Current state:', isExpanded, 'New state:', newState);
        
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

    updateToolsUI(tools: Tool[]): void {
        const enabledCount = tools.filter(tool => tool.enabled).length;
        const totalCount = tools.length;
        
        const toolsLabelSpan = this.toolsHeader.querySelector('.tools-label span');
        if (toolsLabelSpan) {
            toolsLabelSpan.textContent = `Tools Configuration [${enabledCount}/${totalCount}]`;
        }
        
        const sourceCategories = this.toolsList.querySelectorAll('.tool-source-category');
        sourceCategories.forEach(category => {
            const source = (category as HTMLElement).dataset.source;
            if (!source) return;
            
            const currentlyExpanded = (category as HTMLElement).classList.contains('expanded');
            const savedState = this.toolCategoryStates[source];
            
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
            
            const sourceTools = tools.filter(tool => (tool.source || 'default') === source);
            const sourceEnabledCount = sourceTools.filter(tool => tool.enabled).length;
            const sourceTotalCount = sourceTools.length;
            const sourceAllEnabled = sourceEnabledCount === sourceTotalCount;
            
            const counter = category.querySelector('.tool-source-counter');
            if (counter) {
                counter.textContent = `${sourceEnabledCount}/${sourceTotalCount}`;
            }
            
            const sourceToggle = category.querySelector('.tool-source-toggle');
            if (sourceToggle) {
                if (sourceAllEnabled) {
                    sourceToggle.classList.add('enabled');
                } else {
                    sourceToggle.classList.remove('enabled');
                }
            }
            
            const toolItems = category.querySelectorAll('.tool-item');
            toolItems.forEach(toolItem => {
                const toolNameEl = toolItem.querySelector('.tool-name');
                if (!toolNameEl) return;
                
                const toolName = toolNameEl.textContent;
                const tool = tools.find(t => t.name === toolName);
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
}