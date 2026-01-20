/**
 * Family Office Platform - Dashboard JavaScript
 * Core functionality for UI interactions and API communication
 */

// API Configuration
const API_BASE = '/api/v1';

// Theme Management
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-bs-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-bs-theme', newTheme);
    localStorage.setItem('theme', newTheme);

    // Update icon
    const icon = document.querySelector('#themeToggle i');
    if (icon) {
        icon.className = newTheme === 'dark' ? 'bi bi-sun' : 'bi bi-moon-stars';
    }
}

// Initialize theme on load
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
    const icon = document.querySelector('#themeToggle i');
    if (icon) {
        icon.className = savedTheme === 'dark' ? 'bi bi-sun' : 'bi bi-moon-stars';
    }
});

// API Helper Functions
async function apiRequest(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');

    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        }
    };

    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        });

        if (response.status === 401) {
            // Token expired, try to refresh
            const refreshed = await refreshToken();
            if (refreshed) {
                return apiRequest(endpoint, options);
            }
            // Redirect to login
            window.location.href = '/login';
            return null;
        }

        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

async function refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return false;

    try {
        const response = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${refreshToken}`
            }
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.data.access_token);
            return true;
        }
    } catch (error) {
        console.error('Token refresh failed:', error);
    }

    return false;
}

// Formatting Functions
function formatCurrency(value, currency = 'USD') {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

function formatCurrencyPrecise(value, currency = 'USD') {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(value);
}

function formatPercent(value, decimals = 2) {
    if (value === null || value === undefined) return '-';
    const percent = value * 100;
    const sign = percent >= 0 ? '+' : '';
    return `${sign}${percent.toFixed(decimals)}%`;
}

function formatNumber(value, decimals = 2) {
    if (value === null || value === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: decimals
    }).format(value);
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

function formatDateShort(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric'
    }).format(date);
}

// Color Helpers
function getChangeColor(value) {
    if (value > 0) return 'text-success';
    if (value < 0) return 'text-danger';
    return 'text-muted';
}

function getBgColor(value) {
    if (value > 0) return 'bg-success';
    if (value < 0) return 'bg-danger';
    return 'bg-secondary';
}

// Loading State Helpers
function showLoading(elementId, message = 'Loading...') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">${message}</span>
                </div>
                <p class="text-muted mt-2">${message}</p>
            </div>
        `;
    }
}

function showError(elementId, message = 'An error occurred') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="text-center py-4">
                <i class="bi bi-exclamation-triangle text-danger fs-1"></i>
                <p class="text-danger mt-2">${message}</p>
                <button class="btn btn-sm btn-outline-primary" onclick="location.reload()">
                    <i class="bi bi-arrow-clockwise me-1"></i>Retry
                </button>
            </div>
        `;
    }
}

function showEmpty(elementId, message = 'No data available') {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div class="text-center py-4">
                <i class="bi bi-inbox text-muted fs-1"></i>
                <p class="text-muted mt-2">${message}</p>
            </div>
        `;
    }
}

// Toast Notifications
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();

    toast.addEventListener('hidden.bs.toast', () => toast.remove());
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}

// Confirmation Dialog
function confirmAction(message, onConfirm, onCancel) {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Confirm Action</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>${message}</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" id="confirmBtn">Confirm</button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
    const bsModal = new bootstrap.Modal(modal);

    modal.querySelector('#confirmBtn').addEventListener('click', () => {
        bsModal.hide();
        if (onConfirm) onConfirm();
    });

    modal.addEventListener('hidden.bs.modal', () => {
        modal.remove();
        if (onCancel) onCancel();
    });

    bsModal.show();
}

// Data Table Helpers
function createTableRow(columns, isHeader = false) {
    const tag = isHeader ? 'th' : 'td';
    return `<tr>${columns.map(col => `<${tag}>${col}</${tag}>`).join('')}</tr>`;
}

// Debounce Function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle Function
function throttle(func, limit) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Local Storage Helpers
function setStorageItem(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
        console.error('Error saving to localStorage:', e);
    }
}

function getStorageItem(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (e) {
        console.error('Error reading from localStorage:', e);
        return defaultValue;
    }
}

// Export for use in other scripts
window.FamilyOffice = {
    apiRequest,
    formatCurrency,
    formatCurrencyPrecise,
    formatPercent,
    formatNumber,
    formatDate,
    formatDateShort,
    getChangeColor,
    getBgColor,
    showLoading,
    showError,
    showEmpty,
    showToast,
    confirmAction,
    debounce,
    throttle,
    setStorageItem,
    getStorageItem
};
