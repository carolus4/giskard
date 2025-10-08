/**
 * ChatManager - Handles chat interface and Ollama integration
 */
class ChatManager {
    constructor() {
        this.chatMessages = [];
        this.isTyping = false;
        this.currentConversation = null;
        this.currentSessionId = null;
        this.conversationHistory = [];
        this.modelName = 'gemma3:4b'; // Default fallback
        this.currentStreamingMessage = null;

        // Set up API base URL (same logic as APIClient)
        this.isTauri = window.__TAURI__ !== undefined;
        this.baseURL = this.isTauri ? 'http://localhost:5001/api' : '/api';

        console.log('🤖 ChatManager: Tauri detected:', this.isTauri, 'Base URL:', this.baseURL);

        this._bindEvents();
        this._initializeChat();
        this._subscribeToModelUpdates();

        // Initialize conversation threads and load most recent (if any)
        setTimeout(async () => {
            await this._loadConversationSessions();
            await this._loadMostRecentSession();
        }, 100);
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
        this.typingIndicator = null; // Will be created dynamically
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

        // Add user message to UI immediately
        this._addMessage('user', message);
        this.chatInput.value = '';
        this._updateSendButton();
        this._hideSuggestions();

        // Show typing indicator with informative message
        this._showTyping();
        this._updateTypingMessage('Thinking');
        
        // Ensure the typing indicator is visible for a minimum time
        const typingStartTime = Date.now();
        const minTypingDuration = 800; // Minimum 800ms to ensure visibility

        try {
            // Send to Ollama via the orchestrator
            await this._sendToOllama(message);

            // If this was the first message in a new conversation, ensure we have a thread ID
            if (!this.currentThreadId) {
                this.currentThreadId = `chat-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
                await this._loadConversationSessions(); // Refresh the threads list
            }
        } catch (error) {
            console.error('Failed to get response from agent:', error);

            // Provide more specific error messages
            let errorMessage = 'I encountered an error. Please try again.';

            if (error.message.includes('timeout') || error.message.includes('timed out')) {
                errorMessage = 'The AI is taking longer than expected to process your request. This can happen with complex tasks. Please try again with a simpler request or wait a moment.';
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
     * Handle new chat - clears current conversation and starts fresh
     */
    _handleNewChat() {
        console.log('✨ Starting new chat conversation...');

        // Show brief clearing animation
        if (this.chatMessagesContainer) {
            this.chatMessagesContainer.style.opacity = '0.5';
        }

        // Brief delay for visual feedback, then update UI
        setTimeout(() => {
            // Clear current conversation state
            this.chatMessages = [];
            this.currentSessionId = null;
            
            // Ensure typing indicator is hidden when starting new chat
            this._hideTyping();

            // Re-render UI (will show welcome message)
            this._renderMessages();

            // Show suggestion buttons for new conversation
            this._showSuggestions();

            // Restore opacity
            if (this.chatMessagesContainer) {
                this.chatMessagesContainer.style.opacity = '1';
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
     * Updated to use orchestrator endpoint
     */
    async _sendToOllama(message) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000); // 120 second timeout for complex agent workflows

        try {
            // Use current thread ID or create new one if none exists
            let sessionId = this.currentSessionId;
            if (!sessionId) {
                // Create a new session for this conversation
                sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            }

            // Get conversation context for better responses
            const conversationContext = this._getConversationContext();

            const response = await fetch(`${this.baseURL}/agent/conversation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    input_text: message,
                    session_id: sessionId,
                    domain: 'chat',
                    conversation_context: conversationContext
                }),
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Debug logging
            console.log('🤖 Conversation response:', data);

            if (data.success) {
                // Display each step progressively
                await this._displayConversationSteps(data.steps);

                // Handle events from the orchestrator
                if (data.events && data.events.length > 0) {
                    console.log('🔧 Events:', data.events);
                    this._handleEvents(data.events);
                }

                // Handle side effects (task creation, etc.) - maintain compatibility
                if (data.side_effects && data.side_effects.length > 0) {
                    console.log('🔧 Side effects:', data.side_effects);
                    this._handleSideEffects(data.side_effects);
                }

                // Update current session and refresh conversation sessions
                if (!this.currentSessionId) {
                    this.currentSessionId = data.session_id || sessionId;
                }
                await this._loadConversationSessions();

                console.log('✅ Conversation completed successfully');
            } else {
                console.error('❌ Conversation failed:', data.error);
                throw new Error(data.error || 'Conversation failed');
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
     * Display conversation steps progressively
     */
    async _displayConversationSteps(steps) {
        if (!steps || steps.length === 0) return;

        console.log('📋 Displaying conversation steps:', steps.length);

        for (let i = 0; i < steps.length; i++) {
            const step = steps[i];

            // Add a small delay between steps for better UX
            if (i > 0) {
                await new Promise(resolve => setTimeout(resolve, 800));
            }

            // Always show typing indicator for processing steps (except when it's the final step and we want to show the result immediately)
            const isLastStep = i === steps.length - 1;
            const shouldShowTyping = !isLastStep || !step.details?.is_final;
            
            if (shouldShowTyping) {
                this._showTyping();
                this._updateTypingMessage(this._getStepDisplayMessage(step));
                
                // Wait longer for the typing indicator to be visible and give user feedback
                await new Promise(resolve => setTimeout(resolve, 1000));
            }

            // Hide typing and add the step as a bot message
            this._hideTyping();

            // Add step as a bot message with special formatting
            this._addStepMessage(step);
        }
    }

    /**
     * Add a conversation step as a message
     */
    _addStepMessage(step) {
        const stepContent = this._formatStepContent(step);
        const message = {
            type: 'bot',
            content: stepContent,
            step: step,
            timestamp: new Date().toISOString()
        };

        this.chatMessages.push(message);
        const messageElement = this._renderMessage(message);

        this._scrollToBottom();
        this._saveChatHistory();
    }

    /**
     * Format step content for display
     */
    _formatStepContent(step) {
        const { step_type, content, details } = step;
        
        // Handle missing content
        if (!content) {
            return `Step: ${step_type}`;
        }

        // For final synthesizer step, just return the content
        if (details?.is_final) {
            return content;
        }

        // For planner steps, show clean format
        if (step_type === 'planner_llm') {
            return `Planner: ${content}`;
        }

        // For action execution steps, show clean format
        if (step_type === 'action_exec') {
            const actionName = this._getActionNameFromContent(content);
            if (details?.successful_actions > 0) {
                return `Action: ${actionName} successful`;
            } else if (details?.failed_actions > 0) {
                return `Action: ${actionName} failed`;
            } else {
                return `Action: calling ${actionName}`;
            }
        }

        // For synthesizer steps, show clean format
        if (step_type === 'synthesizer_llm') {
            return `Synthesizer: thinking...`;
        }

        // For other steps, show clean format
        return `${this._getStepDisplayName(step_type)}: ${content}`;
    }

    /**
     * Get action name from content
     */
    _getActionNameFromContent(content) {
        // Extract action name from content like "Executed fetch_tasks" or "Calling fetch_tasks"
        if (!content) return 'action';
        const match = content.match(/(?:Executed|Calling|Executing)\s+(\w+)/i);
        return match ? match[1] : 'action';
    }

    /**
     * Get clean step display name
     */
    _getStepDisplayName(stepType) {
        const nameMap = {
            'workflow_start': 'Workflow',
            'ingest_user_input': 'Input',
            'planner_llm': 'Planner',
            'action_exec': 'Action',
            'synthesizer_llm': 'Synthesizer'
        };
        return nameMap[stepType] || stepType;
    }


    /**
     * Get display message for typing indicator
     */
    _getStepDisplayMessage(step) {
        const stepName = this._getStepDisplayName(step.step_type);
        
        if (step.step_type === 'planner_llm') {
            return 'Planner: thinking...';
        } else if (step.step_type === 'action_exec') {
            const actionName = this._getActionNameFromContent(step.content);
            return `Action: calling ${actionName}`;
        } else if (step.step_type === 'synthesizer_llm') {
            return 'Synthesizer: thinking...';
        } else {
            return `${stepName}: thinking...`;
        }
    }


    /**
     * Handle orchestrator events
     */
    _handleEvents(events) {
        events.forEach(event => {
            switch (event.type) {
                case 'run_started':
                    console.log('🚀 Run started:', event.run_id);
                    break;
                case 'llm_message':
                    console.log(`🧠 LLM ${event.node}:`, event.content);
                    break;
                case 'action_call':
                    console.log('🔧 Action called:', event.name, event.args);
                    this._displayActionCall(event);
                    break;
                case 'action_result':
                    console.log('✅ Action result:', event.name, event.ok ? 'success' : 'failed');
                    this._displayActionResult(event);
                    break;
                case 'final_message':
                    console.log('💬 Final message:', event.content);
                    break;
                case 'run_completed':
                    console.log('🏁 Run completed:', event.status);
                    break;
            }
        });
    }

    /**
     * Display action call in the chat
     */
    _displayActionCall(event) {
        if (!this.chatMessagesContainer) return;
        
        const actionDiv = document.createElement('div');
        actionDiv.className = 'action-call-container';
        actionDiv.innerHTML = `
            <div class="action-call-header">
                <div class="action-call-avatar">🔧</div>
                <div class="action-call-title">Executing ${this._formatActionName(event.name)}...</div>
            </div>
        `;
        
        this.chatMessagesContainer.appendChild(actionDiv);
        this._scrollToBottom();
    }

    /**
     * Display action result in the chat
     */
    _displayActionResult(event) {
        if (!this.chatMessagesContainer) return;
        
        const resultDiv = document.createElement('div');
        resultDiv.className = `action-result-container ${event.ok ? 'success' : 'error'}`;
        resultDiv.innerHTML = `
            <div class="action-result-header">
                <div class="action-result-avatar">${event.ok ? '✅' : '❌'}</div>
                <div class="action-result-title">${this._formatActionName(event.name)} ${event.ok ? 'completed' : 'failed'}</div>
            </div>
            ${event.result ? `<div class="action-result-details">${JSON.stringify(event.result, null, 2)}</div>` : ''}
            ${event.error ? `<div class="action-result-error">Error: ${event.error}</div>` : ''}
        `;
        
        this.chatMessagesContainer.appendChild(resultDiv);
        this._scrollToBottom();
    }

    /**
     * Format action names for display
     */
    _formatActionName(actionName) {
        const nameMap = {
            'create_task': 'Create Task',
            'update_task_status': 'Update Task Status',
            'reorder_tasks': 'Reorder Tasks',
            'fetch_tasks': 'Fetch Tasks',
            'no_op': 'No Operation'
        };
        return nameMap[actionName] || actionName;
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
        
        // Undo functionality removed for simplicity
        
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
        
        // No welcome message - just show empty chat

        // Render all chat messages
        this.chatMessages.forEach(message => {
            this._renderMessage(message, false);
        });
    }


    /**
     * Render single message
     */
    _renderMessage(message, animate = true) {
        if (!this.chatMessagesContainer) return null;

        const messageEl = document.createElement('div');
        let baseClass = `message ${message.type}-message ${animate ? 'fade-in' : ''}`;

        // Add step-specific classes if this is a step message
        if (message.step && message.step.step_type) {
            baseClass += ` step-message ${message.step.step_type}`;
        }

        messageEl.className = baseClass;

        // Timestamps removed for cleaner interface

        // Render different content for step messages vs regular messages
        if (message.step && message.step.step_type) {
            messageEl.innerHTML = this._renderStepMessage(message);
        } else {
            if (message.type === 'user') {
                messageEl.innerHTML = `
                    <div class="message-avatar">
                        <i class="fas fa-user"></i>
                    </div>
                    <div class="message-content">
                        ${this._formatMessage(message.content)}
                    </div>
                `;
            } else {
                // Bot messages - no avatar, just content
                messageEl.innerHTML = `
                    <div class="message-content">
                        ${this._formatMessage(message.content)}
                    </div>
                `;
            }
        }

        this.chatMessagesContainer.appendChild(messageEl);
        return messageEl;
    }

    /**
     * Render a step-specific message
     */
    _renderStepMessage(message) {
        const step = message.step;
        const content = this._formatMessage(message.content);

        // For synthesizer_llm (final step), render as plain text
        if (step.step_type === 'synthesizer_llm') {
            return `
                <div class="message-content">
                    ${content}
                </div>
            `;
        }

        // For other steps, just show the content without details
        return `
            <div class="message-content">
                ${content}
            </div>
        `;
    }

    /**
     * Render step details section
     */
    _renderStepDetails(details) {
        let detailsHtml = '<div class="step-details">';

        if (details.actions_count !== undefined) {
            detailsHtml += `<strong>Planning:</strong> ${details.actions_count} action${details.actions_count !== 1 ? 's' : ''} to execute`;
        } else if (details.successful_actions !== undefined || details.failed_actions !== undefined) {
            const successful = details.successful_actions || 0;
            const failed = details.failed_actions || 0;
            detailsHtml += `<strong>Execution:</strong> ${successful} successful, ${failed} failed`;
        }

        detailsHtml += '</div>';
        return detailsHtml;
    }

    /**
     * Format message content using proper markdown parsing
     */
    _formatMessage(content) {
        if (!content) return '';
        
        // Use a simple but robust markdown parser
        return this._parseMarkdown(content);
    }

    /**
     * Simple markdown parser that handles common formatting
     */
    _parseMarkdown(text) {
        // Split into lines for processing
        const lines = text.split('\n');
        const result = [];
        let inCodeBlock = false;
        let inList = false;
        let listType = null;

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            const trimmedLine = line.trim();

            // Handle code blocks
            if (trimmedLine.startsWith('```')) {
                if (inCodeBlock) {
                    result.push('</pre></code>');
                    inCodeBlock = false;
                } else {
                    result.push('<pre><code>');
                    inCodeBlock = true;
                }
                continue;
            }

            if (inCodeBlock) {
                result.push(this._escapeHtml(line) + '\n');
                continue;
            }

            // Handle headers
            if (trimmedLine.startsWith('### ')) {
                this._closeList(result, inList, listType);
                inList = false;
                result.push(`<h3>${this._parseInlineMarkdown(trimmedLine.slice(4))}</h3>`);
            } else if (trimmedLine.startsWith('## ')) {
                this._closeList(result, inList, listType);
                inList = false;
                result.push(`<h2>${this._parseInlineMarkdown(trimmedLine.slice(3))}</h2>`);
            } else if (trimmedLine.startsWith('# ')) {
                this._closeList(result, inList, listType);
                inList = false;
                result.push(`<h1>${this._parseInlineMarkdown(trimmedLine.slice(2))}</h1>`);
            }
            // Handle unordered lists
            else if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('* ')) {
                if (!inList || listType !== 'ul') {
                    this._closeList(result, inList, listType);
                    result.push('<ul>');
                    inList = true;
                    listType = 'ul';
                }
                result.push(`<li>${this._parseInlineMarkdown(trimmedLine.slice(2))}</li>`);
            }
            // Handle ordered lists
            else if (/^\d+\.\s/.test(trimmedLine)) {
                if (!inList || listType !== 'ol') {
                    this._closeList(result, inList, listType);
                    result.push('<ol>');
                    inList = true;
                    listType = 'ol';
                }
                const listContent = trimmedLine.replace(/^\d+\.\s/, '');
                result.push(`<li>${this._parseInlineMarkdown(listContent)}</li>`);
            }
            // Handle empty lines
            else if (trimmedLine === '') {
                this._closeList(result, inList, listType);
                inList = false;
                result.push('<br>');
            }
            // Handle regular paragraphs
            else {
                this._closeList(result, inList, listType);
                inList = false;
                result.push(`<p>${this._parseInlineMarkdown(line)}</p>`);
            }
        }

        // Close any remaining list
        this._closeList(result, inList, listType);

        return result.join('');
    }

    /**
     * Parse inline markdown (bold, italic, code, links)
     */
    _parseInlineMarkdown(text) {
        return text
            // Bold: **text** -> <strong>text</strong>
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Italic: *text* -> <em>text</em>
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Inline code: `code` -> <code>code</code>
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            // Links: [text](url) -> <a href="url">text</a>
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    }

    /**
     * Close list if open
     */
    _closeList(result, inList, listType) {
        if (inList) {
            result.push(`</${listType}>`);
        }
    }

    /**
     * Escape HTML characters
     */
    _escapeHtml(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    /**
     * Show typing indicator
     */
    _showTyping() {
        try {
            this.isTyping = true;
            
            // Ensure chatMessagesContainer exists
            if (!this.chatMessagesContainer) {
                console.warn('⚠️ chatMessagesContainer not found, cannot show typing indicator');
                return;
            }
            
            // Create typing indicator if it doesn't exist
            if (!this.typingIndicator) {
                this.typingIndicator = document.createElement('div');
                this.typingIndicator.className = 'typing-indicator';
                this.typingIndicator.innerHTML = `
                    <span class="typing-message">Giskard is thinking</span>
                    <div class="dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                `;
                this.chatMessagesContainer.appendChild(this.typingIndicator);
            }
            
            this.typingIndicator.style.display = 'flex';
            this._scrollToBottom();
            
            console.log('✅ Typing indicator shown');
        } catch (error) {
            console.error('❌ Failed to show typing indicator:', error);
        }
    }

    /**
     * Hide typing indicator
     */
    _hideTyping() {
        try {
            this.isTyping = false;
            if (this.typingIndicator) {
                this.typingIndicator.style.display = 'none';
                console.log('✅ Typing indicator hidden');
            }
        } catch (error) {
            console.error('❌ Failed to hide typing indicator:', error);
        }
    }

    /**
     * Update typing indicator message
     */
    _updateTypingMessage(message) {
        try {
            if (this.typingIndicator) {
                const messageElement = this.typingIndicator.querySelector('.typing-message');
                if (messageElement) {
                    messageElement.textContent = message;
                    console.log('✅ Typing message updated to:', message);
                } else {
                    console.warn('⚠️ Typing message element not found');
                }
            } else {
                console.warn('⚠️ Typing indicator not found when updating message');
            }
        } catch (error) {
            console.error('❌ Failed to update typing message:', error);
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
     * Load chat history from localStorage (legacy support)
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
     * Load conversation threads from backend
     */
    async _loadConversationSessions() {
        try {
            const response = await fetch(`${this.baseURL}/agent/sessions`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.sessions) {
                    this.conversationHistory = data.sessions;
                    console.log('📚 Loaded conversation sessions:', this.conversationHistory.length);
                }
            }
        } catch (error) {
            console.error('Failed to load conversation sessions:', error);
        }
    }

    /**
     * Load messages for a specific thread
     */
    async _loadSessionMessages(sessionId) {
        try {
            const response = await fetch(`${this.baseURL}/agent/sessions/${sessionId}`);
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.traces) {
                    // Convert backend traces to chat messages format
                    this.chatMessages = data.traces.map(trace => {
                        // Create user message
                        const userMessage = {
                            type: 'user',
                            content: trace.user_message,
                            timestamp: trace.created_at
                        };
                        
                        // Create bot message if there's a response
                        const botMessage = trace.assistant_response ? {
                            type: 'bot',
                            content: trace.assistant_response,
                            timestamp: trace.completed_at || trace.created_at
                        } : null;
                        
                        // Return both messages if bot message exists
                        return botMessage ? [userMessage, botMessage] : [userMessage];
                    }).flat();

                    this.currentSessionId = sessionId;
                    this._renderMessages();
                    this._hideSuggestions();
                    console.log(`📖 Loaded ${this.chatMessages.length} messages for session: ${sessionId}`);
                }
            }
        } catch (error) {
            console.error('Failed to load session messages:', error);
        }
    }

    /**
     * Create a new conversation thread
     */
    async _createNewSession(inputText) {
        const sessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        try {
            // Create initial conversation in the session
            const response = await fetch(`${this.baseURL}/agent/conversation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    input_text: inputText,
                    session_id: sessionId,
                    domain: 'chat'
                })
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    this.currentSessionId = sessionId;
                    await this._loadSessionMessages(sessionId);
                    await this._loadConversationSessions(); // Refresh sessions list
                    return sessionId;
                }
            }
        } catch (error) {
            console.error('Failed to create new session:', error);
        }
        return sessionId;
    }

    /**
     * Get conversation context from previous messages in current thread
     */
    _getConversationContext() {
        if (!this.currentSessionId || this.chatMessages.length === 0) {
            return [];
        }

        // Return last 10 messages for context (excluding the current one being processed)
        return this.chatMessages.slice(-10).map(msg => ({
            type: msg.type,
            content: msg.content,
            timestamp: msg.timestamp
        }));
    }

    /**
     * Load the most recent conversation thread
     */
    async _loadMostRecentSession() {
        if (this.conversationHistory.length === 0) {
            // No conversation history, just show welcome message
            this._renderMessages();
            this._showSuggestions();
            return;
        }

        try {
            // Load the most recent session (first in the sorted list)
            const mostRecentSession = this.conversationHistory[0];
            if (mostRecentSession && mostRecentSession.session_id) {
                await this._loadSessionMessages(mostRecentSession.session_id);
                console.log('📖 Loaded most recent conversation session');
            }
        } catch (error) {
            console.error('Failed to load most recent session:', error);
            // Fallback to showing welcome message if loading fails
            this._renderMessages();
            this._showSuggestions();
        }
    }

    /**
     * Handle streaming response from the agent
     */
    async _handleStreamingResponse(response, steps) {
        if (!steps || steps.length === 0) return;

        console.log('📡 Starting streaming response with', steps.length, 'steps');

        for (let i = 0; i < steps.length; i++) {
            const step = steps[i];

            // Add a small delay between steps for better UX
            if (i > 0) {
                await new Promise(resolve => setTimeout(resolve, 800));
            }

            // Show typing indicator for non-final steps
            if (!step.details?.is_final) {
                this._showTyping();
                this._updateTypingMessage(this._getStepDisplayMessage(step));
            }

            // Wait a moment for the typing indicator to be visible
            await new Promise(resolve => setTimeout(resolve, 500));

            // Hide typing and add the step as a bot message
            this._hideTyping();

            // Add step as a bot message with special formatting
            this._addStepMessage(step);
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
     * NEW: Display tool calls in the chat interface
     */
    _displayToolCalls(toolCalls) {
        if (!this.chatMessagesContainer || !toolCalls.length) return;
        
        // Create a tool calls container
        const toolCallsContainer = document.createElement('div');
        toolCallsContainer.className = 'tool-calls-container';
        toolCallsContainer.innerHTML = `
            <div class="tool-calls-header">
                <div class="tool-calls-avatar">🔧</div>
                <div class="tool-calls-title">Executing ${toolCalls.length} action${toolCalls.length > 1 ? 's' : ''}...</div>
            </div>
            <div class="tool-calls-list">
                ${toolCalls.map(toolCall => this._renderToolCall(toolCall)).join('')}
            </div>
        `;
        
        this.chatMessagesContainer.appendChild(toolCallsContainer);
        this._scrollToBottom();
    }

    /**
     * NEW: Render individual tool call
     */
    _renderToolCall(toolCall) {
        const statusIcon = toolCall.status === 'completed' ? 
            (toolCall.result?.success ? '✅' : '❌') : '⏳';
        
        const statusClass = toolCall.status === 'completed' ? 
            (toolCall.result?.success ? 'success' : 'error') : 'executing';
        
        return `
            <div class="tool-call-item ${statusClass}">
                <div class="tool-call-header">
                    <span class="tool-call-icon">${statusIcon}</span>
                    <span class="tool-call-name">${this._formatToolName(toolCall.tool_name)}</span>
                    <span class="tool-call-status">${toolCall.status}</span>
                </div>
                ${this._renderToolCallDetails(toolCall)}
            </div>
        `;
    }

    /**
     * NEW: Format tool names for display
     */
    _formatToolName(toolName) {
        const nameMap = {
            'create_task': 'Create Task',
            'get_tasks': 'Get Tasks',
            'update_task': 'Update Task',
            'delete_task': 'Delete Task',
            'update_task_status': 'Update Status'
        };
        return nameMap[toolName] || toolName;
    }

    /**
     * NEW: Render tool call details
     */
    _renderToolCallDetails(toolCall) {
        let details = '';
        
        if (toolCall.tool_name === 'create_task' && toolCall.arguments.title) {
            details = `<div class="tool-call-details">Creating: "${toolCall.arguments.title}"</div>`;
        } else if (toolCall.tool_name === 'get_tasks') {
            const status = toolCall.arguments.status || 'all';
            details = `<div class="tool-call-details">Fetching ${status} tasks</div>`;
        } else if (toolCall.tool_name === 'update_task' && toolCall.arguments.title) {
            details = `<div class="tool-call-details">Updating: "${toolCall.arguments.title}"</div>`;
        }
        
        if (toolCall.result && !toolCall.result.success) {
            details += `<div class="tool-call-error">Error: ${toolCall.result.error}</div>`;
        }
        
        return details;
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
