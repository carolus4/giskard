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
        this.lastReorderTime = 0;
        this.reorderDebounceMs = 500; // Prevent rapid reorders
    }

    /**
     * Initialize drag and drop for all task items
     */
    initializeDragDrop() {
        console.log('🔧 DragDropManager.initializeDragDrop() called');
        
        // Clean up existing event listeners first
        this.cleanup();
        
        const taskItems = document.querySelectorAll('.task-item');
        console.log(`📝 Found ${taskItems.length} task items to initialize`);
        
        taskItems.forEach((taskItem, index) => {
            console.log(`⚙️  Initializing drag for task ${index + 1}:`, taskItem.dataset);
            this.addDragHandlers(taskItem);
        });
        
        console.log('🎯 DragDropManager initialization complete');
    }
    
    /**
     * Clean up existing event listeners
     */
    cleanup() {
        console.log('🧹 Cleaning up existing drag-drop listeners');
        
        // Remove existing dragover and drop listeners
        if (this.dragOverHandler && this.dropHandler) {
            const elements = [
                document.querySelector('.content-body'),
                document.querySelector('.task-list'),
                document.querySelector('.view-container'),
                document.body
            ];
            
            elements.forEach(element => {
                if (element) {
                    element.removeEventListener('dragover', this.dragOverHandler);
                    element.removeEventListener('drop', this.dropHandler);
                }
            });
        }
        
        // Reset state
        this.draggedTask = null;
        this.insertionIndex = -1;
        this.isDropping = false;
        this.isDragging = false;
        this.dragOverHandler = null;
        this.dropHandler = null;
    }

    /**
     * Add drag handlers to a single task item - CUSTOM IMPLEMENTATION FOR TAURI
     */
    addDragHandlers(taskItem) {
        const dragHandle = taskItem.querySelector('.task-drag-handle');
        
        if (!dragHandle) {
            console.warn('⚠️  No drag handle found for task:', taskItem.dataset?.taskId);
            return;
        }

        console.log('✅ Adding CUSTOM drag to task:', taskItem.dataset?.taskId);

        // CUSTOM DRAG IMPLEMENTATION (not HTML5 drag-drop) for Tauri compatibility
        let isDragging = false;
        let dragStartY = 0;
        let dragThreshold = 5; // pixels to move before starting drag
        
        // Mouse down - start tracking
        dragHandle.addEventListener('mousedown', (e) => {
            console.log('🖱️ CUSTOM: Drag handle mousedown');
            e.preventDefault(); // Prevent text selection
            isDragging = false;
            dragStartY = e.clientY;
            
            // Add document listeners for drag tracking
            const handleMouseMove = (moveEvent) => {
                const deltaY = Math.abs(moveEvent.clientY - dragStartY);
                
                if (!isDragging && deltaY > dragThreshold) {
                    // Start dragging
                    isDragging = true;
                    console.log('🎯 CUSTOM DRAG START:', taskItem.dataset?.taskId);
                    this._customDragStart(moveEvent, taskItem);
                }
                
                if (isDragging) {
                    console.log('🖱️ CUSTOM DRAGMOVE:', moveEvent.clientY);
                    this._customDragMove(moveEvent);
                }
            };
            
            const handleMouseUp = (upEvent) => {
                console.log('🔚 CUSTOM DRAG END:', {isDragging, taskId: taskItem.dataset?.taskId});
                
                if (isDragging) {
                    this._customDragEnd(upEvent, taskItem);
                }
                
                // Clean up
                document.removeEventListener('mousemove', handleMouseMove);
                document.removeEventListener('mouseup', handleMouseUp);
                isDragging = false;
            };
            
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
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
        const task = this._getTaskDataFromElement(taskItem);
        
        console.log('🎯 DRAG START: Dragging task:', task.title, 'file_idx:', task.file_idx);
        
        // Add dragging state
        document.body.classList.add('dragging');
        taskItem.classList.add('selected-for-move');
        console.log('✅ Added dragging class to body');
        
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
        console.log('🔚 Drag ended', {
            insertionIndex: this.insertionIndex,
            draggedTask: this.draggedTask?.file_idx,
            isDropping: this.isDropping,
            target: event.target?.tagName
        });
        
        // If we have a valid insertion point and aren't already dropping, trigger drop
        if (this.insertionIndex !== -1 && this.draggedTask && !this.isDropping) {
            console.log('⚡ Triggering drop from dragend');
            this._handleDrop();
        }
        
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
        
        // Add event listeners to MULTIPLE containers to ensure dragover fires
        const contentArea = document.querySelector('.content-body') || this.taskListContainer;
        const taskList = document.querySelector('.task-list');
        const viewContainer = document.querySelector('.view-container');
        
        console.log('🎯 Adding dragover listeners to multiple elements:', {
            contentArea: contentArea?.className,
            taskList: taskList?.className, 
            viewContainer: viewContainer?.className
        });
        
        this.dragOverHandler = (e) => {
            console.log('🎯 DRAGOVER EVENT FIRED on:', e.target.className);
            this._handleDragOver(e);
        };
        this.dropHandler = (e) => this._handleDrop(e);
        
        // Add to ALL possible containers
        [contentArea, taskList, viewContainer, document.body].forEach(element => {
            if (element) {
                console.log('✅ Adding dragover to:', element.tagName, element.className);
                element.addEventListener('dragover', this.dragOverHandler);
                element.addEventListener('drop', this.dropHandler);
            }
        });
        
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
        
        // Create new insertion line with clean styling
        const insertionLine = document.createElement('div');
        insertionLine.className = 'insertion-line';
        insertionLine.style.top = '-10px'; // Start hidden above viewport
        
        // Add to document body for fixed positioning
        document.body.appendChild(insertionLine);
        
        console.log('✅ Created clean insertion line');
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
        
        console.log('🖱️ DRAGOVER: Mouse Y:', event.clientY);
        
        // Calculate insertion index for drop logic
        const insertionIndex = this._calculateInsertionIndex(event.clientY);
        this.insertionIndex = insertionIndex;
        
        console.log('📍 Calculated insertion index:', insertionIndex);
        
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
            console.log('⚠️ Cannot update line - missing line or mouseY:', {
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
        
        console.log(`📍 LINE MOVED: ${oldTop} → ${snappedY}px (mouse: ${this.lastMouseY})`);
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
        
        // Debounce rapid reorders
        const now = Date.now();
        if (now - this.lastReorderTime < this.reorderDebounceMs) {
            console.log('Reorder debounced, too soon since last reorder');
            return;
        }
        this.lastReorderTime = now;
        
        this.isDropping = true;
        
        console.log('DROP: Moving task', this.draggedTask.file_idx, 'to visual position', this.insertionIndex);
        
        // Calculate the new file index sequence
        const newFileIdxSequence = this._calculateReorderSequence();
        
        // Check if the order actually changed
        const allVisibleTasks = Array.from(document.querySelectorAll('.task-item'));
        const currentFileIndices = allVisibleTasks.map(task => parseInt(task.dataset.fileIdx));
        
        if (JSON.stringify(currentFileIndices) === JSON.stringify(newFileIdxSequence)) {
            console.log('No change in order, skipping reorder');
            this.isDropping = false;
            return;
        }
        
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
        
        console.log('Simple reorder: moving visual index', draggedVisualPos, '→', this.insertionIndex);
        console.log('  Original file indices:', fileIndices);
        console.log('  Dragged task file index:', draggedTaskFileIdx);
        console.log('  New file index sequence:', reorderedFileIndices);
        
        return reorderedFileIndices;
    }

    /**
     * CUSTOM drag start handler for Tauri compatibility
     */
    _customDragStart(event, taskItem) {
        const fileIdxStr = taskItem.dataset.fileIdx;
        const fileIdx = fileIdxStr && fileIdxStr !== '' ? parseInt(fileIdxStr) : null;
        const taskTitle = taskItem.querySelector('.task-title')?.textContent || 'Unknown';
        
        if (fileIdx === null || isNaN(fileIdx)) {
            console.error(`❌ Invalid fileIdx for task: "${taskTitle}" - fileIdx: "${fileIdxStr}"`);
            return;
        }
        
        console.log(`🎯 CUSTOM DRAG START: "${taskTitle}" - file_idx: ${fileIdx}`);
        
        // Visual feedback
        document.body.classList.add('dragging');
        taskItem.classList.add('selected-for-move');
        console.log('✅ Added dragging class to body');
        
        // Store drag state
        this.draggedTask = {
            file_idx: fileIdx,
            title: taskTitle,
            element: taskItem
        };
        this.isDragging = true;
        this.draggedElement = taskItem;
        
        // Initialize insertion tracking
        this._initializeInsertionTracking();
        
        // Initial position update
        this.lastMouseY = event.clientY;
        this._updateInsertionLinePosition();
    }
    
    /**
     * CUSTOM drag move handler for Tauri compatibility
     */
    _customDragMove(event) {
        if (!this.isDragging || !this.draggedTask) return;
        
        // Update mouse position and insertion line
        this.lastMouseY = event.clientY;
        
        // Calculate insertion index
        const insertionIndex = this._calculateInsertionIndex(event.clientY);
        this.insertionIndex = insertionIndex;
        
        console.log('📍 CUSTOM DRAG MOVE: Y:', event.clientY, 'Index:', insertionIndex);
        
        // Update insertion line position
        this._updateInsertionLinePosition();
    }
    
    /**
     * CUSTOM drag end handler for Tauri compatibility
     */
    _customDragEnd(event, taskItem) {
        console.log(`🔚 CUSTOM DRAG END: ${this.draggedTask?.file_idx} at index ${this.insertionIndex}`);
        
        // Handle drop if valid
        if (this.isDragging && this.insertionIndex !== -1 && this.draggedTask && !this.isDropping) {
            console.log('✅ CUSTOM DROP: Performing reorder');
            this._handleDrop(event);
        }
        
        // Clean up drag state
        this._cleanupCustomDragState();
    }
    
    /**
     * Clean up custom drag state and visual feedback
     */
    _cleanupCustomDragState() {
        // Remove visual classes
        document.body.classList.remove('dragging');
        if (this.draggedElement) {
            this.draggedElement.classList.remove('selected-for-move');
        }
        
        // Remove insertion line
        const insertionLine = document.querySelector('.insertion-line');
        if (insertionLine) {
            insertionLine.remove();
        }
        
        // Reset state
        this.isDragging = false;
        this.draggedTask = null;
        this.draggedElement = null;
        this.insertionIndex = -1;
        this.lastMouseY = null;
        
        console.log('🧹 Custom drag state cleaned up');
    }
    
    /**
     * Clean up drag state (original HTML5 method - kept for compatibility)
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
