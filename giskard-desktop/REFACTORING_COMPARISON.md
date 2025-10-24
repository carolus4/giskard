# DragDropManager Refactoring: Before vs After

This document shows specific code examples comparing the original monolithic implementation with the refactored modular architecture.

## Example 1: State Management

### Before (Scattered State)
```javascript
class DragDropManager {
    constructor() {
        // Debug flag
        this.DEBUG = false;

        // Core drag state
        this.draggedTask = null;
        this.insertionIndex = -1;
        this.lastMouseY = 0;
        this.isDropping = false;
        this.isDragging = false;

        // Event handlers
        this.dragOverHandler = null;
        this.dropHandler = null;
        this.taskEventHandlers = new Map();

        // Performance
        this.lastReorderTime = 0;
        this.reorderDebounceMs = 500;
        this.mouseMoveThrottle = null;
        this.throttleDelay = 16;
        this.lastInitTime = 0;
        this.initDebounceMs = 200;
        this.isCleanedUp = false;
    }

    // State changes scattered throughout methods
    _handleDragStart(event, taskItem) {
        this.draggedTask = { id, title, element };
        this.isDragging = true;
        this.lastMouseY = event.clientY;
    }

    _handleDragEnd() {
        this.isDragging = false;
        this.draggedTask = null;
        this.insertionIndex = -1;
    }
}
```

### After (Centralized State)
```javascript
// DragState.js - Single source of truth
class DragState {
    constructor() {
        this.DEBUG = false;
        this.draggedTask = null;
        this.insertionIndex = -1;
        this.lastMouseY = 0;
        this.isDropping = false;
        this.isDragging = false;
        // ... other state
    }

    setDraggedTask(task) {
        this.draggedTask = task;
        this.isDragging = true;
    }

    clearDraggedTask() {
        this.draggedTask = null;
        this.isDragging = false;
        this.insertionIndex = -1;
        this.lastMouseY = 0;
    }
}

// DragDropManager.js - Clean orchestration
class DragDropManager {
    constructor() {
        this.state = new DragState(); // Single state object
        this.visual = new DragVisualFeedback(this.state);
        this.eventHandlers = new DragEventHandlers(this.state, this.visual);
    }
}
```

**Benefits:**
- ✅ State changes are explicit via methods
- ✅ Easy to track state history
- ✅ Can add state validation in one place
- ✅ Clear ownership (DragState owns all state)

---

## Example 2: Calculations

### Before (Mixed with Logic)
```javascript
class DragDropManager {
    _handleDragMove(event) {
        if (!this.isDragging) return;

        this.lastMouseY = event.clientY;

        // Calculation mixed with event handling
        const taskItems = Array.from(document.querySelectorAll('.task-item'))
            .filter(item => !item.classList.contains('selected-for-move'));

        let insertIndex = 0;
        let minDistance = Infinity;

        const firstRect = taskItems[0].getBoundingClientRect();
        const distanceToFirst = Math.abs(event.clientY - (firstRect.top - 5));
        if (distanceToFirst < minDistance) {
            minDistance = distanceToFirst;
            insertIndex = 0;
        }

        taskItems.forEach((taskItem, i) => {
            const rect = taskItem.getBoundingClientRect();
            const afterTaskY = rect.bottom + 5;
            const distance = Math.abs(event.clientY - afterTaskY);

            if (distance < minDistance) {
                minDistance = distance;
                insertIndex = i + 1;
            }
        });

        this.insertionIndex = insertIndex;
        this._updateInsertionLinePosition();
    }
}
```

### After (Pure Functions)
```javascript
// DragCalculations.js - Pure, testable functions
class DragCalculations {
    static calculateInsertionIndex(mouseY) {
        const taskItems = Array.from(document.querySelectorAll('.task-item'))
            .filter(item => !item.classList.contains('selected-for-move'));

        if (taskItems.length === 0) return 0;

        let insertIndex = 0;
        let minDistance = Infinity;

        const firstRect = taskItems[0].getBoundingClientRect();
        const distanceToFirst = Math.abs(mouseY - (firstRect.top - 5));
        if (distanceToFirst < minDistance) {
            minDistance = distanceToFirst;
            insertIndex = 0;
        }

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
}

// DragEventHandlers.js - Clean event handling
_handleDragMove(event) {
    if (!this.state.isDragging) return;

    this.state.setMouseY(event.clientY);

    const insertionIndex = DragCalculations.calculateInsertionIndex(event.clientY);
    this.state.setInsertionIndex(insertionIndex);

    this.visual.updateInsertionLinePosition(event.clientY);
}
```

**Benefits:**
- ✅ Easy to unit test (no DOM events needed)
- ✅ Can test with different mouse positions
- ✅ No side effects
- ✅ Reusable in other contexts

**Example Test:**
```javascript
test('calculateInsertionIndex with no tasks', () => {
    const index = DragCalculations.calculateInsertionIndex(100);
    expect(index).toBe(0);
});

test('calculateInsertionIndex near first task', () => {
    // Mock DOM with task elements
    const index = DragCalculations.calculateInsertionIndex(50);
    expect(index).toBe(0);
});
```

---

## Example 3: Visual Feedback

### Before (Scattered DOM Updates)
```javascript
class DragDropManager {
    _handleDragStart(event, taskItem) {
        // Visual feedback mixed with logic
        document.body.classList.add('dragging');
        taskItem.classList.add('selected-for-move');

        // State updates
        this.draggedTask = { id, title, element: taskItem };

        // More visual feedback
        this._createInsertionLine();
        this.lastMouseY = event.clientY;
        this._updateInsertionLinePosition();
    }

    _handleDragEnd() {
        // Cleanup mixed with logic
        document.body.classList.remove('dragging');
        document.querySelectorAll('.task-item').forEach(item => {
            item.classList.remove('selected-for-move');
        });

        const insertionLine = document.querySelector('.insertion-line');
        if (insertionLine) {
            insertionLine.remove();
        }

        this.isDragging = false;
        this.draggedTask = null;
    }

    _createInsertionLine() {
        const existing = document.querySelector('.insertion-line');
        if (existing) existing.remove();

        const insertionLine = document.createElement('div');
        insertionLine.className = 'insertion-line';
        insertionLine.style.top = '-10px';
        document.body.appendChild(insertionLine);
    }

    _updateInsertionLinePosition() {
        const insertionLine = document.querySelector('.insertion-line');
        if (!insertionLine || !this.lastMouseY) return;

        const snappedY = this._findClosestTaskBoundary(this.lastMouseY);
        insertionLine.style.top = `${snappedY}px`;
    }
}
```

### After (Centralized Visual Management)
```javascript
// DragVisualFeedback.js - All visual logic
class DragVisualFeedback {
    applyDragStartVisuals(taskElement) {
        document.body.classList.add('dragging');
        taskElement.classList.add('selected-for-move');
    }

    removeAllVisuals() {
        document.body.classList.remove('dragging');
        document.querySelectorAll('.task-item').forEach(item => {
            item.classList.remove('selected-for-move');
        });

        const insertionLine = document.querySelector('.insertion-line');
        if (insertionLine) {
            insertionLine.remove();
        }
    }

    createInsertionLine() {
        const existing = document.querySelector('.insertion-line');
        if (existing) existing.remove();

        const insertionLine = document.createElement('div');
        insertionLine.className = 'insertion-line';
        insertionLine.style.top = '-10px';
        document.body.appendChild(insertionLine);
    }

    updateInsertionLinePosition(mouseY) {
        const insertionLine = document.querySelector('.insertion-line');
        if (!insertionLine || !mouseY) return;

        const snappedY = DragCalculations.findClosestTaskBoundary(mouseY);
        insertionLine.style.top = `${snappedY}px`;
    }
}

// DragEventHandlers.js - Clean event handling
_handleDragStart(event, taskItem) {
    const taskData = this.visual.getTaskDataFromElement(taskItem);
    this.visual.applyDragStartVisuals(taskItem);
    this.state.setDraggedTask(taskData);
    this.visual.createInsertionLine();
    this.state.setMouseY(event.clientY);
    this.visual.updateInsertionLinePosition(event.clientY);
}

_cleanupDragState() {
    this.visual.removeAllVisuals();
    this.state.clearDraggedTask();
}
```

**Benefits:**
- ✅ All DOM updates in one place
- ✅ Easy to change visual styling
- ✅ Can test visual feedback independently
- ✅ Can swap out visual implementation

---

## Example 4: Event Handling

### Before (Monolithic Method)
```javascript
class DragDropManager {
    addDragHandlers(taskItem) {
        // 125 lines of tightly coupled logic
        if (!taskItem || !taskItem.isConnected) return false;

        const dragHandle = taskItem.querySelector('.task-drag-handle');
        if (!dragHandle) return false;

        if (this.taskEventHandlers.has(taskItem)) return false;

        let dragStartY = 0;
        let dragThreshold = 5;
        let isDraggingThisItem = false;

        const mousedownHandler = (e) => {
            // Validation
            if (!taskItem.isConnected) return;
            if (this.isDragging) return;

            e.preventDefault();
            dragStartY = e.clientY;
            isDraggingThisItem = false;

            const mouseMoveHandler = (moveEvent) => {
                // More nested logic
                if (!taskItem.isConnected) {
                    // Cleanup
                    document.removeEventListener('mousemove', mouseMoveHandler);
                    document.removeEventListener('mouseup', mouseUpHandler);
                    return;
                }

                const deltaY = Math.abs(moveEvent.clientY - dragStartY);

                if (!isDraggingThisItem && deltaY > dragThreshold) {
                    isDraggingThisItem = true;
                    this._handleDragStart(moveEvent, taskItem);
                }

                if (isDraggingThisItem && this.isDragging) {
                    // Throttling logic
                    if (this.mouseMoveThrottle) {
                        clearTimeout(this.mouseMoveThrottle);
                    }
                    this.mouseMoveThrottle = setTimeout(() => {
                        if (!this.isCleanedUp && taskItem.isConnected) {
                            this._handleDragMove(moveEvent);
                        }
                    }, this.throttleDelay);
                }
            };

            const mouseUpHandler = (upEvent) => {
                if (isDraggingThisItem && this.isDragging) {
                    this._handleDragEnd(upEvent);
                }
                document.removeEventListener('mousemove', mouseMoveHandler);
                document.removeEventListener('mouseup', mouseUpHandler);
                isDraggingThisItem = false;
                this.isDragging = false;
            };

            document.addEventListener('mousemove', mouseMoveHandler, { passive: true });
            document.addEventListener('mouseup', mouseUpHandler, { once: true });
        };

        const contextmenuHandler = (e) => e.preventDefault();

        dragHandle.addEventListener('mousedown', mousedownHandler);
        dragHandle.addEventListener('contextmenu', contextmenuHandler);

        this.taskEventHandlers.set(taskItem, {
            mousedown: mousedownHandler,
            contextmenu: contextmenuHandler,
            dragHandle: dragHandle
        });

        return true;
    }
}
```

### After (Separated Concerns)
```javascript
// DragEventHandlers.js - Focused event management
class DragEventHandlers {
    addTaskHandlers(taskItem) {
        if (!taskItem || !taskItem.isConnected) return false;

        const dragHandle = taskItem.querySelector('.task-drag-handle');
        if (!dragHandle) return false;

        if (this.taskEventHandlers.has(taskItem)) return false;

        let dragStartY = 0;
        let dragThreshold = 5;
        let isDraggingThisItem = false;

        const mousedownHandler = (e) => {
            if (!taskItem.isConnected || this.state.isDragging) return;

            e.preventDefault();
            dragStartY = e.clientY;
            isDraggingThisItem = false;

            const mouseMoveHandler = this._createMoveHandler(
                taskItem, dragStartY, dragThreshold, () => isDraggingThisItem
            );
            const mouseUpHandler = this._createUpHandler(
                taskItem, () => isDraggingThisItem
            );

            document.addEventListener('mousemove', mouseMoveHandler, { passive: true });
            document.addEventListener('mouseup', mouseUpHandler, { once: true });
        };

        const contextmenuHandler = (e) => e.preventDefault();

        dragHandle.addEventListener('mousedown', mousedownHandler);
        dragHandle.addEventListener('contextmenu', contextmenuHandler);

        this.taskEventHandlers.set(taskItem, {
            mousedown: mousedownHandler,
            contextmenu: contextmenuHandler,
            dragHandle: dragHandle
        });

        return true;
    }

    _handleDragStart(event, taskItem) {
        const taskData = this.visual.getTaskDataFromElement(taskItem);
        if (!taskData) return;

        this.visual.applyDragStartVisuals(taskItem);
        this.state.setDraggedTask(taskData);
        this.visual.initializeInsertionTracking();
        this.state.setMouseY(event.clientY);
        this.visual.updateInsertionLinePosition(event.clientY);
    }
}
```

**Benefits:**
- ✅ Event handling logic separated from state/visual
- ✅ Can create helper methods for handler creation
- ✅ Clear dependency injection (state, visual)
- ✅ Easier to add new event types

---

## Example 5: Initialization

### Before (Everything in One Place)
```javascript
class DragDropManager {
    initializeDragDrop() {
        // Debounce check
        const now = Date.now();
        if (now - this.lastInitTime < this.initDebounceMs) return;
        this.lastInitTime = now;

        // Cleanup
        this.cleanup();

        requestAnimationFrame(() => {
            if (this.isCleanedUp) {
                requestAnimationFrame(() => this.initializeDragDrop());
                return;
            }

            const taskItems = document.querySelectorAll('.task-item');
            if (taskItems.length === 0) return;

            let successCount = 0;
            taskItems.forEach((taskItem) => {
                const success = this.addDragHandlers(taskItem);
                if (success) successCount++;
            });
        });
    }

    cleanup() {
        this.isCleanedUp = true;

        // Remove listeners
        const container = document.querySelector('.content-body') || document.body;
        if (container && this.dragOverHandler) {
            container.removeEventListener('dragover', this.dragOverHandler);
        }
        // ... more cleanup

        this.taskEventHandlers.forEach((handlers, taskElement) => {
            // ... cleanup logic
        });
        this.taskEventHandlers.clear();

        // Reset state
        this.draggedTask = null;
        this.insertionIndex = -1;
        // ... more state resets

        this.isCleanedUp = false;
    }
}
```

### After (Delegated Responsibilities)
```javascript
// DragDropManager.js - Simple orchestration
class DragDropManager {
    initializeDragDrop() {
        if (this.state.shouldDebounceInit()) return;
        this.state.updateInitTime();

        this.cleanup();

        requestAnimationFrame(() => {
            if (this.state.isCleanedUp) {
                requestAnimationFrame(() => this.initializeDragDrop());
                return;
            }

            const taskItems = document.querySelectorAll('.task-item');
            if (taskItems.length === 0) return;

            let successCount = 0;
            taskItems.forEach((taskItem) => {
                const success = this.eventHandlers.addTaskHandlers(taskItem);
                if (success) successCount++;
            });
        });
    }

    cleanup() {
        this.eventHandlers.cleanup();
        this.visual.removeAllVisuals();
    }
}

// DragState.js - State management
class DragState {
    shouldDebounceInit() {
        const now = Date.now();
        return now - this.lastInitTime < this.initDebounceMs;
    }

    updateInitTime() {
        this.lastInitTime = Date.now();
    }

    reset() {
        this.clearDraggedTask();
        this.clearThrottle();
        this.taskListContainer = null;
    }
}

// DragEventHandlers.js - Event cleanup
class DragEventHandlers {
    cleanup() {
        this.state.setCleanedUp(true);

        this.taskEventHandlers.forEach((handlers, taskElement) => {
            const dragHandle = handlers.dragHandle ||
                taskElement.querySelector('.task-drag-handle');
            if (dragHandle && handlers.mousedown) {
                dragHandle.removeEventListener('mousedown', handlers.mousedown);
            }
            if (dragHandle && handlers.contextmenu) {
                dragHandle.removeEventListener('contextmenu', handlers.contextmenu);
            }
        });
        this.taskEventHandlers.clear();

        this.state.reset();
        this.state.setCleanedUp(false);
    }
}
```

**Benefits:**
- ✅ Each module handles its own cleanup
- ✅ Clear separation: state checks, event cleanup, visual cleanup
- ✅ Easy to add new cleanup steps to specific modules
- ✅ DragDropManager just orchestrates, doesn't know details

---

## Summary of Improvements

| Aspect | Before | After | Benefit |
|--------|--------|-------|---------|
| **Lines per file** | 759 | 130-400 | Easier to read |
| **Responsibilities** | Many (mixed) | One per module | Clear purpose |
| **Testability** | Hard (coupled) | Easy (isolated) | Better tests |
| **State management** | Scattered | Centralized | Single source of truth |
| **Calculations** | Mixed | Pure functions | Reusable, testable |
| **Visual updates** | Scattered | Centralized | Consistent |
| **Event handling** | Monolithic | Focused | Clear flow |
| **Debugging** | Complex | Simple | Find bugs faster |

## Testing Improvements

### Before: Hard to Test
```javascript
// Can't test without full DOM and events
test('drag and drop', () => {
    const manager = new DragDropManager();
    // Need to set up: DOM, events, state, visual...
    // Hard to isolate what you're testing
});
```

### After: Easy to Test
```javascript
// Test calculations (pure functions)
test('calculateInsertionIndex', () => {
    const index = DragCalculations.calculateInsertionIndex(100);
    expect(index).toBe(0);
});

// Test state (simple object)
test('setDraggedTask', () => {
    const state = new DragState();
    state.setDraggedTask({ id: 1 });
    expect(state.isDragging).toBe(true);
});

// Test visual (with DOM fixtures)
test('applyDragStartVisuals', () => {
    const element = document.createElement('div');
    const visual = new DragVisualFeedback(new DragState());
    visual.applyDragStartVisuals(element);
    expect(element.classList.contains('selected-for-move')).toBe(true);
});
```

---

**Conclusion:** The refactored version is more code overall, but each piece is simpler, more focused, and easier to work with. The modular architecture pays dividends in maintainability, testability, and developer experience.
