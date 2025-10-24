/**
 * DragCalculations - Handles all position and index calculations for drag and drop
 */
class DragCalculations {
    /**
     * Calculate the insertion index based on mouse Y position
     * @param {number} mouseY - Current mouse Y position
     * @returns {number} - Insertion index
     */
    static calculateInsertionIndex(mouseY) {
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
     * Find the closest task boundary Y position for snapping the insertion line
     * @param {number} mouseY - Current mouse Y position
     * @returns {number} - Y position to snap to
     */
    static findClosestTaskBoundary(mouseY) {
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
     * Calculate the new task ID sequence after reordering
     * @param {number} draggedTaskId - ID of the task being dragged
     * @param {number} insertionIndex - Target insertion index
     * @returns {Array<number>} - New sequence of task IDs
     */
    static calculateReorderSequence(draggedTaskId, insertionIndex) {
        // Get all visible tasks in current order (including dragged one)
        const allVisibleTasks = Array.from(document.querySelectorAll('.task-item'));

        // Extract the task IDs in their current visual positions, filtering out invalid ones
        const taskIds = allVisibleTasks
            .map(task => {
                const taskId = task.dataset.taskId;
                return taskId && taskId !== '' ? parseInt(taskId) : null;
            })
            .filter(taskId => taskId !== null);

        // Find dragged task position
        const draggedVisualPos = allVisibleTasks.findIndex(
            item => {
                const taskId = item.dataset.taskId;
                return taskId && taskId !== '' && parseInt(taskId) === draggedTaskId;
            }
        );

        // Create a new array without the dragged task
        const reorderedTaskIds = [...taskIds];
        reorderedTaskIds.splice(draggedVisualPos, 1);  // Remove dragged task
        reorderedTaskIds.splice(insertionIndex, 0, draggedTaskId);  // Insert at new position

        return reorderedTaskIds;
    }

    /**
     * Check if the order has actually changed
     * @param {Array<number>} newSequence - New task ID sequence
     * @returns {boolean} - True if order changed
     */
    static hasOrderChanged(newSequence) {
        const allVisibleTasks = Array.from(document.querySelectorAll('.task-item'));
        const currentTaskIds = allVisibleTasks.map(task => parseInt(task.dataset.taskId));

        return JSON.stringify(currentTaskIds) !== JSON.stringify(newSequence);
    }
}

export default DragCalculations;
