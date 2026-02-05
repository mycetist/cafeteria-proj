/**
 * Authentication utilities for the Cafeteria Management System
 * Handles JWT token storage, retrieval, and API calls
 */

// Token management
const Auth = {
    getToken() {
        return localStorage.getItem('access_token');
    },
    
    getRefreshToken() {
        return localStorage.getItem('refresh_token');
    },
    
    getUser() {
        const user = localStorage.getItem('user');
        return user ? JSON.parse(user) : null;
    },
    
    isAuthenticated() {
        return !!this.getToken();
    },
    
    hasRole(role) {
        const user = this.getUser();
        return user && user.role === role;
    },
    
    logout() {
        // Call logout endpoint to clear cookies
        fetch('/api/auth/logout', {
            method: 'POST',
            credentials: 'include'
        }).catch(() => {}).finally(() => {
            // Clear local storage
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            
            // Redirect to login
            window.location.href = '/login';
        });
    },
    
    async refreshToken() {
        const refreshToken = this.getRefreshToken();
        if (!refreshToken) {
            this.logout();
            return null;
        }
        
        try {
            const response = await fetch('/api/auth/refresh', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${refreshToken}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                return data.access_token;
            } else {
                this.logout();
                return null;
            }
        } catch (error) {
            this.logout();
            return null;
        }
    },
    
    // Get headers for API calls
    getHeaders() {
        const token = this.getToken();
        return {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
        };
    },
    
    // Make authenticated API call
    async apiCall(url, options = {}) {
        const headers = this.getHeaders();
        
        const config = {
            ...options,
            headers: {
                ...headers,
                ...options.headers
            }
        };
        
        let response = await fetch(url, config);
        
        // If token expired, try to refresh
        if (response.status === 401) {
            const newToken = await this.refreshToken();
            if (newToken) {
                config.headers['Authorization'] = `Bearer ${newToken}`;
                response = await fetch(url, config);
            }
        }
        
        return response;
    }
};

// Global logout function for onclick handlers
function logout() {
    Auth.logout();
}

// Check authentication on page load
document.addEventListener('DOMContentLoaded', function() {
    // Update UI with user info if authenticated (from localStorage)
    const user = Auth.getUser();
    if (user) {
        const userNameEl = document.getElementById('userName');
        if (userNameEl) {
            userNameEl.textContent = user.full_name;
        }
    }
    // Note: Server-side routes now handle authentication via cookies
    // No need to redirect client-side
});

// Protect role-specific pages
function requireRole(role) {
    const user = Auth.getUser();
    if (!user || user.role !== role) {
        window.location.href = '/login';
    }
}
