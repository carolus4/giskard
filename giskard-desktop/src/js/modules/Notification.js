/**
 * Notification - Toast notification system
 */
class Notification {
    /**
     * Show a success message
     */
    static success(message) {
        this.show(message, 'success');
    }

    /**
     * Show an error message
     */
    static error(message) {
        this.show(message, 'error');
    }

    /**
     * Show an info message
     */
    static info(message) {
        this.show(message, 'info');
    }

    /**
     * Show a notification
     */
    static show(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            padding: '12px 16px',
            borderRadius: '8px',
            background: this.getBackgroundColor(type),
            color: '#fff',
            fontWeight: '500',
            fontSize: '14px',
            zIndex: '1000',
            transform: 'translateX(100%)',
            transition: 'transform 0.3s ease',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
        });
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    /**
     * Get background color based on notification type
     */
    static getBackgroundColor(type) {
        const colors = {
            success: '#4caf50',
            error: '#dc4c3e',
            info: '#2196f3',
            warning: '#ff9500'
        };
        return colors[type] || colors.info;
    }

    /**
     * Clear all notifications
     */
    static clearAll() {
        const notifications = document.querySelectorAll('.notification');
        notifications.forEach(notification => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        });
    }
}

export default Notification;
