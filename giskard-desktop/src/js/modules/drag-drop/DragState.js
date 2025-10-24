/**
 * DragState - Manages all drag and drop state
 * Single source of truth for drag operation state
 */
class DragState {
    constructor() {
        // Debug flag
        this.DEBUG = false;

        // Core drag state
        this.draggedTask = null;
        this.insertionIndex = -1;
        this.lastMouseY = 0;
        this.isDropping = false;
        this.isDragging = false;

        // Performance and reliability
        this.lastReorderTime = 0;
        this.reorderDebounceMs = 500;
        this.lastInitTime = 0;
        this.initDebounceMs = 200;
        this.isCleanedUp = false;

        // Throttling
        this.mouseMoveThrottle = null;
        this.throttleDelay = 16; // ~60fps

        // Container reference
        this.taskListContainer = null;
    }

    /**
     * Check if initialization should be debounced
     * @returns {boolean}
     */
    shouldDebounceInit() {
        const now = Date.now();
        return now - this.lastInitTime < this.initDebounceMs;
    }

    /**
     * Update last init time
     */
    updateInitTime() {
        this.lastInitTime = Date.now();
    }

    /**
     * Check if reorder should be debounced
     * @returns {boolean}
     */
    shouldDebounceReorder() {
        const now = Date.now();
        return now - this.lastReorderTime < this.reorderDebounceMs;
    }

    /**
     * Update last reorder time
     */
    updateReorderTime() {
        this.lastReorderTime = Date.now();
    }

    /**
     * Set dragged task
     * @param {Object} task - Task object with id, title, element
     */
    setDraggedTask(task) {
        this.draggedTask = task;
        this.isDragging = true;
    }

    /**
     * Clear dragged task
     */
    clearDraggedTask() {
        this.draggedTask = null;
        this.isDragging = false;
        this.insertionIndex = -1;
        this.lastMouseY = 0;
        this.isDropping = false;
    }

    /**
     * Set insertion index
     * @param {number} index
     */
    setInsertionIndex(index) {
        this.insertionIndex = index;
    }

    /**
     * Set mouse Y position
     * @param {number} y
     */
    setMouseY(y) {
        this.lastMouseY = y;
    }

    /**
     * Set cleanup flag
     * @param {boolean} value
     */
    setCleanedUp(value) {
        this.isCleanedUp = value;
    }

    /**
     * Clear throttle timeout
     */
    clearThrottle() {
        if (this.mouseMoveThrottle) {
            clearTimeout(this.mouseMoveThrottle);
            this.mouseMoveThrottle = null;
        }
    }

    /**
     * Set throttle timeout
     * @param {number} timeoutId
     */
    setThrottle(timeoutId) {
        this.mouseMoveThrottle = timeoutId;
    }

    /**
     * Reset all state
     */
    reset() {
        this.clearDraggedTask();
        this.clearThrottle();
        this.taskListContainer = null;
    }

    /**
     * Enable debug mode
     */
    enableDebug() {
        this.DEBUG = true;
        console.log('🐛 DragState debug mode enabled');
    }

    /**
     * Disable debug mode
     */
    disableDebug() {
        this.DEBUG = false;
    }

    /**
     * Log debug message if debug enabled
     * @param {string} message
     * @param  {...any} args
     */
    log(message, ...args) {
        if (this.DEBUG) {
            console.log(message, ...args);
        }
    }
}

export default DragState;
