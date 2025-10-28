/**
 * MarkdownRenderer - Lightweight markdown parser and renderer
 * Supports GitHub-style markdown features for task descriptions
 */
class MarkdownRenderer {
    constructor() {
        this.supportedFeatures = [
            'headings', 'emphasis', 'links', 'lists', 'taskLists', 'code'
        ];
    }

    /**
     * Render markdown content to HTML
     * @param {string} markdown - Raw markdown content
     * @returns {string} Rendered HTML
     */
    render(markdown) {
        if (!markdown || typeof markdown !== 'string') {
            return '<p class="empty-description">No description provided</p>';
        }

        let html = markdown
            // Escape HTML first
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            
            // Code blocks (fenced)
            .replace(/```([\s\S]*?)```/g, (match, code) => {
                const escapedCode = code.trim()
                    .replace(/&amp;/g, '&')
                    .replace(/&lt;/g, '<')
                    .replace(/&gt;/g, '>');
                return `<pre><code class="code-block">${escapedCode}</code></pre>`;
            })
            
            // Inline code
            .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
            
            // Headings
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            
            // Task lists (- [ ] and - [x]) - handle indented ones too
            .replace(/^- \[ \] (.*$)/gim, (match, text) => {
                return `<div class="markdown-task-item"><input type="checkbox" disabled> <span>${text}</span></div>`;
            })
            .replace(/^- \[x\] (.*$)/gim, (match, text) => {
                return `<div class="markdown-task-item completed"><input type="checkbox" checked disabled> <span>${text}</span></div>`;
            })
            
            // Unordered lists
            .replace(/^- (.*$)/gim, '<li>$1</li>')
            .replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>')
            
            // Ordered lists
            .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
            
            // Links [text](url)
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>')
            
            // Bold and italic (order matters - bold first)
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\*([^*]+)\*/g, '<em>$1</em>')
            
            // Line breaks
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');

        // Wrap in paragraph if not already wrapped
        if (!html.startsWith('<')) {
            html = `<p>${html}</p>`;
        }

        // Clean up empty paragraphs
        html = html.replace(/<p><\/p>/g, '');

        // Remove <br> tags around block-level elements (headings, divs, lists)
        html = html
            .replace(/<br>\s*(<h[123]>)/g, '$1')  // Remove <br> before headers
            .replace(/(<\/h[123]>)\s*<br>/g, '$1')  // Remove <br> after headers
            .replace(/<br>\s*(<div class="markdown-task-item)/g, '$1')  // Remove <br> before task items
            .replace(/(<\/div>)\s*<br>/g, '$1')  // Remove <br> after divs
            .replace(/<br>\s*(<ul>)/g, '$1')  // Remove <br> before lists
            .replace(/(<\/ul>)\s*<br>/g, '$1');  // Remove <br> after lists

        return html;
    }

    /**
     * Extract plain text from markdown (for previews, etc.)
     * @param {string} markdown - Raw markdown content
     * @returns {string} Plain text
     */
    extractText(markdown) {
        if (!markdown) return '';
        
        return markdown
            // Remove code blocks
            .replace(/```[\s\S]*?```/g, '')
            // Remove inline code
            .replace(/`[^`]+`/g, '')
            // Remove markdown syntax
            .replace(/#{1,6}\s+/g, '')
            .replace(/\*\*([^*]+)\*\*/g, '$1')
            .replace(/\*([^*]+)\*/g, '$1')
            .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
            .replace(/^- \[[ x]\] /gm, '')
            .replace(/^- /gm, '')
            .replace(/^\d+\. /gm, '')
            .trim();
    }

    /**
     * Check if content has markdown features
     * @param {string} markdown - Raw markdown content
     * @returns {boolean} True if content has markdown features
     */
    hasMarkdownFeatures(markdown) {
        if (!markdown) return false;
        
        const markdownPatterns = [
            /#{1,6}\s+/,           // Headings
            /\*\*.*\*\*/,          // Bold
            /\*[^*]+\*/,          // Italic
            /\[.*\]\(.*\)/,        // Links
            /^- \[[ x]\]/,         // Task lists
            /^- /,                 // Lists
            /^\d+\. /,             // Numbered lists
            /```/,                 // Code blocks
            /`[^`]+`/              // Inline code
        ];
        
        return markdownPatterns.some(pattern => pattern.test(markdown));
    }
}

// Make available globally
window.MarkdownRenderer = MarkdownRenderer;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MarkdownRenderer;
}
