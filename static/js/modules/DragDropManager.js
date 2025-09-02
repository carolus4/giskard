/**
 * DragDropManager - Handles drag and drop reordering of tasks
 */
class DragDropManager {
    constructor() {
        this.draggedTask = null;
        this.insertionIndex = -1;
        this.taskListContainer = null;
        this.lastMouseY = 0;
        this.isDropping = false;
        this.dragOverHandler = null;
        this.dropHandler = null;
    }

    /**
     * Initialize drag and drop for all task items
     */
    initializeDragDrop() {
        const taskItems = document.querySelectorAll('.task-item');
        taskItems.forEach(taskItem => {
            this.addDragHandlers(taskItem);
        });
    }

    /**
     * Add drag handlers to a single task item
     */
    addDragHandlers(taskItem) {
        const dragHandle = taskItem.querySelector('.task-drag-handle');
        if (!dragHandle) return;

        // Make the entire task item draggable, but only when initiated from the handle
        taskItem.draggable = false;
        
        // Drag handle mouse down - enable dragging
        dragHandle.addEventListener('mousedown', (e) => {
            console.log('🖱️ Mouse down on drag handle');
            taskItem.draggable = true;
        });
        
        // Also enable dragging when mouse leaves the handle (in case user drags quickly)
        dragHandle.addEventListener('mouseleave', (e) => {
            setTimeout(() => {
                taskItem.draggable = false;
            }, 100);
        });
        
        // Drag start
        taskItem.addEventListener('dragstart', (e) => {
            if (!taskItem.draggable) {
                e.preventDefault();
                return;
            }
            
            this._handleDragStart(e, taskItem);
        });
        
        // Drag end
        taskItem.addEventListener('dragend', (e) => {
            this._handleDragEnd(e, taskItem);
        });
    }

    /**
     * Handle drag start
     */
    _handleDragStart(event, taskItem) {
        const task = this._getTaskDataFromElement(taskItem);
        
        console.log('🎯 DRAG START: Dragging task:', task.title, 'file_idx:', task.file_idx);
        
        // Add dragging state
        document.body.classList.add('dragging');
        taskItem.classList.add('selected-for-move');
        
        // Store the dragged task data
        this.draggedTask = {
            file_idx: task.file_idx,
            title: task.title,
            element: taskItem
        };
        
        // Store the task data for drop event
        event.dataTransfer.setData('text/plain', JSON.stringify({
            file_idx: task.file_idx,
            title: task.title
        }));
        event.dataTransfer.effectAllowed = 'move';
        
        // Create insertion line and add mouse tracking
        setTimeout(() => this._initializeInsertionTracking(), 10);
    }

    /**
     * Handle drag end
     */
    _handleDragEnd(event, taskItem) {
        console.log('Drag ended');
        document.body.classList.remove('dragging');
        taskItem.draggable = false;
        this._cleanupDragState();
    }

    /**
     * Initialize insertion line tracking
     */
    _initializeInsertionTracking() {
        console.log('Initializing insertion tracking...');
        
        // Find the actual tasks container
        const firstTask = document.querySelector('.task-item');
        if (!firstTask) {
            console.error('No tasks found to determine container');
            return;
        }
        
        this.taskListContainer = firstTask.parentElement;
        console.log('Task container found:', this.taskListContainer.className);
        
        // Create insertion line
        this._createInsertionLine();
        
        // Add event listeners to the broader content area for better mouse tracking
        const contentArea = document.querySelector('.content-body') || this.taskListContainer;
        
        this.dragOverHandler = (e) => this._handleDragOver(e);
        this.dropHandler = (e) => this._handleDrop(e);
        
        contentArea.addEventListener('dragover', this.dragOverHandler);
        contentArea.addEventListener('drop', this.dropHandler);
        
        console.log('✅ Insertion tracking initialized');
    }

    /**
     * Create insertion line
     */
    _createInsertionLine() {
        // Remove any existing insertion line
        const existing = document.querySelector('.insertion-line');
        if (existing) {
            existing.remove();
        }
        
        // Create new insertion line with fixed positioning
        const insertionLine = document.createElement('div');
        insertionLine.className = 'insertion-line';
        insertionLine.style.top = '-10px'; // Start hidden
        
        // Add to document body for fixed positioning
        document.body.appendChild(insertionLine);
        
        console.log('Created fixed-position insertion line');
    }

    /**
     * Handle drag over events
     */
    _handleDragOver(event) {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
        
        if (!this.draggedTask) return;
        
        // Store mouse position and update insertion line position
        this.lastMouseY = event.clientY;
        
        // Calculate insertion index for drop logic
        const insertionIndex = this._calculateInsertionIndex(event.clientY);
        this.insertionIndex = insertionIndex;
        
        // Update insertion line to follow mouse directly
        this._updateInsertionLinePosition();
    }

    /**
     * Calculate where to insert the dragged task
     */
    _calculateInsertionIndex(mouseY) {
        const taskItems = Array.from(document.querySelectorAll('.task-item')).filter(
            item => !item.classList.contains('selected-for-move')
        );
        
        if (taskItems.length === 0) {
            return 0;
        }
        
        // Find which task boundary we're closest to
        let insertIndex = 0;
        let minDistance = Infinity;
        
        // Check before first task
        const firstRect = taskItems[0].getBoundingClientRect();
        const distanceToFirst = Math.abs(mouseY - (firstRect.top - 5));
        if (distanceToFirst < minDistance) {
            minDistance = distanceToFirst;
            insertIndex = 0;
        }
        
        // Check after each task
        taskItems.forEach((taskItem, i) => {
            const rect = taskItem.getBoundingClientRect();
            const afterTaskY = rect.bottom + 5;
            const distance = Math.abs(mouseY - afterTaskY);
            
            if (distance < minDistance) {
                minDistance = distance;
                insertIndex = i + 1;
            }
        });
        
        return insertIndex;
    }

    /**
     * Update insertion line position
     */
    _updateInsertionLinePosition() {
        const insertionLine = document.querySelector('.insertion-line');
        if (!insertionLine || !this.lastMouseY) return;
        
        // Find the closest task boundary for snapping
        const snappedY = this._findClosestTaskBoundary(this.lastMouseY);
        
        // Use the snapped position
        insertionLine.style.top = `${snappedY}px`;
        
        console.log(`Mouse Y: ${this.lastMouseY}, Snapped Y: ${snappedY}, Insert Index: ${this.insertionIndex}`);
    }

    /**
     * Find closest task boundary for insertion line snapping
     */
    _findClosestTaskBoundary(mouseY) {
        const taskItems = Array.from(document.querySelectorAll('.task-item')).filter(
            item => !item.classList.contains('selected-for-move')
        );
        
        if (taskItems.length === 0) {
            return mouseY;
        }
        
        let closestY = mouseY;
        let minDistance = Infinity;
        
        // Check position before first task
        const firstTask = taskItems[0];
        const firstRect = firstTask.getBoundingClientRect();
        const beforeFirst = firstRect.top - 5;
        const distanceToFirst = Math.abs(mouseY - beforeFirst);
        if (distanceToFirst < minDistance) {
            minDistance = distanceToFirst;
            closestY = beforeFirst;
        }
        
        // Check position after each task
        taskItems.forEach((task) => {
            const rect = task.getBoundingClientRect();
            const afterTask = rect.bottom + 5;
            const distance = Math.abs(mouseY - afterTask);
            
            if (distance < minDistance) {
                minDistance = distance;
                closestY = afterTask;
            }
        });
        
        return closestY;
    }

    /**
     * Handle drop events
     */
    _handleDrop(event) {
        event.preventDefault();
        
        if (!this.draggedTask || this.insertionIndex === -1) {
            console.log('No valid drop target');
            return;
        }
        
        // Prevent multiple drops
        if (this.isDropping) {
            console.log('Drop already in progress, ignoring');
            return;
        }
        this.isDropping = true;
        
        console.log('DROP: Moving task', this.draggedTask.file_idx, 'to visual position', this.insertionIndex);
        
        // Calculate the new file index sequence
        const newFileIdxSequence = this._calculateReorderSequence();
        
        console.log('📝 REORDER: Complete new file index sequence:', newFileIdxSequence);
        
        // Emit reorder event
        const event_detail = {
            detail: { fileIdxSequence: newFileIdxSequence }
        };
        
        document.dispatchEvent(new CustomEvent('task:reorder', event_detail));
        
        this.isDropping = false;
    }

    /**
     * Calculate the new file index sequence after reordering
     */
    _calculateReorderSequence() {
        // Get all visible tasks in current order (including dragged one)
        const allVisibleTasks = Array.from(document.querySelectorAll('.task-item'));
        
        // Extract the file indices in their current visual positions
        const fileIndices = allVisibleTasks.map(task => parseInt(task.dataset.fileIdx));
        
        // Find dragged task position
        const draggedVisualPos = allVisibleTasks.findIndex(
            item => parseInt(item.dataset.fileIdx) === this.draggedTask.file_idx
        );
        
        // Get the file index of the task being dragged
        const draggedTaskFileIdx = this.draggedTask.file_idx;
        
        // Create a new array without the dragged task
        const reorderedFileIndices = [...fileIndices];
        reorderedFileIndices.splice(draggedVisualPos, 1);  // Remove dragged task
        reorderedFileIndices.splice(this.insertionIndex, 0, draggedTaskFileIdx);  // Insert at new position
        
        console.log('Simple reorder: moving visual index', draggedVisualPos, '→', this.insertionIndex);
        console.log('  Original file indices:', fileIndices);
        console.log('  Dragged task file index:', draggedTaskFileIdx);
        console.log('  New file index sequence:', reorderedFileIndices);
        
        return reorderedFileIndices;
    }

    /**
     * Clean up drag state
     */
    _cleanupDragState() {
        // Remove dragging state from tasks
        document.querySelectorAll('.task-item').forEach(item => {
            item.classList.remove('selected-for-move');
        });
        
        // Remove insertion line
        const insertionLine = document.querySelector('.insertion-line');
        if (insertionLine) {
            insertionLine.remove();
        }
        
        // Remove event listeners
        if (this.taskListContainer) {
            const contentArea = document.querySelector('.content-body') || this.taskListContainer;
            if (this.dragOverHandler) {
                contentArea.removeEventListener('dragover', this.dragOverHandler);
            }
            if (this.dropHandler) {
                contentArea.removeEventListener('drop', this.dropHandler);
            }
        }
        
        // Clear drag data
        this.draggedTask = null;
        this.taskListContainer = null;
        this.insertionIndex = -1;
        this.lastMouseY = 0;
        this.isDropping = false;
        this.dragOverHandler = null;
        this.dropHandler = null;
    }

    /**
     * Get task data from DOM element
     */
    _getTaskDataFromElement(element) {
        return {
            file_idx: parseInt(element.dataset.fileIdx),
            title: element.querySelector('.task-title')?.textContent || '',
            id: element.dataset.taskId,
            status: element.dataset.status,
            order: parseInt(element.dataset.order)
        };
    }

    /**
     * Clear any existing drag states
     */
    clearDragState() {
        this._cleanupDragState();
    }
}

export default DragDropManager;
