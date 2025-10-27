/**
 * TaskDataManager - Centralized task data collection and validation
 *
 * This class provides a single source of truth for accessing task data from the UI,
 * mirroring the backend's TaskDB pattern of centralizing data access and validation.
 *
 * Design principles:
 * - Single Responsibility: Only handles data collection and validation
 * - Encapsulation: Hides implementation details of where data comes from
 * - Consistency: Mirrors backend API's data model and validation rules
 */
class TaskDataManager {
    constructor(pageManager) {
        this.pageManager = pageManager;
    }

    /**
     * Get current task data from the detail page
     * This is the single source of truth for collecting task data from the UI
     *
     * @returns {Object} Current task data {title, description, project, categories}
     */
    getCurrentTaskData() {
        const titleInput = document.getElementById('detail-title');

        return {
            title: this._getTitle(titleInput),
            description: this._getDescription(),
            // Future: Add other fields here as needed
            // project: this._getProject(),
            // categories: this._getCategories(),
        };
    }

    /**
     * Get only changed fields by comparing current data with original task
     * Useful for partial updates to minimize API payload
     *
     * @param {Object} originalTask - The original task object
     * @returns {Object} Only the fields that have changed
     */
    getChangedFields(originalTask) {
        const currentData = this.getCurrentTaskData();
        const changes = {};

        if (currentData.title !== originalTask.title) {
            changes.title = currentData.title;
        }

        if (currentData.description !== (originalTask.description || '')) {
            changes.description = currentData.description;
        }

        return changes;
    }

    /**
     * Validate task data before sending to API
     * Mirrors backend validation rules
     *
     * @param {Object} data - Task data to validate
     * @returns {Object} Validated and sanitized data
     * @throws {Error} If validation fails
     */
    validateTaskData(data) {
        const validated = {};

        // Title validation (matches backend: required, max 200 chars)
        if (data.title !== undefined) {
            const title = data.title.trim();
            if (!title) {
                throw new Error('Title cannot be empty');
            }
            if (title.length > 200) {
                throw new Error('Title too long (max 200 characters)');
            }
            validated.title = title;
        }

        // Description validation (sanitize, allow empty)
        if (data.description !== undefined) {
            validated.description = data.description.trim();
        }

        // Project validation
        if (data.project !== undefined) {
            validated.project = data.project;
        }

        // Categories validation
        if (data.categories !== undefined) {
            if (!Array.isArray(data.categories)) {
                throw new Error('Categories must be an array');
            }
            validated.categories = data.categories;
        }

        return validated;
    }

    /**
     * Prepare task data for API submission
     * Combines collection, validation, and sanitization
     *
     * @param {Object} overrides - Optional field overrides
     * @returns {Object} API-ready task data
     */
    prepareForAPI(overrides = {}) {
        const currentData = this.getCurrentTaskData();
        const mergedData = { ...currentData, ...overrides };
        return this.validateTaskData(mergedData);
    }

    // Private helper methods

    /**
     * Get current title from input
     * @private
     */
    _getTitle(titleInput) {
        if (!titleInput) {
            titleInput = document.getElementById('detail-title');
        }
        return titleInput?.value.trim() || '';
    }

    /**
     * Get current description from GitHub editor
     * Handles both edit mode (live textarea) and view mode (saved content)
     * @private
     */
    _getDescription() {
        if (!this.pageManager.githubEditor) {
            return '';
        }
        return this.pageManager.githubEditor.getContent() || '';
    }

    /**
     * Check if current task data is valid for submission
     * @returns {boolean} True if valid
     */
    isValid() {
        try {
            const data = this.getCurrentTaskData();
            this.validateTaskData(data);
            return true;
        } catch (error) {
            return false;
        }
    }

    /**
     * Get validation errors for current task data
     * @returns {Array<string>} Array of error messages, empty if valid
     */
    getValidationErrors() {
        const errors = [];
        try {
            const data = this.getCurrentTaskData();
            this.validateTaskData(data);
        } catch (error) {
            errors.push(error.message);
        }
        return errors;
    }
}

export default TaskDataManager;
