// Automotive Price Monitor Dashboard JavaScript

// Global variables
let autoRefreshInterval;
let chartInstances = {};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
    startAutoRefresh();
});

function initializeDashboard() {
    console.log('🚀 Initializing Automotive Price Monitor Dashboard');
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Setup form validation
    setupFormValidation();
    
    // Setup AJAX handlers
    setupAjaxHandlers();
    
    console.log('✅ Dashboard initialized successfully');
}

function setupEventListeners() {
    // Price update buttons
    const priceUpdateButtons = document.querySelectorAll('.btn-update-prices');
    priceUpdateButtons.forEach(button => {
        button.addEventListener('click', function() {
            const priceType = this.getAttribute('data-price-type') || 'avg';
            updatePrices(priceType);
        });
    });
    
    // Manual scraping button
    const scrapingButton = document.querySelector('.btn-start-scraping');
    if (scrapingButton) {
        scrapingButton.addEventListener('click', startManualScraping);
    }
    
    // Export buttons
    const exportButtons = document.querySelectorAll('.btn-export');
    exportButtons.forEach(button => {
        button.addEventListener('click', function() {
            const exportType = this.getAttribute('data-export-type');
            exportData(exportType);
        });
    });
    
    // Search functionality
    const searchInput = document.querySelector('#product-search');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(this.value);
            }, 500);
        });
    }
    
    // Filter change handlers
    const filterSelects = document.querySelectorAll('.filter-select');
    filterSelects.forEach(select => {
        select.addEventListener('change', function() {
            applyFilters();
        });
    });
}

function setupFormValidation() {
    // Bootstrap form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });
    
    // Price validation
    const priceInputs = document.querySelectorAll('input[name*="price"]');
    priceInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = parseFloat(this.value);
            if (value < 0) {
                this.setCustomValidity('قیمت نمی‌تواند منفی باشد');
            } else if (value > 1000000000) {
                this.setCustomValidity('قیمت خیلی زیاد است');
            } else {
                this.setCustomValidity('');
            }
        });
    });
}

function setupAjaxHandlers() {
    // Setup CSRF token for AJAX requests
    const csrfToken = document.querySelector('meta[name=csrf-token]');
    if (csrfToken) {
        fetch.defaults = {
            headers: {
                'X-CSRFToken': csrfToken.getAttribute('content')
            }
        };
    }
}

// Price update functionality
function updatePrices(priceType = 'avg') {
    if (!confirm('آیا مطمئن هستید که می‌خواهید قیمت‌ها را به‌روزرسانی کنید؟')) {
        return;
    }
    
    showLoading('در حال به‌روزرسانی قیمت‌ها...');
    
    fetch('/woocommerce/update-prices', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            price_type: priceType,
            dry_run: false
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        if (data.success) {
            showAlert('success', 'به‌روزرسانی قیمت‌ها با موفقیت شروع شد');
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            showAlert('error', 'خطا: ' + data.error);
        }
    })
    .catch(error => {
        hideLoading();
        showAlert('error', 'خطا در ارتباط با سرور');
        console.error('Error:', error);
    });
}

// Manual scraping functionality
function startManualScraping() {
    const form = document.getElementById('manualScrapingForm');
    const formData = new FormData(form);
    
    showLoading('در حال شروع اسکرپینگ...');
    
    fetch('/scraping/manual', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        hideLoading();
        if (response.ok) {
            showAlert('success', 'اسکرپینگ با موفقیت شروع شد');
        } else {
            showAlert('error', 'خطا در شروع اسکرپینگ');
        }
    })
    .catch(error => {
        hideLoading();
        showAlert('error', 'خطا در ارتباط با سرور');
        console.error('Error:', error);
    });
}

// Data export functionality
function exportData(exportType) {
    showLoading('در حال تولید فایل...');
    
    const url = `/api/export/csv/${exportType}`;
    
    fetch(url)
    .then(response => {
        hideLoading();
        if (response.ok) {
            return response.blob();
        } else {
            throw new Error('Export failed');
        }
    })
    .then(blob => {
        // Download file
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `automotive_${exportType}_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        
        showAlert('success', 'فایل با موفقیت دانلود شد');
    })
    .catch(error => {
        hideLoading();
        showAlert('error', 'خطا در تولید فایل');
        console.error('Error:', error);
    });
}

// Search functionality
function performSearch(query) {
    if (query.length < 2) {
        return;
    }
    
    const searchResults = document.getElementById('search-results');
    if (!searchResults) return;
    
    fetch(`/api/search?q=${encodeURIComponent(query)}`)
    .then(response => response.json())
    .then(data => {
        displaySearchResults(data.results);
    })
    .catch(error => {
        console.error('Search error:', error);
    });
}

function displaySearchResults(results) {
    const container = document.getElementById('search-results');
    if (!container) return;
    
    if (results.length === 0) {
        container.innerHTML = '<p class="text-muted">نتیجه‌ای یافت نشد</p>';
        return;
    }
    
    let html = '<div class="list-group">';
    results.forEach(result => {
        html += `
            <a href="/products/${result.id}" class="list-group-item list-group-item-action">
                <div class="d-flex w-100 justify-content-between">
                    <h6 class="mb-1">${result.name}</h6>
                    <small class="text-muted">${result.category}</small>
                </div>
                <p class="mb-1 text-muted">${result.description || ''}</p>
                <small>قیمت: ${formatCurrency(result.price)}</small>
            </a>
        `;
    });
    html += '</div>';
    
    container.innerHTML = html;
}

// Filter functionality
function applyFilters() {
    const form = document.getElementById('filterForm');
    if (!form) return;
    
    const formData = new FormData(form);
    const params = new URLSearchParams();
    
    for (let [key, value] of formData) {
        if (value) {
            params.append(key, value);
        }
    }
    
    // Update URL and reload page with filters
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.location.href = newUrl;
}

// Chart utilities
function createPriceChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'قیمت میانگین',
                data: data.prices,
                borderColor: 'rgb(75, 192, 192)',
                backgroundColor: 'rgba(75, 192, 192, 0.1)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `قیمت: ${formatCurrency(context.parsed.y)}`;
                        }
                    }
                }
            }
        }
    });
}

function createCategoryChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: [
                    '#FF6384', '#36A2EB', '#FFCE56', '#FF9F40', '#FF6384',
                    '#36A2EB', '#FFCE56', '#FF9F40', '#FF6384', '#36A2EB'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Auto refresh functionality
function startAutoRefresh() {
    const refreshInterval = parseInt(document.body.getAttribute('data-refresh-interval') || '300') * 1000;
    
    if (refreshInterval > 0) {
        autoRefreshInterval = setInterval(() => {
            if (!document.hidden) {  // Only refresh if page is visible
                refreshDashboardData();
            }
        }, refreshInterval);
    }
}

function refreshDashboardData() {
    fetch('/api/stats')
    .then(response => response.json())
    .then(data => {
        updateDashboardStats(data);
    })
    .catch(error => {
        console.error('Auto refresh error:', error);
    });
}

function updateDashboardStats(data) {
    // Update system stats
    if (data.system) {
        updateSystemStats(data.system);
    }
    
    // Update database stats
    if (data.database) {
        updateDatabaseStats(data.database);
    }
    
    // Update scraping stats
    if (data.scraping) {
        updateScrapingStats(data.scraping);
    }
}

// UI utility functions
function showLoading(message = 'در حال بارگذاری...') {
    const loadingHtml = `
        <div id="loading-overlay" class="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center" 
             style="background-color: rgba(0,0,0,0.5); z-index: 9999;">
            <div class="text-center text-white">
                <div class="spinner"></div>
                <p>${message}</p>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', loadingHtml);
}

function hideLoading() {
    const loading = document.getElementById('loading-overlay');
    if (loading) {
        loading.remove();
    }
}

function showAlert(type, message, duration = 5000) {
    const alertHtml = `
        <div class="alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed" 
             style="top: 20px; left: 20px; right: 20px; z-index: 9998;">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('afterbegin', alertHtml);
    
    // Auto dismiss
    setTimeout(() => {
        const alert = document.querySelector('.alert');
        if (alert) {
            alert.remove();
        }
    }, duration);
}

function formatCurrency(value) {
    if (value === null || value === undefined) {
        return '0 ریال';
    }
    return new Intl.NumberFormat('fa-IR').format(Math.round(value)) + ' ریال';
}

function formatNumber(value) {
    if (value === null || value === undefined) {
        return '0';
    }
    return new Intl.NumberFormat('fa-IR').format(value);
}

function getCSRFToken() {
    const token = document.querySelector('meta[name=csrf-token]');
    return token ? token.getAttribute('content') : '';
}

// Product management functions
function toggleProductStatus(productId, isActive) {
    fetch(`/api/products/${productId}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            is_active: isActive
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'وضعیت محصول به‌روزرسانی شد');
        } else {
            showAlert('error', 'خطا در به‌روزرسانی وضعیت محصول');
        }
    })
    .catch(error => {
        showAlert('error', 'خطا در ارتباط با سرور');
    });
}

function deleteProduct(productId, productName) {
    if (!confirm(`آیا مطمئن هستید که می‌خواهید محصول "${productName}" را حذف کنید؟`)) {
        return;
    }
    
    fetch(`/api/products/${productId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('success', 'محصول با موفقیت حذف شد');
            // Remove row from table
            const row = document.querySelector(`tr[data-product-id="${productId}"]`);
            if (row) {
                row.remove();
            }
        } else {
            showAlert('error', 'خطا در حذف محصول');
        }
    })
    .catch(error => {
        showAlert('error', 'خطا در ارتباط با سرور');
    });
}

// Site monitoring functions
function checkSiteStatus(siteName) {
    fetch(`/api/sites/${siteName}/status`)
    .then(response => response.json())
    .then(data => {
        updateSiteStatusDisplay(siteName, data);
    })
    .catch(error => {
        console.error(`Error checking ${siteName} status:`, error);
    });
}

function updateSiteStatusDisplay(siteName, statusData) {
    const statusElement = document.querySelector(`[data-site="${siteName}"] .status-indicator`);
    if (statusElement) {
        statusElement.className = `status-indicator ${statusData.available ? 'status-online' : 'status-offline'}`;
    }
    
    const lastUpdateElement = document.querySelector(`[data-site="${siteName}"] .last-update`);
    if (lastUpdateElement && statusData.last_success) {
        lastUpdateElement.textContent = new Date(statusData.last_success).toLocaleString('fa-IR');
    }
}

// Real-time updates using Server-Sent Events (if implemented)
function setupSSE() {
    if (typeof(EventSource) !== "undefined") {
        const source = new EventSource('/api/events');
        
        source.onmessage = function(event) {
            const data = JSON.parse(event.data);
            handleRealTimeUpdate(data);
        };
        
        source.onerror = function(event) {
            console.error('SSE error:', event);
        };
    }
}

function handleRealTimeUpdate(data) {
    switch (data.type) {
        case 'price_update':
            updateProductPrice(data.product_id, data.price);
            break;
        case 'scraping_status':
            updateScrapingStatus(data.site_name, data.status);
            break;
        case 'system_alert':
            showAlert('warning', data.message);
            break;
    }
}

// Pagination handling
function goToPage(page) {
    const url = new URL(window.location);
    url.searchParams.set('page', page);
    window.location.href = url.toString();
}

// Table sorting
function sortTable(column, direction) {
    const url = new URL(window.location);
    url.searchParams.set('sort_by', column);
    url.searchParams.set('sort_order', direction);
    window.location.href = url.toString();
}

// Theme switching
function toggleTheme() {
    const currentTheme = document.body.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Update charts if they exist
    Object.values(chartInstances).forEach(chart => {
        chart.options.plugins.legend.labels.color = newTheme === 'dark' ? '#ffffff' : '#666666';
        chart.update();
    });
}

// Print functionality
function printReport() {
    window.print();
}

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // Ctrl+R for refresh
    if (event.ctrlKey && event.key === 'r') {
        event.preventDefault();
        location.reload();
    }
    
    // Ctrl+S for save (if in form)
    if (event.ctrlKey && event.key === 's') {
        const form = document.querySelector('form');
        if (form) {
            event.preventDefault();
            form.submit();
        }
    }
    
    // Esc to close modals
    if (event.key === 'Escape') {
        const modal = document.querySelector('.modal.show');
        if (modal) {
            bootstrap.Modal.getInstance(modal).hide();
        }
    }
});

// Page visibility handling
document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // Page is hidden, pause auto-refresh
        if (autoRefreshInterval) {
            clearInterval(autoRefreshInterval);
        }
    } else {
        // Page is visible, resume auto-refresh
        startAutoRefresh();
    }
});

// Cleanup when page unloads
window.addEventListener('beforeunload', function() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    // Destroy chart instances
    Object.values(chartInstances).forEach(chart => {
        chart.destroy();
    });
});

console.log('📱 Dashboard JavaScript loaded successfully');
