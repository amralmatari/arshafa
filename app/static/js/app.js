/**
 * Arshafa Document Management System
 * Main JavaScript Application
 */

// Set moment.js locale to Arabic
moment.locale('ar');

// Global application object
const App = {
    // Configuration
    config: {
        maxFileSize: 100 * 1024 * 1024, // 100MB
        allowedExtensions: ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'jpg', 'jpeg', 'png', 'gif'],
        searchDelay: 300 // milliseconds
    },
    
    // Initialize application
    init: function() {
        this.formatDates();
        this.initFileUpload();
        this.initSearch();
        this.initDatePickers();
        this.initConfirmDialogs();
        this.convertMomentNumbersToHindu();
    },
    
    // Initialize Bootstrap tooltips
    initTooltips: function() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },
    
    // Initialize file upload functionality
    initFileUpload: function() {
        const uploadAreas = document.querySelectorAll('.upload-area');
        
        uploadAreas.forEach(area => {
            const fileInput = area.querySelector('input[type="file"]');
            
            // Click to upload
            area.addEventListener('click', () => {
                if (fileInput) fileInput.click();
            });
            
            // Drag and drop
            area.addEventListener('dragover', (e) => {
                e.preventDefault();
                area.classList.add('dragover');
            });
            
            area.addEventListener('dragleave', () => {
                area.classList.remove('dragover');
            });
            
            area.addEventListener('drop', (e) => {
                e.preventDefault();
                area.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                if (files.length > 0 && fileInput) {
                    fileInput.files = files;
                    this.handleFileSelection(fileInput);
                }
            });
            
            // File input change
            if (fileInput) {
                fileInput.addEventListener('change', () => {
                    this.handleFileSelection(fileInput);
                });
            }
        });
    },
    
    // Handle file selection
    handleFileSelection: function(input) {
        const files = input.files;
        const preview = document.getElementById('file-preview');
        
        if (files.length === 0) return;
        
        const file = files[0];
        
        // Validate file size
        if (file.size > this.config.maxFileSize) {
            this.showAlert('حجم الملف كبير. الحد الأقصى المسموح هو 100 ميجابايت.', 'error');
            input.value = '';
            return;
        }
        
        // Validate file extension
        const extension = file.name.split('.').pop().toLowerCase();
        if (!this.config.allowedExtensions.includes(extension)) {
            this.showAlert('نوع الملف غير مدعوم.', 'error');
            input.value = '';
            return;
        }
        
        // Show file preview
        if (preview) {
            preview.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-file me-2"></i>
                    <strong>${file.name}</strong>
                    <br>
                    <small>الحجم: ${this.formatFileSize(file.size)}</small>
                </div>
            `;
        }
    },
    
    // Initialize search functionality
    initSearch: function() {
        const searchInput = document.getElementById('search-input');
        const searchResults = document.getElementById('search-results');
        let searchTimeout;
        
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                const query = e.target.value.trim();
                
                if (query.length >= 2) {
                    searchTimeout = setTimeout(() => {
                        this.performSearch(query);
                    }, this.config.searchDelay);
                } else if (searchResults) {
                    searchResults.innerHTML = '';
                }
            });
        }
        
        // Advanced search toggle
        const advancedToggle = document.getElementById('advanced-search-toggle');
        const advancedForm = document.getElementById('advanced-search-form');
        
        if (advancedToggle && advancedForm) {
            advancedToggle.addEventListener('click', () => {
                advancedForm.classList.toggle('d-none');
                const icon = advancedToggle.querySelector('i');
                icon.classList.toggle('fa-chevron-down');
                icon.classList.toggle('fa-chevron-up');
            });
        }
    },
    
    // Perform AJAX search
    performSearch: function(query) {
        const searchResults = document.getElementById('search-results');
        if (!searchResults) return;
        
        // Show loading
        searchResults.innerHTML = '<div class="text-center"><div class="loading-spinner"></div> جاري البحث...</div>';
        
        fetch(`/api/search?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.displaySearchResults(data.results);
                } else {
                    searchResults.innerHTML = '<div class="alert alert-warning">حدث خطأ أثناء البحث</div>';
                }
            })
            .catch(error => {
                console.error('Search error:', error);
                searchResults.innerHTML = '<div class="alert alert-danger">حدث خطأ أثناء البحث</div>';
            });
    },
    
    // Display search results
    displaySearchResults: function(results) {
        const searchResults = document.getElementById('search-results');
        if (!searchResults) return;
        
        if (results.length === 0) {
            searchResults.innerHTML = '<div class="alert alert-info">لم يتم العثور على نتائج</div>';
            return;
        }
        
        let html = '<div class="list-group">';
        results.forEach(result => {
            html += `
                <a href="/documents/${result.id}" class="list-group-item list-group-item-action">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">${result.title}</h6>
                        <small>${moment(result.created_at).fromNow()}</small>
                    </div>
                    <p class="mb-1">${result.description || ''}</p>
                    <small>الفئة: ${result.category || 'غير محدد'}</small>
                </a>
            `;
        });
        html += '</div>';
        
        searchResults.innerHTML = html;
    },
    
    // Initialize date pickers
    initDatePickers: function() {
        const dateInputs = document.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            // Set Arabic locale for date inputs if supported
            if (input.lang !== 'ar') {
                input.lang = 'ar';
            }
        });
    },
    
    // Initialize confirmation dialogs
    initConfirmDialogs: function() {
        const confirmButtons = document.querySelectorAll('[data-confirm]');
        
        confirmButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const message = button.getAttribute('data-confirm');
                if (!confirm(message)) {
                    e.preventDefault();
                }
            });
        });
    },
    
    // Initialize auto-save functionality
    initAutoSave: function() {
        const autoSaveForms = document.querySelectorAll('[data-autosave]');
        
        autoSaveForms.forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            let saveTimeout;
            
            inputs.forEach(input => {
                input.addEventListener('input', () => {
                    clearTimeout(saveTimeout);
                    saveTimeout = setTimeout(() => {
                        this.autoSaveForm(form);
                    }, 2000); // Auto-save after 2 seconds of inactivity
                });
            });
        });
    },
    
    // Auto-save form data
    autoSaveForm: function(form) {
        const formData = new FormData(form);
        const url = form.getAttribute('data-autosave-url') || form.action;
        
        fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Auto-Save': 'true'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showToast('تم حفظ التغييرات تلقائ', 'success');
            }
        })
        .catch(error => {
            console.error('Auto-save error:', error);
        });
    },
    
    // تحويل الأرقام في عناصر moment بعد تحميل الصفحة
    convertMomentNumbersToHindu: function() {
        // انتظر قليلاً لضمان تحميل جميع عناصر moment
        setTimeout(() => {
            const momentElements = document.querySelectorAll('.moment');
            momentElements.forEach(element => {
                if (element.textContent) {
                    element.textContent = this.toHinduNumerals(element.textContent);
                }
            });
        }, 100);
    },

    // تحويل الأرقام العربية إلى أرقام هندية
    toHinduNumerals: function(str) {
        if (!str) return str;
        return str.replace(/[0-9]/g, function(d) {
            return String.fromCharCode(d.charCodeAt(0) + 1584); // تحويل الأرقام العربية إلى هندية
        });
    },
    
    // Format dates using moment.js
    formatDates: function() {
        // تعيين اللغة العربية
        moment.locale('ar');
        
        // تنسيق جميع التواريخ المعروضة بواسطة Flask-Moment
        const momentElements = document.querySelectorAll('[data-moment]');
        momentElements.forEach(element => {
            // تحويل النص إلى أرقام هندية
            if (element.textContent) {
                element.textContent = this.toHinduNumerals(element.textContent);
            }
        });
    },
    
    // Utility functions
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 بايت';
        
        const k = 1024;
        const sizes = ['بايت', 'كيلوبايت', 'ميجابايت', 'جيجابايت'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // Show alert message
    showAlert: function(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container') || document.body;
        const alertId = 'alert-' + Date.now();
        
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertContainer.insertAdjacentHTML('afterbegin', alertHtml);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    },
    
    // Show toast notification
    showToast: function(message, type = 'info') {
        // Create toast container if it doesn't exist
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast" role="alert">
                <div class="toast-header">
                    <i class="fas fa-info-circle text-${type === 'error' ? 'danger' : type} me-2"></i>
                    <strong class="me-auto">إشعار</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement);
        toast.show();
        
        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    }
};

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    App.init();
});

// Export for global access
window.App = App;







