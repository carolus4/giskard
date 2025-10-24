/**
 * DragEventHandlers - Manages all event handling for drag and drop
 * Encapsulates mousedown, mousemove, mouseup, dragover, and drop events
 */
class DragEventHandlers {
    constructor(state, visualFeedback, onDragEnd) {
        this.state = state;
        this.visual = visualFeedback;
        this.onDragEnd = onDragEnd; // Callback for handling drop/reorder

        // Event handler storage for cleanup
        this.taskEventHandlers = new Map();
        this.dragOverHandler = null;
        this.dropHandler = null;
    }

    /**
     * Add drag handlers to a single task item
     * @param {HTMLElement} taskItem - Task element
     * @returns {boolean} - True if handlers were successfully added
     */
    addTaskHandlers(taskItem) {
        // Validate task item
        if (!taskItem || !taskItem.isConnected) {
            if (this.state.DEBUG) {
                console.warn('⚠️  Task item is null or not connected to DOM');
            }
            return false;
        }

        const dragHandle = taskItem.querySelector('.task-drag-handle');

        if (!dragHandle) {
            if (this.state.DEBUG) {
                console.warn('⚠️  No drag handle found for task:', taskItem.dataset?.taskId);
            }
            return false;
        }

        // Check if handlers already exist for this task
        if (this.taskEventHandlers.has(taskItem)) {
            if (this.state.DEBUG) {
                console.warn('⚠️  Handlers already exist for task:', taskItem.dataset?.taskId);
            }
            return false;
        }

        if (this.state.DEBUG) {
            console.log('✅ Adding drag handlers to task:', taskItem.dataset?.taskId);
        }

        // Store drag start data for this specific drag handle
        let dragStartY = 0;
        let dragThreshold = 5; // pixels to move before starting drag
        let isDraggingThisItem = false;

        // Mouse down - start tracking for this specific item
        const mousedownHandler = (e) => {
            // Validate elements are still in DOM when event fires
            if (!taskItem.isConnected || !dragHandle.isConnected) {
                if (this.state.DEBUG) {
                    console.warn('⚠️  Element disconnected during mousedown');
                }
                return;
            }

            if (this.state.DEBUG) {
                console.log('🖱️ Drag handle mousedown for task:', taskItem.dataset?.taskId);
            }
            e.preventDefault(); // Prevent text selection

            // Don't start drag if already dragging another item
            if (this.state.isDragging) {
                if (this.state.DEBUG) {
                    console.log('⚠️ Already dragging another item, ignoring');
                }
                return;
            }

            dragStartY = e.clientY;
            isDraggingThisItem = false;

            // Create mouse move handler for this specific drag operation
            const mouseMoveHandler = (moveEvent) => {
                // Validate elements still exist
                if (!taskItem.isConnected) {
                    if (this.state.DEBUG) {
                        console.warn('⚠️  Task disconnected during drag move');
                    }
                    document.removeEventListener('mousemove', mouseMoveHandler);
                    document.removeEventListener('mouseup', mouseUpHandler);
                    this.state.isDragging = false;
                    isDraggingThisItem = false;
                    return;
                }

                const deltaY = Math.abs(moveEvent.clientY - dragStartY);

                if (!isDraggingThisItem && deltaY > dragThreshold) {
                    // Start dragging this specific item
                    isDraggingThisItem = true;
                    if (this.state.DEBUG) {
                        console.log('🎯 DRAG START:', taskItem.dataset?.taskId);
                    }
                    this._handleDragStart(moveEvent, taskItem);
                }

                if (isDraggingThisItem && this.state.isDragging) {
                    // Throttle mousemove events for performance
                    if (this.state.mouseMoveThrottle) {
                        clearTimeout(this.state.mouseMoveThrottle);
                    }
                    const throttleId = setTimeout(() => {
                        // Guard: Don't execute if cleanup already happened
                        if (!this.state.isCleanedUp && taskItem.isConnected) {
                            this._handleDragMove(moveEvent);
                        }
                    }, this.state.throttleDelay);
                    this.state.setThrottle(throttleId);
                }
            };

            // Create mouse up handler for this specific drag operation
            const mouseUpHandler = (upEvent) => {
                if (this.state.DEBUG) {
                    console.log('🔚 DRAG END:', {
                        isDragging: this.state.isDragging,
                        taskId: taskItem.dataset?.taskId
                    });
                }

                if (isDraggingThisItem && this.state.isDragging) {
                    this._handleDragEnd(upEvent);
                }

                // Clean up document listeners for this drag operation
                document.removeEventListener('mousemove', mouseMoveHandler);
                document.removeEventListener('mouseup', mouseUpHandler);
                isDraggingThisItem = false;
                this.state.isDragging = false;
            };

            // Add document listeners for this drag operation with options
            document.addEventListener('mousemove', mouseMoveHandler, { passive: true });
            document.addEventListener('mouseup', mouseUpHandler, { once: true });
        };

        // Prevent context menu on drag handle
        const contextmenuHandler = (e) => {
            e.preventDefault();
        };

        try {
            dragHandle.addEventListener('mousedown', mousedownHandler);
            dragHandle.addEventListener('contextmenu', contextmenuHandler);

            // Track handlers for cleanup
            this.taskEventHandlers.set(taskItem, {
                mousedown: mousedownHandler,
                contextmenu: contextmenuHandler,
                dragHandle: dragHandle  // Store reference for validation
            });

            return true;
        } catch (error) {
            if (this.state.DEBUG) {
                console.error('❌ Failed to add event listeners:', error);
            }
            return false;
        }
    }

    /**
     * Handle drag start
     * @param {MouseEvent} event
     * @param {HTMLElement} taskItem
     * @private
     */
    _handleDragStart(event, taskItem) {
        // Validate element is still in DOM
        if (!taskItem.isConnected) {
            if (this.state.DEBUG) {
                console.error('❌ Task element no longer in DOM');
            }
            return;
        }

        const taskData = this.visual.getTaskDataFromElement(taskItem);
        if (!taskData) {
            return;
        }

        if (this.state.DEBUG) {
            console.log(`🎯 DRAG START: "${taskData.title}" - taskId: ${taskData.id}`);
        }

        // Visual feedback
        this.visual.applyDragStartVisuals(taskItem);

        // Store drag state
        this.state.setDraggedTask(taskData);

        // Initialize insertion tracking
        this.visual.initializeInsertionTracking();

        // Initial position update
        this.state.setMouseY(event.clientY);
        this.visual.updateInsertionLinePosition(event.clientY);
    }

    /**
     * Handle drag move
     * @param {MouseEvent} event
     * @private
     */
    _handleDragMove(event) {
        if (!this.state.isDragging || !this.state.draggedTask) return;

        // Validate dragged element is still in DOM
        if (!this.state.draggedTask.element?.isConnected) {
            if (this.state.DEBUG) {
                console.error('❌ Dragged element no longer in DOM, aborting drag');
            }
            this._cleanupDragState();
            return;
        }

        // Update mouse position
        this.state.setMouseY(event.clientY);

        // Import calculation function
        const DragCalculations = window.DragCalculations ||
            (typeof require !== 'undefined' ? require('./DragCalculations.js').default : null);

        if (DragCalculations) {
            // Calculate insertion index
            const insertionIndex = DragCalculations.calculateInsertionIndex(event.clientY);
            this.state.setInsertionIndex(insertionIndex);

            if (this.state.DEBUG) {
                console.log('📍 DRAG MOVE: Y:', event.clientY, 'Index:', insertionIndex);
            }
        }

        // Update insertion line position
        this.visual.updateInsertionLinePosition(event.clientY);
    }

    /**
     * Handle drag end
     * @param {MouseEvent} event
     * @private
     */
    _handleDragEnd(event) {
        if (this.state.DEBUG) {
            console.log(`🔚 DRAG END: ${this.state.draggedTask?.id} at index ${this.state.insertionIndex}`);
        }

        // Validate dragged element is still in DOM before proceeding
        const isValidDrop = this.state.isDragging &&
                           this.state.insertionIndex !== -1 &&
                           this.state.draggedTask &&
                           !this.state.isDropping &&
                           this.state.draggedTask.element?.isConnected;

        // Handle drop if valid
        if (isValidDrop) {
            if (this.state.DEBUG) {
                console.log('✅ DROP: Performing reorder');
            }
            this._handleDrop(event);
        } else if (this.state.draggedTask && !this.state.draggedTask.element?.isConnected) {
            if (this.state.DEBUG) {
                console.warn('⚠️ DROP: Dragged element removed from DOM, skipping reorder');
            }
        }

        // Clean up drag state
        this._cleanupDragState();
    }

    /**
     * Handle drop event
     * @param {Event} event
     * @private
     */
    _handleDrop(event) {
        event.preventDefault();

        if (!this.state.draggedTask || this.state.insertionIndex === -1) {
            if (this.state.DEBUG) {
                console.log('No valid drop target');
            }
            return;
        }

        // Prevent multiple drops
        if (this.state.isDropping) {
            if (this.state.DEBUG) {
                console.log('Drop already in progress, ignoring');
            }
            return;
        }

        // Debounce rapid reorders
        if (this.state.shouldDebounceReorder()) {
            if (this.state.DEBUG) {
                console.log('Reorder debounced, too soon since last reorder');
            }
            return;
        }
        this.state.updateReorderTime();

        this.state.isDropping = true;

        if (this.state.DEBUG) {
            console.log('DROP: Moving task', this.state.draggedTask.id, 'to visual position', this.state.insertionIndex);
        }

        // Import calculation function
        const DragCalculations = window.DragCalculations ||
            (typeof require !== 'undefined' ? require('./DragCalculations.js').default : null);

        if (!DragCalculations) {
            console.error('DragCalculations not available');
            this.state.isDropping = false;
            return;
        }

        // Calculate the new task ID sequence
        const newTaskIdSequence = DragCalculations.calculateReorderSequence(
            this.state.draggedTask.id,
            this.state.insertionIndex
        );

        // Check if the order actually changed
        if (!DragCalculations.hasOrderChanged(newTaskIdSequence)) {
            if (this.state.DEBUG) {
                console.log('No change in order, skipping reorder');
            }
            this.state.isDropping = false;
            return;
        }

        if (this.state.DEBUG) {
            console.log('📝 REORDER: Complete new task ID sequence:', newTaskIdSequence);
        }

        // Call the callback to handle the reorder
        if (this.onDragEnd) {
            this.onDragEnd(newTaskIdSequence);
        }

        this.state.isDropping = false;
    }

    /**
     * Clean up drag state and visual feedback
     * @private
     */
    _cleanupDragState() {
        this.visual.removeAllVisuals();
        this.state.clearDraggedTask();

        if (this.state.DEBUG) {
            console.log('🧹 Drag state cleaned up');
        }
    }

    /**
     * Remove all event handlers
     */
    cleanup() {
        if (this.state.DEBUG) {
            console.log('🧹 Cleaning up event handlers');
        }

        // Set guard flag to prevent throttled callbacks from executing
        this.state.setCleanedUp(true);

        // Remove all tracked mousedown handlers
        this.taskEventHandlers.forEach((handlers, taskElement) => {
            const dragHandle = handlers.dragHandle || taskElement.querySelector('.task-drag-handle');
            if (dragHandle && handlers.mousedown) {
                try {
                    dragHandle.removeEventListener('mousedown', handlers.mousedown);
                } catch (error) {
                    if (this.state.DEBUG) {
                        console.warn('⚠️ Failed to remove mousedown listener:', error);
                    }
                }
            }
            if (dragHandle && handlers.contextmenu) {
                try {
                    dragHandle.removeEventListener('contextmenu', handlers.contextmenu);
                } catch (error) {
                    if (this.state.DEBUG) {
                        console.warn('⚠️ Failed to remove contextmenu listener:', error);
                    }
                }
            }
        });
        this.taskEventHandlers.clear();

        // Reset state
        this.state.reset();
        this.dragOverHandler = null;
        this.dropHandler = null;

        // Reset cleanup flag
        this.state.setCleanedUp(false);
    }
}

export default DragEventHandlers;
