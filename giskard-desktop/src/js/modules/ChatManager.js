/**
 * ChatManager - Handles chat interface and Ollama integration
 */
class ChatManager {
    constructor() {
        this.chatMessages = [];
        this.isTyping = false;
        this.currentConversation = null;
        
        // Set up API base URL (same logic as APIClient)
        this.isTauri = window.__TAURI__ !== undefined;
        this.baseURL = this.isTauri ? 'http://localhost:5001/api' : '/api';
        
        console.log('🤖 ChatManager: Tauri detected:', this.isTauri, 'Base URL:', this.baseURL);
        
        this._bindEvents();
        this._initializeChat();
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
            console.error('Failed to get response from Ollama:', error);
            this._addMessage('bot', "I'm having trouble connecting right now. Please check if Ollama is running with llama3.1:8b and try again.");
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
     * Send message to Ollama (with timeout and error handling)
     */
    async _sendToOllama(message) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
        
        try {
            const response = await fetch(`${this.baseURL}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    conversation_history: this.chatMessages.slice(-6) // Reduced context for faster responses
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data.response;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error('Request timed out. The AI might be busy - please try again.');
            }
            throw error;
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
        this._renderMessage(message);
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
        if (!this.chatMessagesContainer) return;

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
     * Debug function - inspect current chat state
     */
    debugChatState() {
        console.log('=== CHAT DEBUG STATE ===');
        console.log('💬 Messages in memory:', this.chatMessages.length, this.chatMessages);
        console.log('💾 LocalStorage:', localStorage.getItem('giscard_chat_history'));
        console.log('🎯 chatMessagesContainer:', !!this.chatMessagesContainer);
        console.log('💡 chatSuggestions:', !!this.chatSuggestions);
        console.log('⌨️ chatInput:', !!this.chatInput);
        console.log('========================');
    }
}

export default ChatManager;
