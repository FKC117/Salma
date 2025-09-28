/*
Smart Content Detection & Formatting System
Automatically detects and formats different content types in chat messages
*/

class SmartContentFormatter {
    constructor() {
        this.contentTypes = {
            TABLE: 'table',
            CHART: 'chart',
            CODE: 'code',
            JSON: 'json',
            LIST: 'list',
            QUOTE: 'quote',
            TEXT: 'text'
        };
        
        this.patterns = {
            // Table detection patterns
            table: [
                /^\s*\|.*\|.*$/m,  // Markdown table
                /^\s*[^\n]+\s*\|\s*[^\n]+\s*$/m,  // Pipe-separated
                /^\s*[^\n]+\s*\|\s*[^\n]+\s*\|\s*[^\n]+\s*$/m  // Multi-column
            ],
            
            // Chart detection patterns
            chart: [
                /chart|graph|plot|visualization/i,
                /bar chart|line chart|pie chart|scatter plot/i,
                /histogram|heatmap|correlation matrix/i
            ],
            
            // Code detection patterns
            code: [
                /```[\s\S]*?```/g,  // Code blocks
                /`[^`]+`/g,  // Inline code
                /def\s+\w+|function\s+\w+|class\s+\w+/i  // Function/class definitions
            ],
            
            // JSON detection patterns
            json: [
                /^\s*[\{\[].*[\}\]]\s*$/s,  // JSON object/array
                /"[\w\s]+"\s*:\s*["\d\w\s,{}[\]]+/  // JSON key-value pairs
            ],
            
            // List detection patterns
            list: [
                /^\s*[-*+]\s+.+$/m,  // Unordered lists
                /^\s*\d+\.\s+.+$/m,  // Ordered lists
                /^\s*•\s+.+$/m  // Bullet points
            ],
            
            // Quote detection patterns
            quote: [
                /^>\s+.+$/m,  // Markdown quotes
                /^"[\s\S]*"$/m,  // Quoted text
                /^'[\s\S]*'$/m  // Single-quoted text
            ]
        };
    }
    
    /**
     * Detect content type from text
     */
    detectContentType(text) {
        if (!text || typeof text !== 'string') {
            return this.contentTypes.TEXT;
        }
        
        // Check for tables
        if (this.patterns.table.some(pattern => pattern.test(text))) {
            return this.contentTypes.TABLE;
        }
        
        // Check for charts
        if (this.patterns.chart.some(pattern => pattern.test(text))) {
            return this.contentTypes.CHART;
        }
        
        // Check for code
        if (this.patterns.code.some(pattern => pattern.test(text))) {
            return this.contentTypes.CODE;
        }
        
        // Check for JSON
        if (this.patterns.json.some(pattern => pattern.test(text))) {
            return this.contentTypes.JSON;
        }
        
        // Check for lists
        if (this.patterns.list.some(pattern => pattern.test(text))) {
            return this.contentTypes.LIST;
        }
        
        // Check for quotes
        if (this.patterns.quote.some(pattern => pattern.test(text))) {
            return this.contentTypes.QUOTE;
        }
        
        return this.contentTypes.TEXT;
    }
    
    /**
     * Format content based on detected type
     */
    formatContent(text, contentType = null) {
        if (!contentType) {
            contentType = this.detectContentType(text);
        }
        
        switch (contentType) {
            case this.contentTypes.TABLE:
                return this.formatTable(text);
            case this.contentTypes.CHART:
                return this.formatChart(text);
            case this.contentTypes.CODE:
                return this.formatCode(text);
            case this.contentTypes.JSON:
                return this.formatJSON(text);
            case this.contentTypes.LIST:
                return this.formatList(text);
            case this.contentTypes.QUOTE:
                return this.formatQuote(text);
            default:
                return this.formatText(text);
        }
    }
    
    /**
     * Format table content
     */
    formatTable(text) {
        // Convert markdown table to HTML
        const lines = text.trim().split('\n');
        const tableRows = lines.filter(line => line.includes('|'));
        
        if (tableRows.length < 2) {
            return this.formatText(text);
        }
        
        // Extract table data
        const tableData = this.extractTableData(tableRows);
        
        let html = '<div class="table-container">';
        html += '<div class="table-header">';
        html += '<div class="table-title">';
        html += '<h6><i class="bi bi-table"></i> Data Table</h6>';
        html += `<span class="table-meta">${tableData.length} rows × ${tableData.headers.length} columns</span>`;
        html += '</div>';
        html += '<div class="table-actions">';
        html += '<div class="btn-group" role="group">';
        html += '<button class="btn btn-sm btn-outline-secondary" onclick="sortTable(this)" data-sort="none">';
        html += '<i class="bi bi-arrow-down-up"></i> Sort</button>';
        html += '<button class="btn btn-sm btn-outline-secondary" onclick="exportTable(this, \'csv\')">';
        html += '<i class="bi bi-file-earmark-spreadsheet"></i> CSV</button>';
        html += '<button class="btn btn-sm btn-outline-secondary" onclick="exportTable(this, \'json\')">';
        html += '<i class="bi bi-file-earmark-code"></i> JSON</button>';
        html += '<button class="btn btn-sm btn-outline-secondary" onclick="fullscreenTable(this)">';
        html += '<i class="bi bi-arrows-fullscreen"></i> Fullscreen</button>';
        html += '</div></div></div>';
        
        html += '<div class="table-content">';
        html += '<div class="table-responsive">';
        html += '<table class="table table-striped table-hover table-sm" id="dataTable">';
        html += '<thead class="table-dark">';
        html += '<tr>';
        tableData.headers.forEach(header => {
            html += `<th scope="col" class="sortable" onclick="sortByColumn(this)">${this.escapeHtml(header)} <i class="bi bi-arrow-down-up sort-icon"></i></th>`;
        });
        html += '</tr></thead>';
        html += '<tbody>';
        
        tableData.rows.forEach(row => {
            html += '<tr>';
            row.forEach(cell => {
                html += `<td>${this.escapeHtml(cell)}</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table>';
        html += '</div></div>';
        html += '<div class="table-footer">';
        html += '<div class="pagination-info">';
        html += `Showing 1 to ${Math.min(10, tableData.rows.length)} of ${tableData.rows.length} entries`;
        html += '</div></div></div>';
        
        return html;
    }
    
    /**
     * Extract table data from markdown table rows
     */
    extractTableData(tableRows) {
        const headers = tableRows[0].split('|').map(cell => cell.trim()).filter(cell => cell);
        const rows = [];
        
        for (let i = 1; i < tableRows.length; i++) {
            const cells = tableRows[i].split('|').map(cell => cell.trim()).filter(cell => cell);
            if (cells.length === headers.length) {
                rows.push(cells);
            }
        }
        
        return { headers, rows };
    }
    
    /**
     * Format chart content
     */
    formatChart(text) {
        // Create chart placeholder with metadata
        const chartType = this.detectChartType(text);
        const chartId = 'chart_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        
        return `
            <div class="chart-container">
                <div class="chart-header">
                    <h6><i class="bi bi-bar-chart"></i> ${chartType}</h6>
                    <div class="chart-actions">
                        <button class="btn btn-sm btn-outline-secondary" onclick="exportChart('${chartId}')">
                            <i class="bi bi-download"></i> Export
                        </button>
                        <button class="btn btn-sm btn-outline-secondary" onclick="fullscreenChart('${chartId}')">
                            <i class="bi bi-arrows-fullscreen"></i> Fullscreen
                        </button>
                    </div>
                </div>
                <div class="chart-content">
                    <canvas id="${chartId}" width="400" height="200"></canvas>
                </div>
                <div class="chart-description">
                    <p class="text-muted">${this.extractChartDescription(text)}</p>
                </div>
            </div>
        `;
    }
    
    /**
     * Format code content
     */
    formatCode(text) {
        // Handle code blocks
        let html = text.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            const language = lang || 'text';
            return `<pre class="code-block"><code class="language-${language}">${this.escapeHtml(code.trim())}</code></pre>`;
        });
        
        // Handle inline code
        html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
        
        return html;
    }
    
    /**
     * Format JSON content
     */
    formatJSON(text) {
        try {
            const jsonObj = JSON.parse(text);
            const formatted = JSON.stringify(jsonObj, null, 2);
            return `<pre class="json-block"><code>${this.escapeHtml(formatted)}</code></pre>`;
        } catch (e) {
            // If not valid JSON, try to format as code
            return this.formatCode(text);
        }
    }
    
    /**
     * Format list content
     */
    formatList(text) {
        const lines = text.split('\n');
        let html = '';
        let inList = false;
        let listType = 'ul';
        
        lines.forEach(line => {
            const trimmed = line.trim();
            
            if (trimmed.match(/^\d+\.\s+/)) {
                // Ordered list
                if (!inList || listType !== 'ol') {
                    if (inList) html += `</${listType}>`;
                    html += '<ol class="list-group list-group-flush">';
                    inList = true;
                    listType = 'ol';
                }
                const content = trimmed.replace(/^\d+\.\s+/, '');
                html += `<li class="list-group-item">${this.escapeHtml(content)}</li>`;
            } else if (trimmed.match(/^[-*+•]\s+/)) {
                // Unordered list
                if (!inList || listType !== 'ul') {
                    if (inList) html += `</${listType}>`;
                    html += '<ul class="list-group list-group-flush">';
                    inList = true;
                    listType = 'ul';
                }
                const content = trimmed.replace(/^[-*+•]\s+/, '');
                html += `<li class="list-group-item">${this.escapeHtml(content)}</li>`;
            } else if (trimmed === '') {
                // Empty line - continue list
                if (inList) {
                    html += '<li class="list-group-item">&nbsp;</li>';
                }
            } else {
                // Regular text - close list if open
                if (inList) {
                    html += `</${listType}>`;
                    inList = false;
                }
                html += `<p>${this.escapeHtml(trimmed)}</p>`;
            }
        });
        
        if (inList) {
            html += `</${listType}>`;
        }
        
        return html;
    }
    
    /**
     * Format quote content
     */
    formatQuote(text) {
        const lines = text.split('\n');
        let html = '<blockquote class="blockquote">';
        
        lines.forEach(line => {
            const trimmed = line.trim();
            if (trimmed.startsWith('>')) {
                const content = trimmed.substring(1).trim();
                html += `<p class="mb-0">${this.escapeHtml(content)}</p>`;
            } else if (trimmed.startsWith('"') && trimmed.endsWith('"')) {
                const content = trimmed.substring(1, trimmed.length - 1);
                html += `<p class="mb-0">${this.escapeHtml(content)}</p>`;
            } else {
                html += `<p class="mb-0">${this.escapeHtml(trimmed)}</p>`;
            }
        });
        
        html += '</blockquote>';
        return html;
    }
    
    /**
     * Format regular text content
     */
    formatText(text) {
        // Basic markdown formatting
        let html = text;
        
        // Bold text
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Italic text
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Links
        html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
        
        // Line breaks
        html = html.replace(/\n/g, '<br>');
        
        return html;
    }
    
    /**
     * Detect chart type from text
     */
    detectChartType(text) {
        const lowerText = text.toLowerCase();
        
        if (lowerText.includes('bar chart') || lowerText.includes('bar graph')) {
            return 'Bar Chart';
        } else if (lowerText.includes('line chart') || lowerText.includes('line graph')) {
            return 'Line Chart';
        } else if (lowerText.includes('pie chart')) {
            return 'Pie Chart';
        } else if (lowerText.includes('scatter plot')) {
            return 'Scatter Plot';
        } else if (lowerText.includes('histogram')) {
            return 'Histogram';
        } else if (lowerText.includes('heatmap')) {
            return 'Heatmap';
        } else if (lowerText.includes('correlation')) {
            return 'Correlation Matrix';
        } else {
            return 'Chart';
        }
    }
    
    /**
     * Extract chart description from text
     */
    extractChartDescription(text) {
        // Extract meaningful description from chart text
        const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 10);
        return sentences[0] ? sentences[0].trim() : 'Data visualization';
    }
    
    /**
     * Escape HTML characters
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Process message content with smart formatting
     */
    processMessage(messageElement) {
        const content = messageElement.querySelector('.message-body');
        if (!content) return;
        
        const text = content.textContent || content.innerText;
        const contentType = this.detectContentType(text);
        const formatted = this.formatContent(text, contentType);
        
        content.innerHTML = formatted;
        
        // Add content type indicator
        messageElement.classList.add(`content-${contentType}`);
        
        // Initialize charts if present
        if (contentType === this.contentTypes.CHART) {
            this.initializeCharts(messageElement);
        }
    }
    
    /**
     * Initialize charts in message
     */
    initializeCharts(messageElement) {
        const canvases = messageElement.querySelectorAll('canvas');
        canvases.forEach(canvas => {
            // Placeholder for chart initialization
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#58a6ff';
            ctx.font = '14px Inter';
            ctx.textAlign = 'center';
            ctx.fillText('Chart will be rendered here', canvas.width / 2, canvas.height / 2);
        });
    }
}

// Initialize formatter
const contentFormatter = new SmartContentFormatter();

// Auto-format messages when they're added to chat
document.addEventListener('DOMContentLoaded', () => {
    // Format existing messages
    const messages = document.querySelectorAll('.chat-message');
    messages.forEach(message => {
        contentFormatter.processMessage(message);
    });
    
    // Watch for new messages
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === Node.ELEMENT_NODE && node.classList.contains('chat-message')) {
                    contentFormatter.processMessage(node);
                }
            });
        });
    });
    
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        observer.observe(chatMessages, { childList: true });
    }
});

// Export for global use
window.SmartContentFormatter = SmartContentFormatter;
window.contentFormatter = contentFormatter;
