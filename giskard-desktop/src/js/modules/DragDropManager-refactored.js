/**
 * DragDropManager - Orchestrates drag and drop reordering of tasks
 *
 * Refactored to use modular architecture:
 * - DragState: Manages all state
 * - DragVisualFeedback: Handles UI updates
 * - DragEventHandlers: Manages event listeners
 * - DragCalculations: Position and index calculations
 */
import DragState from './drag-drop/DragState.js';
import DragVisualFeedback from './drag-drop/DragVisualFeedback.js';
import DragEventHandlers from './drag-drop/DragEventHandlers.js';
import DragCalculations from './drag-drop/DragCalculations.js';

class DragDropManager {
    constructor() {
        // Initialize modules
        this.state = new DragState();
        this.visual = new DragVisualFeedback(this.state);
        this.eventHandlers = new DragEventHandlers(
            this.state,
            this.visual,
            this.handleReorder.bind(this)
        );

        // Make DragCalculations globally available for visual feedback
        window.DragCalculations = DragCalculations;
    }

    /**
     * Initialize drag and drop for all task items
     */
    initializeDragDrop() {
        // Debounce rapid re-initialization calls
        if (this.state.shouldDebounceInit()) {
            if (this.state.DEBUG) {
                console.log('⏱️ Initialization debounced, too soon since last init');
            }
            return;
        }
        this.state.updateInitTime();

        if (this.state.DEBUG) {
            console.log('🔧 DragDropManager.initializeDragDrop() called');
        }

        // Clean up existing event listeners first
        this.cleanup();

        // Wait for DOM to be fully ready using requestAnimationFrame
        requestAnimationFrame(() => {
            // Double-check that cleanup is complete before proceeding
            if (this.state.isCleanedUp) {
                if (this.state.DEBUG) {
                    console.warn('⚠️ Cleanup still in progress, deferring initialization');
                }
                requestAnimationFrame(() => this.initializeDragDrop());
                return;
            }

            const taskItems = document.querySelectorAll('.task-item');
            if (this.state.DEBUG) {
                console.log(`📝 Found ${taskItems.length} task items to initialize`);
            }

            if (taskItems.length === 0) {
                if (this.state.DEBUG) {
                    console.warn('⚠️ No task items found to initialize');
                }
                return;
            }

            let successCount = 0;
            taskItems.forEach((taskItem, index) => {
                if (this.state.DEBUG) {
                    console.log(`⚙️  Initializing drag for task ${index + 1}:`, taskItem.dataset);
                }
                const success = this.eventHandlers.addTaskHandlers(taskItem);
                if (success) successCount++;
            });

            if (this.state.DEBUG) {
                console.log(`🎯 DragDropManager initialization complete: ${successCount}/${taskItems.length} tasks initialized`);
            }
        });
    }

    /**
     * Clean up existing event listeners
     */
    cleanup() {
        if (this.state.DEBUG) {
            console.log('🧹 Cleaning up existing drag-drop listeners');
        }

        this.eventHandlers.cleanup();
        this.visual.removeAllVisuals();
    }

    /**
     * Handle the reorder operation
     * @param {Array<number>} newTaskIdSequence - New sequence of task IDs
     */
    handleReorder(newTaskIdSequence) {
        // Emit reorder event
        const event_detail = {
            detail: { taskIdSequence: newTaskIdSequence }
        };

        document.dispatchEvent(new CustomEvent('task:reorder', event_detail));
    }

    /**
     * Clear any existing drag states
     */
    clearDragState() {
        this.visual.removeAllVisuals();
        this.state.clearDraggedTask();
    }

    /**
     * Enable debug mode for troubleshooting
     */
    enableDebug() {
        this.state.enableDebug();
        console.log('🐛 DragDropManager debug mode enabled');
    }

    /**
     * Disable debug mode
     */
    disableDebug() {
        this.state.disableDebug();
        console.log('🐛 DragDropManager debug mode disabled');
    }

    /**
     * Verify drag-drop is properly initialized and working
     * @returns {boolean} true if all tasks have handlers attached
     */
    verifyInitialization() {
        const taskItems = document.querySelectorAll('.task-item');
        const taskCount = taskItems.length;
        const handlersCount = this.eventHandlers.taskEventHandlers.size;

        if (taskCount === 0) {
            if (this.state.DEBUG) {
                console.log('✅ No tasks to verify');
            }
            return true;
        }

        const allHaveHandlers = taskCount === handlersCount;

        if (!allHaveHandlers) {
            console.warn(`⚠️ Drag-drop initialization mismatch: ${taskCount} tasks but ${handlersCount} handlers`);
            return false;
        }

        // Verify each task item has valid handlers
        let invalidCount = 0;
        taskItems.forEach(taskItem => {
            if (!this.eventHandlers.taskEventHandlers.has(taskItem)) {
                invalidCount++;
                if (this.state.DEBUG) {
                    console.warn('⚠️ Task missing handlers:', taskItem.dataset?.taskId);
                }
            }
        });

        if (invalidCount > 0) {
            console.warn(`⚠️ ${invalidCount} tasks missing handlers`);
            return false;
        }

        if (this.state.DEBUG) {
            console.log(`✅ Drag-drop verified: ${handlersCount} tasks properly initialized`);
        }
        return true;
    }

    /**
     * Force re-initialization of drag-drop (used for recovery)
     */
    forceReinit() {
        console.log('🔄 Force re-initializing drag-drop...');
        this.state.lastInitTime = 0; // Reset debounce
        this.initializeDragDrop();
    }
}

export default DragDropManager;
