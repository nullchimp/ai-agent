export class Utils {
    static escapeHtml(unsafe: string): string {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    static generateId(): string {
        return Date.now().toString(36) + Math.random().toString(36).substr(2);
    }

    static applyColorSchemeToData(data: Record<string, any>): string {
        return Utils.colorizeJsonData(data, 0);
    }

    static colorizeJsonData(obj: any, depth: number = 0, keyPath: string = '', rootColorMetadata: Record<string, string> = {}): string {
        const indent = '  '.repeat(depth);
        const nextIndent = '  '.repeat(depth + 1);
        
        if (depth === 0) {
            rootColorMetadata = Utils.findRootColorMetadata(obj);
        }
        
        if (obj === null) {
            return '<span class="json-null">null</span>';
        }
        
        if (typeof obj === 'boolean') {
            return `<span class="json-boolean">${obj}</span>`;
        }
        
        if (typeof obj === 'number') {
            return `<span class="json-number">${obj}</span>`;
        }
        
        if (typeof obj === 'string') {
            // Apply color scheme if this is a special string value
            const colorClass = rootColorMetadata[keyPath] || '';
            const className = colorClass ? `json-string ${colorClass}` : 'json-string';
            return `<span class="${className}">"${Utils.escapeHtml(obj)}"</span>`;
        }
        
        if (Array.isArray(obj)) {
            if (obj.length === 0) {
                return '<span class="json-bracket">[]</span>';
            }
            
            let result = '<span class="json-bracket">[</span>\n';
            obj.forEach((item, index) => {
                const itemKeyPath = `${keyPath}[${index}]`;
                result += nextIndent + Utils.colorizeJsonData(item, depth + 1, itemKeyPath, rootColorMetadata);
                if (index < obj.length - 1) {
                    result += '<span class="json-comma">,</span>';
                }
                result += '\n';
            });
            result += indent + '<span class="json-bracket">]</span>';
            return result;
        }
        
        if (typeof obj === 'object') {
            const keys = Object.keys(obj);
            if (keys.length === 0) {
                return '<span class="json-brace">{}</span>';
            }
            
            let result = '<span class="json-brace">{</span>\n';
            keys.forEach((key, index) => {
                const value = obj[key];
                const valueKeyPath = keyPath ? `${keyPath}.${key}` : key;
                
                result += nextIndent;
                result += `<span class="json-key">"${Utils.escapeHtml(key)}"</span>`;
                result += '<span class="json-colon">:</span> ';
                result += Utils.colorizeJsonData(value, depth + 1, valueKeyPath, rootColorMetadata);
                
                if (index < keys.length - 1) {
                    result += '<span class="json-comma">,</span>';
                }
                result += '\n';
            });
            result += indent + '<span class="json-brace">}</span>';
            return result;
        }
        
        return `<span class="json-unknown">${Utils.escapeHtml(String(obj))}</span>`;
    }

    static findRootColorMetadata(obj: any): Record<string, string> {
        const colorMetadata: Record<string, string> = {};
        
        function traverse(current: any, path: string = '') {
            if (typeof current === 'object' && current !== null) {
                if (Array.isArray(current)) {
                    current.forEach((item, index) => {
                        traverse(item, `${path}[${index}]`);
                    });
                } else {
                    Object.keys(current).forEach(key => {
                        const newPath = path ? `${path}.${key}` : key;
                        const value = current[key];
                        
                        // Check for color scheme indicators
                        if (typeof value === 'string') {
                            if (key.toLowerCase().includes('color') || 
                                key.toLowerCase().includes('status') ||
                                key.toLowerCase().includes('level') ||
                                key.toLowerCase().includes('type')) {
                                
                                // Map certain values to color classes
                                if (value.toLowerCase().includes('error') || value.toLowerCase().includes('fail')) {
                                    colorMetadata[newPath] = 'color-error';
                                } else if (value.toLowerCase().includes('warn') || value.toLowerCase().includes('warning')) {
                                    colorMetadata[newPath] = 'color-warning';
                                } else if (value.toLowerCase().includes('success') || value.toLowerCase().includes('ok')) {
                                    colorMetadata[newPath] = 'color-success';
                                } else if (value.toLowerCase().includes('info') || value.toLowerCase().includes('debug')) {
                                    colorMetadata[newPath] = 'color-info';
                                }
                            }
                        }
                        
                        traverse(value, newPath);
                    });
                }
            }
        }
        
        traverse(obj);
        return colorMetadata;
    }

    static truncateString(str: string, maxLength: number): string {
        if (str.length <= maxLength) {
            return str;
        }
        return str.substring(0, maxLength) + '...';
    }

    static formatTimestamp(date: Date): string {
        return date.toLocaleString();
    }

    static isValidSessionId(sessionId: string | null | undefined): boolean {
        return sessionId !== null && sessionId !== undefined && sessionId.trim().length > 0;
    }
}