/**
 * ModelManager - Centralized model configuration management
 * Singleton pattern to ensure single source of truth for model information
 */
class ModelManager {
    constructor() {
        if (ModelManager.instance) {
            return ModelManager.instance;
        }
        
        this.modelName = 'gemma3:4b'; // Default fallback
        this.listeners = [];
        this.loaded = false;
        this.loading = false;
        
        ModelManager.instance = this;
    }

    /**
     * Load model configuration from backend
     */
    async load() {
        if (this.loaded || this.loading) {
            return this.modelName;
        }
        
        this.loading = true;
        
        try {
            const response = await window.apiClient.getModelConfig();
            if (response.success && response.data) {
                this.modelName = response.data.model;
                console.log('🤖 ModelManager: Loaded model config:', this.modelName);
            }
        } catch (error) {
            console.warn('⚠️ ModelManager: Failed to load model config, using default:', error);
            // Keep the default fallback
        } finally {
            this.loaded = true;
            this.loading = false;
            this._notifyListeners();
        }
        
        return this.modelName;
    }

    /**
     * Get current model name (synchronous)
     */
    getModelName() {
        return this.modelName;
    }

    /**
     * Subscribe to model updates
     * @param {Function} callback - Function to call when model is loaded/updated
     */
    subscribe(callback) {
        this.listeners.push(callback);
        
        // If already loaded, call immediately
        if (this.loaded) {
            callback(this.modelName);
        }
    }

    /**
     * Unsubscribe from model updates
     * @param {Function} callback - Callback to remove
     */
    unsubscribe(callback) {
        const index = this.listeners.indexOf(callback);
        if (index > -1) {
            this.listeners.splice(index, 1);
        }
    }

    /**
     * Notify all listeners of model update
     */
    _notifyListeners() {
        this.listeners.forEach(callback => {
            try {
                callback(this.modelName);
            } catch (error) {
                console.error('Error in model update listener:', error);
            }
        });
    }

    /**
     * Force reload model configuration
     */
    async reload() {
        this.loaded = false;
        this.loading = false;
        return await this.load();
    }

    /**
     * Check if model is loaded
     */
    isLoaded() {
        return this.loaded;
    }
}

// Export singleton instance
export default new ModelManager();
