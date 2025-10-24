/**
 * GitHubLikeEditor - GitHub-style markdown editor for task descriptions
 * Features: View/Edit modes, keyboard shortcuts, autosave, markdown rendering
 */
class GitHubLikeEditor {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            autosaveDelay: 1500,
            placeholder: 'Add description...',
            ...options
        };
        
        this.isEditing = false;
        this.originalContent = '';
        this.markdownRenderer = new MarkdownRenderer();
        this.autosaveTimeout = null;
        this.saveStatus = 'saved'; // 'saved', 'saving', 'error'
        
        this.init();
    }

    init() {
        if (!this.container) {
            console.error('GitHubLikeEditor: Container not found');
            return;
        }

        this.createEditorHTML();
        this.bindEvents();
        this.updateSaveStatus('saved');
    }

    createEditorHTML() {
        this.container.innerHTML = `
            <div class="github-editor">
                <div class="editor-view-mode" id="editor-view-mode">
                    <div class="markdown-content" id="markdown-content">
                        <p class="empty-description">No description provided</p>
                    </div>
                    <div class="edit-hint">
                        <span class="edit-hint-text">Click to edit or press <kbd>E</kbd></span>
                    </div>
                </div>
                
                <div class="editor-edit-mode" id="editor-edit-mode" style="display: none;">
                    <div class="editor-toolbar">
                        <div class="toolbar-group">
                            <button type="button" class="toolbar-btn" data-action="bold" title="Bold (Cmd+B)">
                                <i class="fas fa-bold"></i>
                            </button>
                            <button type="button" class="toolbar-btn" data-action="italic" title="Italic (Cmd+I)">
                                <i class="fas fa-italic"></i>
                            </button>
                            <button type="button" class="toolbar-btn" data-action="link" title="Link (Cmd+K)">
                                <i class="fas fa-link"></i>
                            </button>
                        </div>
                        <div class="toolbar-group">
                            <button type="button" class="toolbar-btn" data-action="tasklist" title="Task list">
                                <i class="fas fa-tasks"></i>
                            </button>
                            <button type="button" class="toolbar-btn" data-action="code" title="Code">
                                <i class="fas fa-code"></i>
                            </button>
                        </div>
                    </div>
                    
                    <textarea 
                        class="editor-textarea" 
                        id="editor-textarea" 
                        placeholder="${this.options.placeholder}"
                        spellcheck="false"
                    ></textarea>
                    
                    <div class="editor-footer">
                        <div class="save-status" id="save-status">
                            <span class="status-text">All changes saved</span>
                        </div>
                        <div class="editor-actions">
                            <button type="button" class="btn-secondary" id="cancel-edit">Cancel</button>
                            <button type="button" class="btn-primary" id="save-edit">Save</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Get references to elements
        this.viewMode = document.getElementById('editor-view-mode');
        this.editMode = document.getElementById('editor-edit-mode');
        this.markdownContent = document.getElementById('markdown-content');
        this.textarea = document.getElementById('editor-textarea');
        this.saveStatus = document.getElementById('save-status');
    }

    bindEvents() {
        // View mode events
        this.viewMode.addEventListener('click', () => this.enterEditMode());
        this.viewMode.addEventListener('keydown', (e) => {
            if (e.key === 'e' || e.key === 'E') {
                e.preventDefault();
                this.enterEditMode();
            }
        });

        // Edit mode events
        this.textarea.addEventListener('keydown', (e) => this.handleKeydown(e));
        this.textarea.addEventListener('input', () => this.handleInput());
        this.textarea.addEventListener('blur', (e) => {
            // Only auto-save on blur if content has changed
            if (this.textarea.value !== this.originalContent) {
                this.save();
            }
        });

        // Toolbar events
        const toolbarBtns = this.container.querySelectorAll('.toolbar-btn');
        toolbarBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleToolbarAction(btn.dataset.action);
            });
        });

        // Action buttons
        document.getElementById('cancel-edit').addEventListener('click', () => this.cancelEdit());
        document.getElementById('save-edit').addEventListener('click', () => this.saveAndExit());

        // Global keyboard shortcuts
        document.addEventListener('keydown', (e) => this.handleGlobalKeydown(e));
    }

    handleKeydown(e) {
        // Cmd+Enter to save and exit
        if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
            e.preventDefault();
            this.saveAndExit();
            return;
        }

        // Escape to cancel
        if (e.key === 'Escape') {
            e.preventDefault();
            this.cancelEdit();
            return;
        }

        // Tab handling for lists
        if (e.key === 'Tab') {
            e.preventDefault();
            this.handleTab(e.shiftKey);
        }
    }

    handleGlobalKeydown(e) {
        // Only handle if we're not in edit mode and the target is not an input
        if (this.isEditing || e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        // E key to edit
        if (e.key === 'e' || e.key === 'E') {
            e.preventDefault();
            this.enterEditMode();
        }
    }

    handleInput() {
        // Clear existing autosave timeout
        if (this.autosaveTimeout) {
            clearTimeout(this.autosaveTimeout);
        }

        // Set new autosave timeout
        this.autosaveTimeout = setTimeout(() => {
            this.save();
        }, this.options.autosaveDelay);

        this.updateSaveStatus('saving');
    }

    handleToolbarAction(action) {
        const textarea = this.textarea;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const selectedText = textarea.value.substring(start, end);
        const beforeCursor = textarea.value.substring(0, start);
        const afterCursor = textarea.value.substring(end);

        let newText = '';
        let newCursorPos = start;

        switch (action) {
            case 'bold':
                newText = `**${selectedText || 'bold text'}**`;
                newCursorPos = start + (selectedText ? 2 : 11);
                break;
            case 'italic':
                newText = `*${selectedText || 'italic text'}*`;
                newCursorPos = start + (selectedText ? 1 : 12);
                break;
            case 'link':
                newText = `[${selectedText || 'link text'}](url)`;
                newCursorPos = start + (selectedText ? 0 : 10);
                break;
            case 'tasklist':
                newText = `- [ ] ${selectedText || 'task item'}`;
                newCursorPos = start + (selectedText ? 0 : 6);
                break;
            case 'code':
                if (selectedText.includes('\n')) {
                    newText = `\`\`\`\n${selectedText || 'code'}\n\`\`\``;
                    newCursorPos = start + 4;
                } else {
                    newText = `\`${selectedText || 'code'}\``;
                    newCursorPos = start + (selectedText ? 0 : 1);
                }
                break;
        }

        textarea.value = beforeCursor + newText + afterCursor;
        textarea.setSelectionRange(newCursorPos, newCursorPos);
        textarea.focus();
    }

    handleTab(isShift) {
        const textarea = this.textarea;
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const value = textarea.value;
        
        // Find the start of the current line
        const lineStart = value.lastIndexOf('\n', start - 1) + 1;
        const lineEnd = value.indexOf('\n', start);
        const currentLine = value.substring(lineStart, lineEnd === -1 ? value.length : lineEnd);
        
        // Check if it's a list item
        const listMatch = currentLine.match(/^(\s*)([-*+]|\d+\.)\s/);
        if (listMatch) {
            const indent = listMatch[1];
            const newIndent = isShift ? indent.slice(0, -2) : indent + '  ';
            const newLine = currentLine.replace(/^(\s*)/, newIndent);
            
            textarea.value = value.substring(0, lineStart) + newLine + value.substring(lineEnd === -1 ? value.length : lineEnd);
            textarea.setSelectionRange(start + (newIndent.length - indent.length), end + (newIndent.length - indent.length));
        } else {
            // Regular tab behavior
            const tab = isShift ? '' : '  ';
            textarea.value = value.substring(0, start) + tab + value.substring(end);
            textarea.setSelectionRange(start + tab.length, start + tab.length);
        }
    }

    enterEditMode() {
        if (this.isEditing) return;

        this.isEditing = true;
        this.originalContent = this.textarea.value;
        
        this.viewMode.style.display = 'none';
        this.editMode.style.display = 'block';
        
        this.textarea.focus();
        this.textarea.setSelectionRange(this.textarea.value.length, this.textarea.value.length);
    }

    exitEditMode() {
        if (!this.isEditing) return;

        this.isEditing = false;
        this.viewMode.style.display = 'block';
        this.editMode.style.display = 'none';
        
        // Update the rendered content
        this.updateRenderedContent();
    }

    cancelEdit() {
        this.textarea.value = this.originalContent;
        this.exitEditMode();
    }

    async saveAndExit() {
        await this.save();
        this.exitEditMode();
    }

    async save() {
        if (!this.isEditing) return;

        try {
            this.updateSaveStatus('saving');
            
            // Emit save event
            const saveEvent = new CustomEvent('github-editor-save', {
                detail: { content: this.textarea.value }
            });
            this.container.dispatchEvent(saveEvent);
            
            // Simulate save delay for better UX
            await new Promise(resolve => setTimeout(resolve, 300));
            
            this.updateSaveStatus('saved');
            this.originalContent = this.textarea.value;
            
        } catch (error) {
            console.error('Save failed:', error);
            this.updateSaveStatus('error');
        }
    }

    updateRenderedContent() {
        const content = this.textarea.value;
        
        if (!content.trim()) {
            this.markdownContent.innerHTML = '<p class="empty-description">No description provided</p>';
            return;
        }

        const rendered = this.markdownRenderer.render(content);
        this.markdownContent.innerHTML = rendered;
    }

    updateSaveStatus(status) {
        this.saveStatus = status;
        const statusElement = document.getElementById('save-status');
        
        if (!statusElement) return;

        const statusText = statusElement.querySelector('.status-text');
        if (!statusText) return;

        statusElement.className = `save-status ${status}`;
        
        switch (status) {
            case 'saved':
                statusText.textContent = 'All changes saved';
                break;
            case 'saving':
                statusText.textContent = 'Saving...';
                break;
            case 'error':
                statusText.textContent = 'Save failed';
                break;
        }
    }

    setContent(content) {
        this.textarea.value = content || '';
        this.updateRenderedContent();
    }

    getContent() {
        return this.textarea.value;
    }

    focus() {
        if (this.isEditing) {
            this.textarea.focus();
        } else {
            this.enterEditMode();
        }
    }

    destroy() {
        if (this.autosaveTimeout) {
            clearTimeout(this.autosaveTimeout);
        }
        
        // Remove event listeners
        document.removeEventListener('keydown', this.handleGlobalKeydown);
    }
}

// Make available globally
window.GitHubLikeEditor = GitHubLikeEditor;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GitHubLikeEditor;
}
