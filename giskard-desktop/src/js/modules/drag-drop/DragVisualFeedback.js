/**
 * DragVisualFeedback - Manages all visual feedback during drag operations
 * Handles insertion lines, visual classes, and DOM updates
 */
class DragVisualFeedback {
    constructor(state) {
        this.state = state;
    }

    /**
     * Apply visual feedback when drag starts
     * @param {HTMLElement} taskElement - Task element being dragged
     */
    applyDragStartVisuals(taskElement) {
        document.body.classList.add('dragging');
        taskElement.classList.add('selected-for-move');
    }

    /**
     * Remove all visual feedback
     */
    removeAllVisuals() {
        document.body.classList.remove('dragging');
        document.querySelectorAll('.task-item').forEach(item => {
            item.classList.remove('selected-for-move');
        });

        // Remove insertion line
        const insertionLine = document.querySelector('.insertion-line');
        if (insertionLine) {
            insertionLine.remove();
        }
    }

    /**
     * Create the insertion line element
     */
    createInsertionLine() {
        // Remove any existing insertion line
        const existing = document.querySelector('.insertion-line');
        if (existing) {
            existing.remove();
        }

        // Create new insertion line with clean styling
        const insertionLine = document.createElement('div');
        insertionLine.className = 'insertion-line';
        insertionLine.style.top = '-10px'; // Start hidden above viewport

        // Add to document body for fixed positioning
        document.body.appendChild(insertionLine);

        if (this.state.DEBUG) {
            console.log('✅ Created clean insertion line');
        }
    }

    /**
     * Update insertion line position based on mouse Y
     * @param {number} mouseY - Current mouse Y position
     */
    updateInsertionLinePosition(mouseY) {
        const insertionLine = document.querySelector('.insertion-line');
        if (!insertionLine || !mouseY) {
            if (this.state.DEBUG) {
                console.log('⚠️ Cannot update line - missing line or mouseY:', {
                    hasLine: !!insertionLine,
                    mouseY: mouseY
                });
            }
            return;
        }

        // Import calculation function
        const DragCalculations = window.DragCalculations ||
            (typeof require !== 'undefined' ? require('./DragCalculations.js').default : null);

        if (!DragCalculations) {
            console.error('DragCalculations not available');
            return;
        }

        // Find the closest task boundary for snapping
        const snappedY = DragCalculations.findClosestTaskBoundary(mouseY);

        // Use the snapped position
        const oldTop = insertionLine.style.top;
        insertionLine.style.top = `${snappedY}px`;

        if (this.state.DEBUG) {
            console.log(`📍 LINE MOVED: ${oldTop} → ${snappedY}px (mouse: ${mouseY})`);
        }
    }

    /**
     * Initialize insertion line tracking
     * @returns {boolean} - True if successful
     */
    initializeInsertionTracking() {
        if (this.state.DEBUG) {
            console.log('Initializing insertion tracking...');
        }

        // Find the actual tasks container
        const firstTask = document.querySelector('.task-item');
        if (!firstTask) {
            if (this.state.DEBUG) {
                console.error('No tasks found to determine container');
            }
            return false;
        }

        this.state.taskListContainer = firstTask.parentElement;
        if (this.state.DEBUG) {
            console.log('Task container found:', this.state.taskListContainer.className);
        }

        // Create insertion line
        this.createInsertionLine();

        if (this.state.DEBUG) {
            console.log('✅ Insertion tracking initialized');
        }

        return true;
    }

    /**
     * Validate that task element is still in DOM
     * @param {HTMLElement} element - Element to validate
     * @returns {boolean}
     */
    isElementValid(element) {
        return element && element.isConnected;
    }

    /**
     * Get task data from DOM element
     * @param {HTMLElement} element - Task element
     * @returns {Object|null} - Task data or null if invalid
     */
    getTaskDataFromElement(element) {
        if (!this.isElementValid(element)) {
            return null;
        }

        const taskIdStr = element.dataset.taskId;
        const taskId = taskIdStr && taskIdStr !== '' ? parseInt(taskIdStr) : null;
        const taskTitle = element.querySelector('.task-title')?.textContent || 'Unknown';

        if (taskId === null || isNaN(taskId)) {
            if (this.state.DEBUG) {
                console.error(`❌ Invalid taskId for task: "${taskTitle}" - taskId: "${taskIdStr}"`);
            }
            return null;
        }

        return {
            id: taskId,
            title: taskTitle,
            element: element
        };
    }
}

export default DragVisualFeedback;
