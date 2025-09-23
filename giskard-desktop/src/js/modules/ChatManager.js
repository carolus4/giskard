/**
 * ChatManager - Handles chat interface and Ollama integration
 */
class ChatManager {
    constructor() {
        this.chatMessages = [];
        this.isTyping = false;
        this.currentConversation = null;
        this.modelName = 'gemma3:4b'; // Default fallback
        
        // Set up API base URL (same logic as APIClient)
        this.isTauri = window.__TAURI__ !== undefined;
        this.baseURL = this.isTauri ? 'http://localhost:5001/api' : '/api';
        
        console.log('🤖 ChatManager: Tauri detected:', this.isTauri, 'Base URL:', this.baseURL);
        
        this._bindEvents();
        this._initializeChat();
        this._subscribeToModelUpdates();
    }

    /**
     * Subscribe to model updates from ModelManager
     */
    _subscribeToModelUpdates() {
        // Get current model name if already loaded
        this.modelName = window.ModelManager?.getModelName() || 'gemma3:4b';
        
        // Subscribe to updates
        if (window.ModelManager) {
            window.ModelManager.subscribe((modelName) => {
                this.modelName = modelName;
            });
        }
    }

    /**
     * Initialize chat interface
     */
    _initializeChat() {
        this.chatMessagesContainer = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-message-btn');
        this.typingIndicator = document.getElementById('typing-indicator');
        this.chatSuggestions = document.getElementById('chat-suggestions');
        
        // Load chat history if exists
        this._loadChatHistory();
        
        // Update platform-specific keyboard shortcuts
        this._updateKeyboardShortcuts();
    }

    /**
     * Bind event listeners
     */
    _bindEvents() {
        // Listen for view changes to activate chat when Giskard is selected
        document.addEventListener('view:changed', (e) => {
            if (e.detail.view === 'giskard') {
                this._handleGiskardViewActivated();
            }
        });

        // Wait for DOM to initialize chat elements
        setTimeout(() => this._bindChatEvents(), 100);
    }

    /**
     * Bind chat-specific events after DOM is ready
     */
    _bindChatEvents() {
        // Send message
        if (this.sendButton) {
            this.sendButton.addEventListener('click', () => this._handleSendMessage());
        }

        // Chat input events (throttled for performance)
        if (this.chatInput) {
            let inputTimeout;
            this.chatInput.addEventListener('input', () => {
                clearTimeout(inputTimeout);
                inputTimeout = setTimeout(() => this._handleInputChange(), 50);
            });

            this.chatInput.addEventListener('keydown', (e) => this._handleInputKeydown(e));
        }

        // Suggestion buttons - delegate to container for better performance
        if (this.chatSuggestions) {
            this.chatSuggestions.addEventListener('click', (e) => {
                if (e.target.classList.contains('suggestion-btn')) {
                    this._handleSuggestionClick(e.target.textContent);
                }
            });
        }

        // Chat actions
        const newChatBtn = document.getElementById('new-chat-action-btn');
        
        if (newChatBtn) {
            newChatBtn.addEventListener('click', () => {
                this._handleNewChat();
            });
        }
    }

    /**
     * Handle when Giskard view is activated via sidebar navigation
     */
    _handleGiskardViewActivated() {
        // Focus input and scroll to bottom when chat view is activated
        requestAnimationFrame(() => {
            this.chatInput?.focus();
            this._scrollToBottom();
        });
    }

    /**
     * Handle sending a message
     */
    async _handleSendMessage() {
        const message = this.chatInput?.value?.trim();
        if (!message || this.isTyping) return;

        // Add user message to UI
        this._addMessage('user', message);
        this.chatInput.value = '';
        this._updateSendButton();
        this._hideSuggestions();

        // Show typing indicator
        this._showTyping();

        try {
            // Send to Ollama
            const response = await this._sendToOllama(message);
            this._addMessage('bot', response);
        } catch (error) {
            console.error('Failed to get response from agent:', error);
            
            // Provide more specific error messages
            let errorMessage = 'I encountered an error. Please try again.';
            
            if (error.message.includes('timeout') || error.message.includes('timed out')) {
                errorMessage = 'The request timed out. The AI might be busy - please try again.';
            } else if (error.message.includes('HTTP error')) {
                errorMessage = 'Server error occurred. Please try again.';
            } else if (error.message.includes('Failed to fetch')) {
                errorMessage = 'Connection error. Please check if the server is running.';
            } else if (error.message.includes('Agent step failed')) {
                errorMessage = 'I had trouble processing your request. Please try again.';
            }
            
            this._addMessage('bot', errorMessage);
        } finally {
            this._hideTyping();
        }
    }

    /**
     * Handle input changes
     */
    _handleInputChange() {
        this._updateSendButton();
        this._autoResizeInput();
    }

    /**
     * Handle input keydown events
     */
    _handleInputKeydown(e) {
        const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
        const cmdOrCtrl = isMac ? e.metaKey : e.ctrlKey;

        if (e.key === 'Enter' && cmdOrCtrl) {
            e.preventDefault();
            this._handleSendMessage();
        }
    }

    /**
     * Handle suggestion click
     */
    _handleSuggestionClick(suggestion) {
        if (this.chatInput) {
            this.chatInput.value = suggestion;
            this.chatInput.focus();
            this._updateSendButton();
        }
    }

    /**
     * Handle new chat
     */
    _handleNewChat() {
        console.log('✨ Starting new chat conversation...');
        
        // Show brief clearing animation
        if (this.chatMessagesContainer) {
            this.chatMessagesContainer.style.opacity = '0.5';
        }
        
        // Clear message history (no confirmation needed)
        this.chatMessages = [];
        
        // Brief delay for visual feedback, then update UI
        setTimeout(() => {
            // Re-render UI (will show welcome message)
            this._renderMessages();
            
            // Show suggestion buttons
            this._showSuggestions();
            
            // Restore opacity
            if (this.chatMessagesContainer) {
                this.chatMessagesContainer.style.opacity = '1';
            }
            
            // Save to localStorage immediately
            try {
                localStorage.setItem('giscard_chat_history', JSON.stringify(this.chatMessages));
            } catch (error) {
                console.error('❌ Failed to save to localStorage:', error);
            }
            
            // Reset input and scroll
            if (this.chatInput) {
                this.chatInput.value = '';
                this._updateSendButton();
            }
            this._scrollToBottom();
            
            // Show success notification
            this._showNotification('New chat started! ✨', 'success');
            
            console.log('✅ New chat conversation started successfully');
        }, 150);
    }

    /**
     * Send message to Ollama via agent orchestration (with timeout and error handling)
     */
    async _sendToOllama(message) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
        
        try {
            // Get current UI context (tasks, etc.)
            const uiContext = await this._getUIContext();
            
            // Convert chat messages to agent format
            const agentMessages = this.chatMessages.map(msg => ({
                type: msg.type === 'user' ? 'user' : 'assistant',
                content: msg.content
            }));
            
            // Add current user message
            agentMessages.push({
                type: 'user',
                content: message
            });
            
            const response = await fetch(`${this.baseURL}/agent/step`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    messages: agentMessages.slice(-6), // Keep last 6 messages for context
                    ui_context: uiContext
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            
            // Debug logging
            console.log('🤖 Agent response:', data);
            
            if (data.success) {
                // Handle side effects (task creation, etc.)
                if (data.side_effects && data.side_effects.length > 0) {
                    console.log('🔧 Side effects:', data.side_effects);
                    this._handleSideEffects(data.side_effects);
                }
                
                // Store undo token for potential undo operations
                if (data.undo_token) {
                    console.log('🔄 Undo token:', data.undo_token);
                    this._storeUndoToken(data.undo_token);
                }
                
                return data.assistant_text;
            } else {
                console.error('❌ Agent step failed:', data.error);
                throw new Error(data.error || 'Agent step failed');
            }
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Request timed out. The AI might be busy - please try again.');
            }
            throw error;
        }
    }
    
    /**
     * Get current UI context for the agent
     */
    async _getUIContext() {
        try {
            // Get current tasks from the API
            const response = await fetch(`${this.baseURL}/tasks`);
            if (response.ok) {
                const data = await response.json();
                return {
                    current_tasks: data.tasks || {},
                    task_counts: data.counts || {},
                    today_date: data.today_date || ''
                };
            }
        } catch (error) {
            console.warn('Failed to get UI context:', error);
        }
        
        return {
            current_tasks: {},
            task_counts: {},
            today_date: ''
        };
    }
    
    /**
     * Handle side effects from agent execution
     */
    _handleSideEffects(sideEffects) {
        sideEffects.forEach(effect => {
            if (effect.success && effect.action === 'create_task') {
                // Show success notification
                this._showNotification(`✅ ${effect.message}`, 'success');
                
                // Trigger task list refresh if TaskManager is available
                if (window.TaskManager && window.TaskManager.loadTasks) {
                    console.log('🔄 Refreshing task list after task creation');
                    window.TaskManager.loadTasks(true); // Refresh with animation
                } else {
                    console.warn('⚠️ TaskManager not available for task list refresh');
                }
            } else if (!effect.success) {
                // Show error notification
                this._showNotification(`❌ ${effect.error}`, 'error');
            }
        });
    }
    
    /**
     * Store undo token for potential undo operations
     */
    _storeUndoToken(undoToken) {
        // Store the most recent undo token
        this.lastUndoToken = undoToken;
        
        // You could also store multiple tokens if needed
        if (!this.undoTokens) {
            this.undoTokens = [];
        }
        this.undoTokens.push(undoToken);
        
        // Keep only the last 5 undo tokens
        if (this.undoTokens.length > 5) {
            this.undoTokens.shift();
        }
    }

    /**
     * Add message to chat
     */
    _addMessage(type, content) {
        const message = {
            type: type,
            content: content,
            timestamp: new Date().toISOString()
        };
        
        this.chatMessages.push(message);
        const messageElement = this._renderMessage(message);
        
        // Add undo button if this is an assistant message and we have an undo token
        if (type === 'bot' && this.lastUndoToken) {
            this._addUndoButton(messageElement);
        }
        
        this._scrollToBottom();
        this._saveChatHistory();
    }

    /**
     * Render all messages
     */
    _renderMessages() {
        if (!this.chatMessagesContainer) {
            console.error('❌ chatMessagesContainer not found!');
            return;
        }

        // Clear all messages
        this.chatMessagesContainer.innerHTML = '';
        
        // Show welcome message if no chat messages
        if (this.chatMessages.length === 0) {
            this._renderWelcomeMessage();
        }

        // Render all chat messages
        this.chatMessages.forEach(message => {
            this._renderMessage(message, false);
        });
    }

    /**
     * Render the welcome message
     */
    _renderWelcomeMessage() {
        if (!this.chatMessagesContainer) {
            console.error('❌ chatMessagesContainer not found in _renderWelcomeMessage!');
            return;
        }

        const welcomeDiv = document.createElement('div');
        welcomeDiv.className = 'welcome-message';
        welcomeDiv.innerHTML = `
            <div class="message bot-message">
                <div class="message-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">
                    <p>Hey there! I'm your productivity coach. I can help you organize tasks, set priorities, and stay motivated. What would you like to work on today?</p>
                </div>
            </div>
        `;
        
        this.chatMessagesContainer.appendChild(welcomeDiv);
    }

    /**
     * Render single message
     */
    _renderMessage(message, animate = true) {
        if (!this.chatMessagesContainer) return null;

        const messageEl = document.createElement('div');
        messageEl.className = `message ${message.type}-message ${animate ? 'fade-in' : ''}`;

        const time = new Date(message.timestamp).toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });

        messageEl.innerHTML = `
            <div class="message-avatar">
                <i class="fas ${message.type === 'user' ? 'fa-user' : 'fa-robot'}"></i>
            </div>
            <div class="message-content">
                <p>${this._formatMessage(message.content)}</p>
                <div class="message-time">${time}</div>
            </div>
        `;

        this.chatMessagesContainer.appendChild(messageEl);
        return messageEl;
    }

    /**
     * Format message content (basic markdown-like formatting)
     */
    _formatMessage(content) {
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }

    /**
     * Show typing indicator
     */
    _showTyping() {
        this.isTyping = true;
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'flex';
        }
        this._scrollToBottom();
    }

    /**
     * Hide typing indicator
     */
    _hideTyping() {
        this.isTyping = false;
        if (this.typingIndicator) {
            this.typingIndicator.style.display = 'none';
        }
    }

    /**
     * Update send button state
     */
    _updateSendButton() {
        if (!this.sendButton || !this.chatInput) return;
        
        const hasText = this.chatInput.value.trim().length > 0;
        this.sendButton.disabled = !hasText || this.isTyping;
    }

    /**
     * Auto-resize chat input (optimized)
     */
    _autoResizeInput() {
        if (!this.chatInput) return;
        
        requestAnimationFrame(() => {
            this.chatInput.style.height = 'auto';
            const newHeight = Math.min(this.chatInput.scrollHeight, 120);
            this.chatInput.style.height = newHeight + 'px';
        });
    }

    /**
     * Scroll to bottom of messages (optimized)
     */
    _scrollToBottom() {
        if (!this.chatMessagesContainer) return;
        
        requestAnimationFrame(() => {
            this.chatMessagesContainer.scrollTop = this.chatMessagesContainer.scrollHeight;
        });
    }

    /**
     * Show/hide suggestions
     */
    _showSuggestions() {
        if (this.chatSuggestions && this.chatMessages.length === 0) {
            this.chatSuggestions.style.display = 'flex';
        }
    }

    _hideSuggestions() {
        if (this.chatSuggestions) {
            this.chatSuggestions.style.display = 'none';
        }
    }

    /**
     * Show notification to user
     */
    _showNotification(message, type = 'info') {
        // Check if Notification module is available (from existing codebase)
        if (window.Notification && window.Notification.show) {
            window.Notification.show(message, type);
        } else {
            // Fallback: simple console log + visual indicator
            console.log(`📢 ${message}`);
            
            // Create simple toast notification
            const toast = document.createElement('div');
            toast.className = `chat-toast chat-toast-${type}`;
            toast.textContent = message;
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 16px;
                border-radius: 6px;
                color: white;
                font-size: 14px;
                z-index: 10000;
                opacity: 0;
                transform: translateY(-10px);
                transition: all 0.3s ease;
                ${type === 'success' ? 'background-color: #4CAF50;' : 'background-color: #2196F3;'}
                ${type === 'error' ? 'background-color: #f44336;' : ''}
            `;
            
            document.body.appendChild(toast);
            
            // Animate in
            requestAnimationFrame(() => {
                toast.style.opacity = '1';
                toast.style.transform = 'translateY(0)';
            });
            
            // Remove after 2 seconds
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(-10px)';
                setTimeout(() => {
                    if (toast.parentNode) {
                        toast.parentNode.removeChild(toast);
                    }
                }, 300);
            }, 2000);
        }
    }

    /**
     * Update keyboard shortcuts for platform
     */
    _updateKeyboardShortcuts() {
        const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
        const hint = document.querySelector('.input-hint');
        if (hint) {
            hint.textContent = `Press ${isMac ? '⌘' : 'Ctrl'}+Enter to send`;
        }
    }

    /**
     * Load chat history from localStorage
     */
    _loadChatHistory() {
        try {
            const saved = localStorage.getItem('giscard_chat_history');
            if (saved) {
                this.chatMessages = JSON.parse(saved);
                this._renderMessages();
                if (this.chatMessages.length > 0) {
                    this._hideSuggestions();
                }
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }

    /**
     * Save chat history to localStorage (debounced)
     */
    _saveChatHistory() {
        try {
            // Debounce saves to prevent excessive localStorage writes
            clearTimeout(this._saveTimeout);
            this._saveTimeout = setTimeout(() => {
                localStorage.setItem('giscard_chat_history', JSON.stringify(this.chatMessages));
            }, 500);
        } catch (error) {
            console.error('Failed to save chat history:', error);
        }
    }

    /**
     * Get chat manager instance (for debugging)
     */
    getChatHistory() {
        return this.chatMessages;
    }

    /**
     * Undo the last agent action
     */
    async _undoLastAction() {
        if (!this.lastUndoToken) {
            this._showNotification('No action to undo', 'info');
            return;
        }
        
        try {
            const response = await fetch(`${this.baseURL}/agent/undo`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    undo_token: this.lastUndoToken
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this._showNotification(data.data.message, 'success');
                    
                    // Trigger task list refresh
                    if (window.TaskManager && window.TaskManager.loadTasks) {
                        console.log('🔄 Refreshing task list after undo');
                        window.TaskManager.loadTasks(true); // Refresh with animation
                    } else {
                        console.warn('⚠️ TaskManager not available for task list refresh');
                    }
                    
                    // Clear the undo token
                    this.lastUndoToken = null;
                } else {
                    this._showNotification(data.error || 'Undo failed', 'error');
                }
            } else {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        } catch (error) {
            console.error('Undo failed:', error);
            this._showNotification('Failed to undo action', 'error');
        }
    }
    
    /**
     * Add undo button to the last assistant message
     */
    _addUndoButton(messageElement) {
        if (!this.lastUndoToken || !messageElement) return;
        
        const undoButton = document.createElement('button');
        undoButton.className = 'undo-btn';
        undoButton.innerHTML = '↶ Undo';
        undoButton.style.cssText = `
            background: #f44336;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            margin-top: 8px;
            opacity: 0.8;
            transition: opacity 0.2s;
        `;
        
        undoButton.addEventListener('mouseenter', () => {
            undoButton.style.opacity = '1';
        });
        
        undoButton.addEventListener('mouseleave', () => {
            undoButton.style.opacity = '0.8';
        });
        
        undoButton.addEventListener('click', () => {
            this._undoLastAction();
            undoButton.remove(); // Remove button after undo
        });
        
        const messageContent = messageElement.querySelector('.message-content');
        if (messageContent) {
            messageContent.appendChild(undoButton);
        }
    }

    /**
     * Debug function - inspect current chat state
     */
    debugChatState() {
        console.log('=== CHAT DEBUG STATE ===');
        console.log('💬 Messages in memory:', this.chatMessages.length, this.chatMessages);
        console.log('💾 LocalStorage:', localStorage.getItem('giscard_chat_history'));
        console.log('🎯 chatMessagesContainer:', !!this.chatMessagesContainer);
        console.log('💡 chatSuggestions:', !!this.chatSuggestions);
        console.log('⌨️ chatInput:', !!this.chatInput);
        console.log('🔄 Last undo token:', this.lastUndoToken);
        console.log('========================');
    }
}

export default ChatManager;
