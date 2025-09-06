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
 * ConfirmationModal - Custom confirmation dialog
 */
class ConfirmationModal extends Modal {
    constructor() {
        super('confirmation-modal');
        this.resolve = null;
        this._setupConfirmationModal();
    }

    _setupConfirmationModal() {
        const cancelBtn = this.modal.querySelector('#confirmation-cancel');
        const confirmBtn = this.modal.querySelector('#confirmation-confirm');
        const closeBtn = this.modal.querySelector('#confirmation-close');

        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this._handleCancel());
        }

        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => this._handleConfirm());
        }

        if (closeBtn) {
            closeBtn.addEventListener('click', () => this._handleCancel());
        }

        // ESC key to cancel
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this._handleCancel();
            }
        });
    }

    _handleCancel() {
        this.close();
        if (this.resolve) {
            this.resolve(false);
            this.resolve = null;
        }
    }

    _handleConfirm() {
        this.close();
        if (this.resolve) {
            this.resolve(true);
            this.resolve = null;
        }
    }

    show(message, title = 'Confirm') {
        const messageEl = this.modal.querySelector('#confirmation-message');
        const titleEl = this.modal.querySelector('.modal-header h3');
        
        if (messageEl) messageEl.textContent = message;
        if (titleEl) titleEl.textContent = title;

        this.open();

        return new Promise((resolve) => {
            this.resolve = resolve;
        });
    }
}

export { Modal, ConfirmationModal };
