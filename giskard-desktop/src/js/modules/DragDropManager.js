/**
 * DragDropManager - Handles drag and drop reordering of tasks
 */
class DragDropManager {
    constructor() {
        // Debug flag - set to true only when debugging drag issues
        this.DEBUG = false;
        
        // Core drag state
        this.draggedTask = null;
        this.insertionIndex = -1;
        this.lastMouseY = 0;
        this.isDropping = false;
        this.isDragging = false;
        
        // Event handlers (stored for proper cleanup)
        this.dragOverHandler = null;
        this.dropHandler = null;
        this.mouseMoveHandler = null;
        this.mouseUpHandler = null;
        
        // Performance and reliability
        this.lastReorderTime = 0;
        this.reorderDebounceMs = 500;
        this.mouseMoveThrottle = null;
        this.throttleDelay = 16; // ~60fps
    }

    /**
     * Initialize drag and drop for all task items
     */
    initializeDragDrop() {
        if (this.DEBUG) console.log('🔧 DragDropManager.initializeDragDrop() called');
        
        // Clean up existing event listeners first
        this.cleanup();
        
        const taskItems = document.querySelectorAll('.task-item');
        if (this.DEBUG) console.log(`📝 Found ${taskItems.length} task items to initialize`);
        
        taskItems.forEach((taskItem, index) => {
            if (this.DEBUG) console.log(`⚙️  Initializing drag for task ${index + 1}:`, taskItem.dataset);
            this.addDragHandlers(taskItem);
        });
        
        if (this.DEBUG) console.log('🎯 DragDropManager initialization complete');
    }
    
    /**
     * Clean up existing event listeners
     */
    cleanup() {
        if (this.DEBUG) console.log('🧹 Cleaning up existing drag-drop listeners');
        
        // Remove document-level mouse event listeners
        if (this.mouseMoveHandler) {
            document.removeEventListener('mousemove', this.mouseMoveHandler);
            this.mouseMoveHandler = null;
        }
        if (this.mouseUpHandler) {
            document.removeEventListener('mouseup', this.mouseUpHandler);
            this.mouseUpHandler = null;
        }
        
        // Remove dragover and drop listeners from single container
        const container = document.querySelector('.content-body') || document.body;
        if (container && this.dragOverHandler) {
            container.removeEventListener('dragover', this.dragOverHandler);
        }
        if (container && this.dropHandler) {
            container.removeEventListener('drop', this.dropHandler);
        }
        
        // Clear insertion line
        const insertionLine = document.querySelector('.insertion-line');
        if (insertionLine) {
            insertionLine.remove();
        }
        
        // Reset state
        this.draggedTask = null;
        this.insertionIndex = -1;
        this.isDropping = false;
        this.isDragging = false;
        this.lastMouseY = 0;
        this.dragOverHandler = null;
        this.dropHandler = null;
        
        // Clear throttling
        if (this.mouseMoveThrottle) {
            clearTimeout(this.mouseMoveThrottle);
            this.mouseMoveThrottle = null;
        }
    }

    /**
     * Add drag handlers to a single task item - Simplified implementation
     */
    addDragHandlers(taskItem) {
        const dragHandle = taskItem.querySelector('.task-drag-handle');
        
        if (!dragHandle) {
            if (this.DEBUG) console.warn('⚠️  No drag handle found for task:', taskItem.dataset?.taskId);
            return;
        }

        if (this.DEBUG) console.log('✅ Adding drag handlers to task:', taskItem.dataset?.taskId);

        // Store drag start data
        let dragStartY = 0;
        let dragThreshold = 5; // pixels to move before starting drag
        
        // Mouse down - start tracking
        dragHandle.addEventListener('mousedown', (e) => {
            if (this.DEBUG) console.log('🖱️ Drag handle mousedown');
            e.preventDefault(); // Prevent text selection
            
            dragStartY = e.clientY;
            this.isDragging = false;
            
            // Create throttled mouse move handler
            this.mouseMoveHandler = (moveEvent) => {
                const deltaY = Math.abs(moveEvent.clientY - dragStartY);
                
                if (!this.isDragging && deltaY > dragThreshold) {
                    // Start dragging
                    this.isDragging = true;
                    if (this.DEBUG) console.log('🎯 DRAG START:', taskItem.dataset?.taskId);
                    this._handleDragStart(moveEvent, taskItem);
                }
                
                if (this.isDragging) {
                    // Throttle mousemove events for performance
                    if (this.mouseMoveThrottle) {
                        clearTimeout(this.mouseMoveThrottle);
                    }
                    this.mouseMoveThrottle = setTimeout(() => {
                        this._handleDragMove(moveEvent);
                    }, this.throttleDelay);
                }
            };
            
            // Create mouse up handler
            this.mouseUpHandler = (upEvent) => {
                if (this.DEBUG) console.log('🔚 DRAG END:', {isDragging: this.isDragging, taskId: taskItem.dataset?.taskId});
                
                if (this.isDragging) {
                    this._handleDragEnd(upEvent, taskItem);
                }
                
                // Clean up document listeners
                document.removeEventListener('mousemove', this.mouseMoveHandler);
                document.removeEventListener('mouseup', this.mouseUpHandler);
                this.mouseMoveHandler = null;
                this.mouseUpHandler = null;
                this.isDragging = false;
            };
            
            // Add document listeners
            document.addEventListener('mousemove', this.mouseMoveHandler);
            document.addEventListener('mouseup', this.mouseUpHandler);
        });
        
        // Prevent context menu on drag handle
        dragHandle.addEventListener('contextmenu', (e) => {
            e.preventDefault();
        });
    }

    /**
     * Handle drag start
     */
    _handleDragStart(event, taskItem) {
        const fileIdxStr = taskItem.dataset.fileIdx;
        const fileIdx = fileIdxStr && fileIdxStr !== '' ? parseInt(fileIdxStr) : null;
        const taskTitle = taskItem.querySelector('.task-title')?.textContent || 'Unknown';
        
        if (fileIdx === null || isNaN(fileIdx)) {
            if (this.DEBUG) console.error(`❌ Invalid fileIdx for task: "${taskTitle}" - fileIdx: "${fileIdxStr}"`);
            return;
        }
        
        if (this.DEBUG) console.log(`🎯 DRAG START: "${taskTitle}" - file_idx: ${fileIdx}`);
        
        // Visual feedback
        document.body.classList.add('dragging');
        taskItem.classList.add('selected-for-move');
        
        // Store drag state
        this.draggedTask = {
            file_idx: fileIdx,
            title: taskTitle,
            element: taskItem
        };
        
        // Initialize insertion tracking
        this._initializeInsertionTracking();
        
        // Initial position update
        this.lastMouseY = event.clientY;
        this._updateInsertionLinePosition();
    }

    /**
     * Handle drag move
     */
    _handleDragMove(event) {
        if (!this.isDragging || !this.draggedTask) return;
        
        // Update mouse position and insertion line
        this.lastMouseY = event.clientY;
        
        // Calculate insertion index
        const insertionIndex = this._calculateInsertionIndex(event.clientY);
        this.insertionIndex = insertionIndex;
        
        if (this.DEBUG) console.log('📍 DRAG MOVE: Y:', event.clientY, 'Index:', insertionIndex);
        
        // Update insertion line position
        this._updateInsertionLinePosition();
    }

    /**
     * Handle drag end
     */
    _handleDragEnd(event, taskItem) {
        if (this.DEBUG) console.log(`🔚 DRAG END: ${this.draggedTask?.file_idx} at index ${this.insertionIndex}`);
        
        // Handle drop if valid
        if (this.isDragging && this.insertionIndex !== -1 && this.draggedTask && !this.isDropping) {
            if (this.DEBUG) console.log('✅ DROP: Performing reorder');
            this._handleDrop(event);
        }
        
        // Clean up drag state
        this._cleanupDragState();
    }

    /**
     * Initialize insertion line tracking
     */
    _initializeInsertionTracking() {
        if (this.DEBUG) console.log('Initializing insertion tracking...');
        
        // Find the actual tasks container
        const firstTask = document.querySelector('.task-item');
        if (!firstTask) {
            if (this.DEBUG) console.error('No tasks found to determine container');
            return;
        }
        
        this.taskListContainer = firstTask.parentElement;
        if (this.DEBUG) console.log('Task container found:', this.taskListContainer.className);
        
        // Create insertion line
        this._createInsertionLine();
        
        // Use single container for better reliability
        const container = document.querySelector('.content-body') || document.body;
        
        if (this.DEBUG) console.log('🎯 Adding listeners to container:', container.className);
        
        this.dragOverHandler = (e) => {
            if (this.DEBUG) console.log('🎯 DRAGOVER EVENT FIRED on:', e.target.className);
            this._handleDragOver(e);
        };
        this.dropHandler = (e) => this._handleDrop(e);
        
        // Add to single container
        container.addEventListener('dragover', this.dragOverHandler);
        container.addEventListener('drop', this.dropHandler);
        
        if (this.DEBUG) console.log('✅ Insertion tracking initialized');
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
        
        // Create new insertion line with clean styling
        const insertionLine = document.createElement('div');
        insertionLine.className = 'insertion-line';
        insertionLine.style.top = '-10px'; // Start hidden above viewport
        
        // Add to document body for fixed positioning
        document.body.appendChild(insertionLine);
        
        if (this.DEBUG) console.log('✅ Created clean insertion line');
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
        
        if (this.DEBUG) console.log('🖱️ DRAGOVER: Mouse Y:', event.clientY);
        
        // Calculate insertion index for drop logic
        const insertionIndex = this._calculateInsertionIndex(event.clientY);
        this.insertionIndex = insertionIndex;
        
        if (this.DEBUG) console.log('📍 Calculated insertion index:', insertionIndex);
        
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
        if (!insertionLine || !this.lastMouseY) {
            if (this.DEBUG) console.log('⚠️ Cannot update line - missing line or mouseY:', {
                hasLine: !!insertionLine,
                mouseY: this.lastMouseY
            });
            return;
        }
        
        // Find the closest task boundary for snapping
        const snappedY = this._findClosestTaskBoundary(this.lastMouseY);
        
        // Use the snapped position
        const oldTop = insertionLine.style.top;
        insertionLine.style.top = `${snappedY}px`;
        
        if (this.DEBUG) console.log(`📍 LINE MOVED: ${oldTop} → ${snappedY}px (mouse: ${this.lastMouseY})`);
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
            if (this.DEBUG) console.log('No valid drop target');
            return;
        }
        
        // Prevent multiple drops
        if (this.isDropping) {
            if (this.DEBUG) console.log('Drop already in progress, ignoring');
            return;
        }
        
        // Debounce rapid reorders
        const now = Date.now();
        if (now - this.lastReorderTime < this.reorderDebounceMs) {
            if (this.DEBUG) console.log('Reorder debounced, too soon since last reorder');
            return;
        }
        this.lastReorderTime = now;
        
        this.isDropping = true;
        
        if (this.DEBUG) console.log('DROP: Moving task', this.draggedTask.file_idx, 'to visual position', this.insertionIndex);
        
        // Calculate the new file index sequence
        const newFileIdxSequence = this._calculateReorderSequence();
        
        // Check if the order actually changed
        const allVisibleTasks = Array.from(document.querySelectorAll('.task-item'));
        const currentFileIndices = allVisibleTasks.map(task => parseInt(task.dataset.fileIdx));
        
        if (JSON.stringify(currentFileIndices) === JSON.stringify(newFileIdxSequence)) {
            if (this.DEBUG) console.log('No change in order, skipping reorder');
            this.isDropping = false;
            return;
        }
        
        if (this.DEBUG) console.log('📝 REORDER: Complete new file index sequence:', newFileIdxSequence);
        
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
        
        // Extract the file indices in their current visual positions, filtering out invalid ones
        const fileIndices = allVisibleTasks
            .map(task => {
                const fileIdx = task.dataset.fileIdx;
                return fileIdx && fileIdx !== '' ? parseInt(fileIdx) : null;
            })
            .filter(fileIdx => fileIdx !== null);
        
        // Find dragged task position
        const draggedVisualPos = allVisibleTasks.findIndex(
            item => {
                const fileIdx = item.dataset.fileIdx;
                return fileIdx && fileIdx !== '' && parseInt(fileIdx) === this.draggedTask.file_idx;
            }
        );
        
        // Get the file index of the task being dragged
        const draggedTaskFileIdx = this.draggedTask.file_idx;
        
        // Create a new array without the dragged task
        const reorderedFileIndices = [...fileIndices];
        reorderedFileIndices.splice(draggedVisualPos, 1);  // Remove dragged task
        reorderedFileIndices.splice(this.insertionIndex, 0, draggedTaskFileIdx);  // Insert at new position
        
        if (this.DEBUG) {
            console.log('Simple reorder: moving visual index', draggedVisualPos, '→', this.insertionIndex);
            console.log('  Original file indices:', fileIndices);
            console.log('  Dragged task file index:', draggedTaskFileIdx);
            console.log('  New file index sequence:', reorderedFileIndices);
        }
        
        return reorderedFileIndices;
    }

    /**
     * Clean up drag state and visual feedback
     */
    _cleanupDragState() {
        // Remove visual classes
        document.body.classList.remove('dragging');
        document.querySelectorAll('.task-item').forEach(item => {
            item.classList.remove('selected-for-move');
        });
        
        // Remove insertion line
        const insertionLine = document.querySelector('.insertion-line');
        if (insertionLine) {
            insertionLine.remove();
        }
        
        // Reset state
        this.isDragging = false;
        this.draggedTask = null;
        this.insertionIndex = -1;
        this.lastMouseY = 0;
        this.isDropping = false;
        
        if (this.DEBUG) console.log('🧹 Drag state cleaned up');
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

    /**
     * Enable debug mode for troubleshooting
     */
    enableDebug() {
        this.DEBUG = true;
        console.log('🐛 DragDropManager debug mode enabled');
    }

    /**
     * Disable debug mode
     */
    disableDebug() {
        this.DEBUG = false;
        console.log('🐛 DragDropManager debug mode disabled');
    }
}

export default DragDropManager;
