# DragDropManager Quick Reference Card

## 📁 File Structure

```
src/js/modules/
├── DragDropManager-refactored.js   # Main orchestrator
└── drag-drop/
    ├── DragState.js                # State management
    ├── DragCalculations.js         # Position calculations
    ├── DragVisualFeedback.js       # UI updates
    └── DragEventHandlers.js        # Event handling
```

---

## 🎯 Quick Import

```javascript
import DragDropManager from './modules/DragDropManager-refactored.js';

const manager = new DragDropManager();
manager.initializeDragDrop();
```

---

## 📚 Module Cheat Sheet

### **DragDropManager** (Orchestrator)

```javascript
const manager = new DragDropManager();

// Initialize drag-drop for all tasks
manager.initializeDragDrop();

// Clean up all listeners and state
manager.cleanup();

// Clear drag state (useful for errors)
manager.clearDragState();

// Debug mode
manager.enableDebug();
manager.disableDebug();

// Verify initialization
const isValid = manager.verifyInitialization(); // returns boolean

// Force re-initialization
manager.forceReinit();
```

---

### **DragState** (State Management)

```javascript
const state = new DragState();

// Set dragged task
state.setDraggedTask({ id: 1, title: 'Task', element: elem });

// Clear dragged task
state.clearDraggedTask();

// Set/get state
state.setInsertionIndex(2);
state.setMouseY(450);

// Debouncing
if (state.shouldDebounceInit()) return;
state.updateInitTime();

if (state.shouldDebounceReorder()) return;
state.updateReorderTime();

// Debug
state.enableDebug();
state.disableDebug();
state.log('Debug message');

// Reset all state
state.reset();
```

**Key Properties:**
- `draggedTask` - Current dragged task object
- `insertionIndex` - Target insertion index
- `isDragging` - Whether currently dragging
- `lastMouseY` - Last mouse Y position
- `isDropping` - Whether drop in progress

---

### **DragCalculations** (Static Utilities)

```javascript
// Calculate insertion index from mouse Y
const index = DragCalculations.calculateInsertionIndex(mouseY);

// Find closest task boundary for insertion line
const snappedY = DragCalculations.findClosestTaskBoundary(mouseY);

// Calculate new task sequence after reorder
const newSequence = DragCalculations.calculateReorderSequence(
    draggedTaskId,
    insertionIndex
);

// Check if order changed
const changed = DragCalculations.hasOrderChanged(newSequence);
```

**All methods are pure functions** - no state, no side effects!

---

### **DragVisualFeedback** (UI Management)

```javascript
const visual = new DragVisualFeedback(state);

// Apply visual feedback when drag starts
visual.applyDragStartVisuals(taskElement);

// Remove all visual feedback
visual.removeAllVisuals();

// Create insertion line
visual.createInsertionLine();

// Update insertion line position
visual.updateInsertionLinePosition(mouseY);

// Initialize insertion tracking
const success = visual.initializeInsertionTracking();

// Validate element
const isValid = visual.isElementValid(element);

// Get task data from DOM
const taskData = visual.getTaskDataFromElement(element);
// Returns: { id, title, element } or null
```

---

### **DragEventHandlers** (Event Management)

```javascript
const handlers = new DragEventHandlers(state, visual, onDragEndCallback);

// Add drag handlers to task
const success = handlers.addTaskHandlers(taskItem);

// Clean up all event listeners
handlers.cleanup();

// Access handler map (for debugging)
const handlersMap = handlers.taskEventHandlers; // Map<element, handlers>
```

**Event Flow:**
1. `mousedown` on drag handle
2. `mousemove` (throttled) → calculates position
3. `mouseup` → triggers drop/reorder

---

## 🔔 Events

### Listen for Reorder

```javascript
document.addEventListener('task:reorder', (e) => {
    const newSequence = e.detail.taskIdSequence;
    console.log('New order:', newSequence); // [3, 1, 2, 4, 5]

    // Update backend, UI, etc.
});
```

---

## 🐛 Debugging

### Enable Debug Mode

```javascript
manager.enableDebug();

// You'll see logs like:
// 🔧 DragDropManager.initializeDragDrop() called
// 📝 Found 5 task items to initialize
// 🎯 DRAG START: "Task title" - taskId: 123
// 📍 DRAG MOVE: Y: 450 Index: 2
// 🔚 DRAG END: 123 at index 2
// 📝 REORDER: Complete new task ID sequence: [1, 3, 2]
```

### Check Initialization

```javascript
const isValid = manager.verifyInitialization();
// Logs warnings if handlers are missing
```

### Browser Console

```javascript
// Access manager globally (if exposed)
window.dragDropManager.enableDebug();

// Check state
window.dragDropManager.state.isDragging; // false
window.dragDropManager.state.draggedTask; // null or { id, title, element }

// Check handlers
window.dragDropManager.eventHandlers.taskEventHandlers.size; // number of tasks
```

---

## 🧪 Testing Examples

### Test State

```javascript
test('setDraggedTask updates state', () => {
    const state = new DragState();
    state.setDraggedTask({ id: 1, title: 'Test', element: elem });

    expect(state.draggedTask.id).toBe(1);
    expect(state.isDragging).toBe(true);
});
```

### Test Calculations

```javascript
test('calculateInsertionIndex with no tasks', () => {
    // Mock empty DOM
    document.body.innerHTML = '';

    const index = DragCalculations.calculateInsertionIndex(100);
    expect(index).toBe(0);
});
```

### Test Visual Feedback

```javascript
test('applyDragStartVisuals adds classes', () => {
    const element = document.createElement('div');
    const state = new DragState();
    const visual = new DragVisualFeedback(state);

    visual.applyDragStartVisuals(element);

    expect(document.body.classList.contains('dragging')).toBe(true);
    expect(element.classList.contains('selected-for-move')).toBe(true);
});
```

---

## 💡 Common Patterns

### Initialize on Page Load

```javascript
document.addEventListener('DOMContentLoaded', () => {
    const manager = new DragDropManager();
    manager.initializeDragDrop();
});
```

### Re-initialize After DOM Update

```javascript
function addNewTask(taskData) {
    // Add task to DOM
    taskList.appendChild(newTaskElement);

    // Re-initialize drag-drop
    manager.forceReinit();
}
```

### Handle Reorder

```javascript
document.addEventListener('task:reorder', async (e) => {
    const newSequence = e.detail.taskIdSequence;

    // Update backend
    await fetch('/api/tasks/reorder', {
        method: 'POST',
        body: JSON.stringify({ sequence: newSequence })
    });

    // Refresh UI
    await refreshTaskList();

    // Re-initialize drag-drop
    manager.forceReinit();
});
```

---

## ⚠️ Common Issues

### Issue: Drag doesn't start
**Solution:**
```javascript
// Check handlers are attached
manager.verifyInitialization();

// Check drag handles exist
document.querySelectorAll('.task-drag-handle').length; // should match task count

// Re-initialize
manager.forceReinit();
```

### Issue: Insertion line doesn't appear
**Solution:**
```javascript
// Check CSS exists
const line = document.querySelector('.insertion-line');
console.log(line); // should exist when dragging

// Check visual feedback module
manager.visual.createInsertionLine();
```

### Issue: Reorder event doesn't fire
**Solution:**
```javascript
// Check event listener is registered
document.addEventListener('task:reorder', (e) => {
    console.log('Event fired!', e.detail);
});

// Enable debug to see if drop logic runs
manager.enableDebug();
```

---

## 🔧 Configuration

### Adjust Debouncing

```javascript
const manager = new DragDropManager();

// Adjust init debounce (default: 200ms)
manager.state.initDebounceMs = 100;

// Adjust reorder debounce (default: 500ms)
manager.state.reorderDebounceMs = 300;
```

### Adjust Throttling

```javascript
// Adjust mousemove throttle (default: 16ms = ~60fps)
manager.state.throttleDelay = 8; // ~120fps
```

### Adjust Drag Threshold

Currently hardcoded in DragEventHandlers. To modify:

```javascript
// In DragEventHandlers.addTaskHandlers()
let dragThreshold = 5; // pixels - change this value
```

---

## 📋 Migration Checklist

- [ ] Import refactored DragDropManager
- [ ] Test drag and drop functionality
- [ ] Test reorder events
- [ ] Test initialization/re-initialization
- [ ] Test debug mode
- [ ] Test with rapid DOM updates
- [ ] Test cleanup (no memory leaks)
- [ ] Deploy to staging
- [ ] User acceptance test
- [ ] Deploy to production
- [ ] Monitor for errors
- [ ] Archive old DragDropManager.js

---

## 🆘 Need Help?

1. **Enable Debug Mode:** `manager.enableDebug()`
2. **Check Initialization:** `manager.verifyInitialization()`
3. **Check Console:** Look for error messages
4. **Check State:** `manager.state` in console
5. **Force Re-init:** `manager.forceReinit()`

---

## 📖 Full Documentation

- [DRAGDROP_REFACTOR_GUIDE.md](./DRAGDROP_REFACTOR_GUIDE.md) - Complete migration guide
- [DRAGDROP_REFACTOR_SUMMARY.md](./DRAGDROP_REFACTOR_SUMMARY.md) - Architecture overview
- [REFACTORING_COMPARISON.md](./REFACTORING_COMPARISON.md) - Before/after code examples

---

**Last Updated:** 2025-10-23
