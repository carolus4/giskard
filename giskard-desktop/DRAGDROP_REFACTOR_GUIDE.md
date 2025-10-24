# DragDropManager Refactoring Guide

## Overview

The DragDropManager has been refactored from a monolithic 759-line class into a modular architecture with clear separation of concerns.

## New Architecture

### Module Structure

```
src/js/modules/
├── drag-drop/
│   ├── DragState.js              # State management (157 lines)
│   ├── DragCalculations.js       # Position/index calculations (130 lines)
│   ├── DragVisualFeedback.js     # UI updates and visual feedback (150 lines)
│   └── DragEventHandlers.js      # Event handling (400 lines)
└── DragDropManager-refactored.js # Orchestrator (180 lines)
```

### Responsibilities

#### 1. **DragState** (State Management)
- Manages all drag operation state
- Tracks: draggedTask, insertionIndex, isDragging, etc.
- Provides state validation methods
- Handles debouncing logic
- Controls debug mode

**Key Methods:**
- `setDraggedTask(task)` - Set current dragged task
- `clearDraggedTask()` - Clear drag state
- `shouldDebounceInit()` - Check if init should be debounced
- `shouldDebounceReorder()` - Check if reorder should be debounced
- `enableDebug()` / `disableDebug()` - Toggle debug logging

#### 2. **DragCalculations** (Static Utility)
- Pure functions for calculations
- No state, no side effects
- Position and index calculations

**Key Methods:**
- `calculateInsertionIndex(mouseY)` - Calculate where to insert based on Y position
- `findClosestTaskBoundary(mouseY)` - Find Y position for insertion line snapping
- `calculateReorderSequence(draggedId, insertionIndex)` - Calculate new task order
- `hasOrderChanged(newSequence)` - Check if order actually changed

#### 3. **DragVisualFeedback** (UI Updates)
- Manages all DOM manipulation for visual feedback
- Creates and updates insertion line
- Applies/removes CSS classes
- Validates DOM elements

**Key Methods:**
- `applyDragStartVisuals(element)` - Add dragging visual classes
- `removeAllVisuals()` - Clean up all visual feedback
- `createInsertionLine()` - Create insertion line element
- `updateInsertionLinePosition(mouseY)` - Update line position
- `getTaskDataFromElement(element)` - Extract task data from DOM

#### 4. **DragEventHandlers** (Event Management)
- Manages all event listeners
- Handles mousedown, mousemove, mouseup events
- Orchestrates drag start/move/end lifecycle
- Throttles mousemove for performance

**Key Methods:**
- `addTaskHandlers(taskItem)` - Add drag handlers to task
- `cleanup()` - Remove all event listeners
- Internal: `_handleDragStart()`, `_handleDragMove()`, `_handleDragEnd()`, `_handleDrop()`

#### 5. **DragDropManager** (Orchestrator)
- Coordinates all modules
- Public API for initialization and control
- Emits custom events for reordering

**Key Methods:**
- `initializeDragDrop()` - Initialize drag-drop for all tasks
- `cleanup()` - Clean up listeners
- `enableDebug()` / `disableDebug()` - Toggle debug mode
- `verifyInitialization()` - Check if properly initialized
- `forceReinit()` - Force re-initialization

## Benefits

### 1. **Single Responsibility Principle**
Each module has one clear purpose:
- State → DragState
- Calculations → DragCalculations
- Visual Updates → DragVisualFeedback
- Events → DragEventHandlers
- Coordination → DragDropManager

### 2. **Testability**
- Each module can be unit tested independently
- DragCalculations has pure functions (easiest to test)
- State can be mocked for event handler tests
- Visual feedback can be tested with DOM fixtures

### 3. **Maintainability**
- Smaller files (130-400 lines vs 759 lines)
- Clear boundaries between concerns
- Easier to locate bugs
- Easier to add features

### 4. **Reusability**
- DragCalculations can be used elsewhere
- DragState pattern can be applied to other features
- Visual feedback logic is decoupled

### 5. **Reduced Cognitive Load**
- Each file focuses on one aspect
- No need to understand entire system to change one part
- Better code navigation

## Migration Path

### Option 1: Gradual Migration (Recommended)

**Phase 1:** Test the refactored version alongside existing
```javascript
// Keep both versions during testing
import DragDropManager from './modules/DragDropManager.js';
import DragDropManagerNew from './modules/DragDropManager-refactored.js';

// Use feature flag to switch
const manager = USE_NEW_DRAG_DROP ?
    new DragDropManagerNew() :
    new DragDropManager();
```

**Phase 2:** Run in parallel with logging
- Enable debug mode on both
- Compare behavior
- Log any discrepancies

**Phase 3:** Full cutover
```javascript
// Replace old import
import DragDropManager from './modules/DragDropManager-refactored.js';
```

**Phase 4:** Cleanup
- Delete old DragDropManager.js
- Rename DragDropManager-refactored.js → DragDropManager.js

### Option 2: Direct Replacement (Faster)

1. Backup current DragDropManager.js
2. Replace with refactored version
3. Test thoroughly
4. Rollback if issues

## Testing Checklist

- [ ] Drag and drop works for single task
- [ ] Drag and drop works for multiple tasks
- [ ] Insertion line appears and moves correctly
- [ ] Insertion line snaps to task boundaries
- [ ] Reorder event is emitted with correct task IDs
- [ ] No visual glitches during drag
- [ ] Works with rapid re-initialization
- [ ] Cleanup doesn't leave orphaned listeners
- [ ] Works after DOM updates (new tasks added)
- [ ] Throttling works (no performance issues)
- [ ] Debouncing works (no duplicate reorders)
- [ ] Debug mode provides useful logging
- [ ] Verify initialization reports correct status

## Debugging

### Enable Debug Mode
```javascript
// In browser console
window.__giskardApp.taskManager.dragDrop.enableDebug();

// You should see detailed logs like:
// 🔧 DragDropManager.initializeDragDrop() called
// 📝 Found 5 task items to initialize
// ⚙️  Initializing drag for task 1: {...}
// 🎯 DRAG START: "Task title" - taskId: 123
// 📍 DRAG MOVE: Y: 450 Index: 2
// 🔚 DRAG END: 123 at index 2
```

### Common Issues

**Issue:** Drag doesn't start
- Check: Are task-drag-handle elements present?
- Check: Are event handlers attached? (`verifyInitialization()`)
- Check: Console for errors during `addTaskHandlers()`

**Issue:** Insertion line doesn't appear
- Check: Is `createInsertionLine()` called?
- Check: CSS for `.insertion-line` exists
- Check: Element is added to DOM (`document.querySelector('.insertion-line')`)

**Issue:** Reorder doesn't work
- Check: Is `task:reorder` event emitted?
- Check: Task ID sequence calculated correctly
- Check: Event listener registered for `task:reorder`

## API Compatibility

The refactored version maintains the same public API:

```javascript
const manager = new DragDropManager();

// Identical API
manager.initializeDragDrop();
manager.cleanup();
manager.clearDragState();
manager.enableDebug();
manager.disableDebug();
manager.verifyInitialization();
manager.forceReinit();
```

**Breaking Changes:** None! The public API is 100% compatible.

## Performance

### Metrics
- **Original:** 759 lines in one file
- **Refactored:** ~1017 lines total across 5 files
- **Largest module:** 400 lines (DragEventHandlers)
- **Smallest module:** 130 lines (DragCalculations)

### Performance Impact
- **No runtime overhead** - Same logic, better organization
- **Slightly larger bundle** - 5 files vs 1 (minimal impact with tree-shaking)
- **Better minification** - Smaller modules compress better
- **Same throttling/debouncing** - Performance optimizations preserved

## Future Enhancements

With modular architecture, these become easier:

1. **Touch Support**
   - Add TouchEventHandlers module
   - Share DragState and DragCalculations

2. **Accessibility**
   - Add KeyboardEventHandlers for keyboard navigation
   - Share calculations and visual feedback

3. **Animation**
   - Add DragAnimations module
   - Smooth transitions between positions

4. **Multi-select**
   - Extend DragState to track multiple selected tasks
   - Update calculations for batch moves

5. **Undo/Redo**
   - Track reorder history in DragState
   - Implement undo/redo operations

## Questions?

Common questions during migration:

**Q: Why is the refactored version more lines of code?**
A: Better organization requires some boilerplate (imports, exports, class definitions). But each individual file is much smaller and easier to understand.

**Q: Is there a performance penalty?**
A: No, the logic is identical. Modern bundlers (like Vite/Rollup) will tree-shake and minify efficiently.

**Q: Can I mix and match modules?**
A: Yes! DragCalculations is completely standalone. Others depend on DragState but you could use different implementations.

**Q: Do I need to update my event listeners?**
A: No, the `task:reorder` event remains the same.

**Q: What if I find a bug in the refactored version?**
A: Keep the old DragDropManager.js as a backup. Switch back via imports. Report the issue with debug logs.

## Rollback Plan

If you need to rollback:

1. **Quick Rollback** (< 1 minute)
   ```javascript
   // In TaskManager.js or wherever DragDropManager is imported
   import DragDropManager from './modules/DragDropManager.js'; // Old version
   ```

2. **Full Rollback** (< 5 minutes)
   - Restore DragDropManager.js from backup
   - Delete drag-drop/ directory
   - Delete DragDropManager-refactored.js
   - Clear browser cache
   - Restart app

## Success Criteria

Migration is successful when:

- ✅ All drag and drop functionality works identically
- ✅ No console errors or warnings
- ✅ Visual feedback is smooth and responsive
- ✅ Reorder events fire correctly
- ✅ Debug mode provides useful information
- ✅ Tests pass (if applicable)
- ✅ User acceptance testing confirms no regressions

---

**Ready to migrate?** Start with Option 1 (Gradual Migration) for safety, or Option 2 (Direct Replacement) if you have comprehensive tests.
