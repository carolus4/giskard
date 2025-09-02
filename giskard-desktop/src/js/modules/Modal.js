/**
 * Modal - Reusable modal component system
 */
class Modal {
    constructor(modalId) {
        this.modalId = modalId;
        this.modal = document.getElementById(modalId);
        this.isOpen = false;
        
        if (!this.modal) {
            throw new Error(`Modal with id '${modalId}' not found`);
        }

        this._bindEvents();
    }

    /**
     * Bind modal events
     */
    _bindEvents() {
        // Close on backdrop click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });

        // Close button
        const closeBtn = this.modal.querySelector('.modal-close, .task-detail-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }

        // ESC key to close
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    }

    /**
     * Open the modal
     */
    open() {
        if (this.isOpen) return;
        
        this.modal.classList.add('show');
        this.isOpen = true;
        
        // Focus on first input if available
        setTimeout(() => {
            const firstInput = this.modal.querySelector('input, textarea');
            if (firstInput) {
                firstInput.focus();
            }
        }, 300);

        // Emit open event
        this.modal.dispatchEvent(new CustomEvent('modal:open'));
    }

    /**
     * Close the modal
     */
    close() {
        if (!this.isOpen) return;
        
        this.modal.classList.remove('show');
        this.isOpen = false;

        // Clear form inputs if it's a form modal
        this._clearFormInputs();

        // Emit close event
        this.modal.dispatchEvent(new CustomEvent('modal:close'));
    }

    /**
     * Toggle modal open/close
     */
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    /**
     * Set modal content (for dynamic modals)
     */
    setContent(content) {
        const body = this.modal.querySelector('.modal-body, .task-detail-body');
        if (body) {
            body.innerHTML = content;
        }
    }

    /**
     * Get form data from modal
     */
    getFormData() {
        const formData = {};
        const inputs = this.modal.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            if (input.name || input.id) {
                const key = input.name || input.id;
                formData[key] = input.value.trim();
            }
        });

        return formData;
    }

    /**
     * Set form data in modal
     */
    setFormData(data) {
        Object.entries(data).forEach(([key, value]) => {
            const input = this.modal.querySelector(`[name="${key}"], #${key}`);
            if (input) {
                input.value = value || '';
            }
        });
    }

    /**
     * Clear form inputs
     */
    _clearFormInputs() {
        const inputs = this.modal.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            if (input.type !== 'button' && input.type !== 'submit') {
                input.value = '';
            }
        });
    }

    /**
     * Enable/disable form submit button based on validation
     */
    validateForm(validationFn) {
        const submitBtn = this.modal.querySelector('.btn-add, .save-btn');
        if (!submitBtn) return;

        const inputs = this.modal.querySelectorAll('input[required], textarea[required]');
        
        const validate = () => {
            const isValid = validationFn ? validationFn() : Array.from(inputs).every(input => input.value.trim());
            submitBtn.disabled = !isValid;
        };

        inputs.forEach(input => {
            input.addEventListener('input', validate);
        });

        // Initial validation
        validate();
    }
}

/**
 * AddTaskModal - Specialized modal for adding tasks
 */
class AddTaskModal extends Modal {
    constructor() {
        super('add-task-modal');
        this._setupAddTaskModal();
    }

    _setupAddTaskModal() {
        // Enable/disable add button based on title input
        const titleInput = this.modal.querySelector('#modal-task-name');
        const addBtn = this.modal.querySelector('#modal-add-btn');
        const cancelBtn = this.modal.querySelector('#modal-cancel-btn');

        if (titleInput && addBtn) {
            titleInput.addEventListener('input', () => {
                addBtn.disabled = !titleInput.value.trim();
            });

            // Enter key to submit
            titleInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !addBtn.disabled) {
                    addBtn.click();
                }
            });
        }

        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.close());
        }
    }

    open() {
        super.open();
        // Reset add button state
        const addBtn = this.modal.querySelector('#modal-add-btn');
        if (addBtn) addBtn.disabled = true;
    }

    getTaskData() {
        return {
            title: this.modal.querySelector('#modal-task-name')?.value.trim() || '',
            description: this.modal.querySelector('#modal-task-description')?.value.trim() || ''
        };
    }
}

/**
 * TaskDetailModal - Specialized modal for task details
 */
class TaskDetailModal extends Modal {
    constructor() {
        super('task-detail-modal');
        this.currentTaskData = null;
        this._setupTaskDetailModal();
    }

    _setupTaskDetailModal() {
        // Save button
        const saveBtn = this.modal.querySelector('#save-task-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => {
                this.modal.dispatchEvent(new CustomEvent('task:save', { 
                    detail: this.getTaskData() 
                }));
            });
        }

        // Progress button
        const progressBtn = this.modal.querySelector('#detail-progress-btn');
        if (progressBtn) {
            progressBtn.addEventListener('click', () => {
                this.modal.dispatchEvent(new CustomEvent('task:toggle-progress', {
                    detail: { taskData: this.currentTaskData }
                }));
            });
        }

        // Checkbox
        const checkbox = this.modal.querySelector('#detail-checkbox');
        if (checkbox) {
            checkbox.addEventListener('change', (e) => {
                this.modal.dispatchEvent(new CustomEvent('task:toggle-completion', {
                    detail: { 
                        checked: e.target.checked, 
                        taskData: this.currentTaskData 
                    }
                }));
            });
        }

        // Keyboard shortcuts
        this._setupKeyboardShortcuts();
    }

    _setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            if (!this.isOpen) return;

            // Cmd+Enter or Ctrl+Enter to save
            if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                e.preventDefault();
                const saveBtn = this.modal.querySelector('#save-task-btn');
                if (saveBtn) {
                    // Visual feedback
                    saveBtn.style.transform = 'scale(0.95)';
                    setTimeout(() => {
                        saveBtn.style.transform = '';
                    }, 150);
                    saveBtn.click();
                }
            }
        });
    }

    showTask(taskData) {
        this.currentTaskData = taskData;
        
        // Populate fields
        const titleInput = this.modal.querySelector('#detail-title');
        const descriptionInput = this.modal.querySelector('#detail-description');
        const checkbox = this.modal.querySelector('#detail-checkbox');
        const titleRow = this.modal.querySelector('.task-title-row');
        const progressBtn = this.modal.querySelector('#detail-progress-btn');

        if (titleInput) titleInput.value = taskData.title || '';
        if (descriptionInput) descriptionInput.value = taskData.description || '';
        
        // Set checkbox state
        if (checkbox) {
            checkbox.checked = taskData.status === 'done';
        }
        
        // Update title row styling
        if (titleRow) {
            titleRow.classList.toggle('completed', taskData.status === 'done');
        }

        // Update progress button
        if (progressBtn) {
            const isInProgress = taskData.status === 'in_progress';
            progressBtn.classList.toggle('in-progress', isInProgress);
            progressBtn.innerHTML = isInProgress 
                ? '<i class="fas fa-pause"></i><span>pause</span>'
                : '<i class="fas fa-play"></i><span>start</span>';
        }

        // Set file index for saving
        this.modal.dataset.fileIdx = taskData.file_idx;

        // Update keyboard shortcut display
        this._updateKeyboardShortcut();

        this.open();
    }

    getTaskData() {
        return {
            fileIdx: this.currentTaskData?.file_idx,
            title: this.modal.querySelector('#detail-title')?.value.trim() || '',
            description: this.modal.querySelector('#detail-description')?.value.trim() || ''
        };
    }

    _updateKeyboardShortcut() {
        const shortcutSpan = this.modal.querySelector('.keyboard-shortcut');
        if (shortcutSpan) {
            const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
            shortcutSpan.textContent = isMac ? '⌘↵' : 'Ctrl+↵';
        }
    }
}

export { Modal, AddTaskModal, TaskDetailModal };
