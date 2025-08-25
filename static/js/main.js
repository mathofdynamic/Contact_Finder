/**
 * Contact Finder Web Interface - JavaScript
 * Handles file uploads, real-time updates, and UI interactions
 */

class ContactFinderApp {
    constructor() {
        this.socket = null;
        this.currentSessionId = null;
        this.isProcessing = false;
        this.uploadedFile = null;
        
        this.initializeApp();
        this.setupEventListeners();
        this.connectWebSocket();
    }

    /**
     * Initialize the application
     */
    initializeApp() {
        console.log('🚀 Contact Finder App Initialized');
        this.showToast('Welcome to Contact Finder!', 'info');
    }

    /**
     * Setup event listeners for UI interactions
     */
    setupEventListeners() {
        // File input change
        const fileInput = document.getElementById('fileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
        }

        // Drag and drop functionality
        const uploadArea = document.getElementById('uploadArea');
        if (uploadArea) {
            uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
            uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
            uploadArea.addEventListener('drop', (e) => this.handleFileDrop(e));
        }

        // Scroll log container to bottom when new messages arrive
        this.setupLogAutoScroll();
    }

    /**
     * Connect to WebSocket for real-time updates
     */
    connectWebSocket() {
        try {
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('✅ WebSocket connected');
                this.showToast('Connected to server', 'success');
            });

            this.socket.on('disconnect', () => {
                console.log('❌ WebSocket disconnected');
                this.showToast('Disconnected from server', 'warning');
            });

            this.socket.on('progress_update', (data) => {
                this.handleProgressUpdate(data);
            });

            this.socket.on('result_update', (data) => {
                this.handleResultUpdate(data);
            });

            this.socket.on('log_message', (data) => {
                this.handleLogMessage(data);
            });

            this.socket.on('processing_complete', (data) => {
                this.handleProcessingComplete(data);
            });

            this.socket.on('processing_paused', (data) => {
                this.handleProcessingPaused(data);
            });

        } catch (error) {
            console.error('❌ WebSocket connection failed:', error);
            this.showToast('Failed to connect to server', 'error');
        }
    }

    /**
     * Handle file selection
     */
    async handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            await this.processFile(file);
        }
    }

    /**
     * Handle drag over event
     */
    handleDragOver(event) {
        event.preventDefault();
        event.stopPropagation();
        event.currentTarget.classList.add('drag-over');
    }

    /**
     * Handle drag leave event
     */
    handleDragLeave(event) {
        event.preventDefault();
        event.stopPropagation();
        event.currentTarget.classList.remove('drag-over');
    }

    /**
     * Handle file drop
     */
    async handleFileDrop(event) {
        event.preventDefault();
        event.stopPropagation();
        event.currentTarget.classList.remove('drag-over');
        
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            await this.processFile(files[0]);
        }
    }

    /**
     * Process uploaded file
     */
    async processFile(file) {
        // Validate file
        if (!this.validateFile(file)) {
            return;
        }

        this.uploadedFile = file;
        this.showLoadingOverlay(true);

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.currentSessionId = result.session_id;
                this.displayFilePreview(file, result);
                this.showToast(`File uploaded successfully! ${result.total_companies} companies detected.`, 'success');
            } else {
                throw new Error(result.error || 'Upload failed');
            }

        } catch (error) {
            console.error('❌ Upload error:', error);
            this.showToast(`Upload failed: ${error.message}`, 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    /**
     * Validate uploaded file
     */
    validateFile(file) {
        const allowedTypes = ['text/csv', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
        const maxSize = 16 * 1024 * 1024; // 16MB

        if (!allowedTypes.includes(file.type) && !file.name.match(/\.(csv|xlsx|xls)$/i)) {
            this.showToast('Please upload a CSV, XLSX, or XLS file only.', 'error');
            return false;
        }

        if (file.size > maxSize) {
            this.showToast('File size must be less than 16MB.', 'error');
            return false;
        }

        return true;
    }

    /**
     * Display file preview with company list
     */
    displayFilePreview(file, uploadResult) {
        // Hide upload area and show preview
        document.getElementById('uploadArea').classList.add('hidden');
        const filePreview = document.getElementById('filePreview');
        filePreview.classList.remove('hidden');

        // Update file info
        document.getElementById('fileName').textContent = file.name;
        document.getElementById('fileStats').textContent = `${uploadResult.total_companies} companies detected from column: ${uploadResult.detected_column}`;

        // Display companies preview
        const previewList = document.getElementById('companiesPreviewList');
        previewList.innerHTML = '';
        uploadResult.companies_preview.forEach(company => {
            const li = document.createElement('li');
            li.textContent = company;
            previewList.appendChild(li);
        });

        // Show "and X more..." if there are more companies
        if (uploadResult.total_companies > uploadResult.companies_preview.length) {
            const li = document.createElement('li');
            li.textContent = `... and ${uploadResult.total_companies - uploadResult.companies_preview.length} more`;
            li.style.fontStyle = 'italic';
            li.style.color = '#6b7280';
            previewList.appendChild(li);
        }
    }

    /**
     * Start processing companies
     */
    async startProcessing() {
        if (!this.currentSessionId) {
            this.showToast('No session found. Please upload a file first.', 'error');
            return;
        }

        try {
            this.showLoadingOverlay(true, 'Starting processing...');

            const response = await fetch(`/start_processing/${this.currentSessionId}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.isProcessing = true;
                this.showProcessingSection();
                this.showToast('Processing started!', 'success');
                
                // Join WebSocket session for real-time updates
                if (this.socket) {
                    this.socket.emit('join_session', { session_id: this.currentSessionId });
                }
            } else {
                throw new Error(result.error || 'Failed to start processing');
            }

        } catch (error) {
            console.error('❌ Start processing error:', error);
            this.showToast(`Failed to start processing: ${error.message}`, 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }

    /**
     * Pause processing
     */
    async pauseProcessing() {
        if (!this.currentSessionId) return;

        try {
            const response = await fetch(`/pause_processing/${this.currentSessionId}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.showToast('Processing will pause after current company...', 'info');
                document.getElementById('pauseBtn').classList.add('hidden');
                document.getElementById('resumeBtn').classList.remove('hidden');
            } else {
                throw new Error(result.error || 'Failed to pause processing');
            }

        } catch (error) {
            console.error('❌ Pause processing error:', error);
            this.showToast(`Failed to pause processing: ${error.message}`, 'error');
        }
    }

    /**
     * Resume processing
     */
    async resumeProcessing() {
        if (!this.currentSessionId) return;

        try {
            const response = await fetch(`/start_processing/${this.currentSessionId}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.isProcessing = true;
                this.showToast('Processing resumed!', 'success');
                document.getElementById('pauseBtn').classList.remove('hidden');
                document.getElementById('resumeBtn').classList.add('hidden');
            } else {
                throw new Error(result.error || 'Failed to resume processing');
            }

        } catch (error) {
            console.error('❌ Resume processing error:', error);
            this.showToast(`Failed to resume processing: ${error.message}`, 'error');
        }
    }

    /**
     * Download results CSV
     */
    async downloadResults() {
        if (!this.currentSessionId) return;

        try {
            const response = await fetch(`/download_results/${this.currentSessionId}`);
            
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `contact_finder_results_${this.currentSessionId}.csv`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                this.showToast('Results downloaded successfully!', 'success');
            } else {
                const errorResult = await response.json();
                throw new Error(errorResult.error || 'Download failed');
            }

        } catch (error) {
            console.error('❌ Download error:', error);
            this.showToast(`Download failed: ${error.message}`, 'error');
        }
    }

    /**
     * Show processing section and hide welcome section
     */
    showProcessingSection() {
        document.getElementById('welcomeSection').classList.add('hidden');
        document.getElementById('processingSection').classList.remove('hidden');
        
        // Initialize progress display
        this.updateProgressDisplay({
            processed: 0,
            total: 0,
            percentage: 0,
            current_company: 'Initializing...'
        });
    }

    /**
     * Handle progress update from WebSocket
     */
    handleProgressUpdate(data) {
        if (data.session_id === this.currentSessionId) {
            this.updateProgressDisplay(data);
        }
    }

    /**
     * Update progress display
     */
    updateProgressDisplay(data) {
        // Update progress percentage and bar
        const percentage = data.percentage || 0;
        document.getElementById('progressPercentage').textContent = `${percentage}%`;
        document.getElementById('progressFill').style.width = `${percentage}%`;

        // Update stats
        document.getElementById('processedCount').textContent = data.processed || 0;
        document.getElementById('remainingCount').textContent = (data.total - data.processed) || 0;

        // Update current company
        document.getElementById('currentCompany').textContent = data.current_company || 'Waiting...';
    }

    /**
     * Handle result update from WebSocket
     */
    handleResultUpdate(data) {
        if (data.session_id === this.currentSessionId) {
            this.addResultToTable(data);
            this.updateResultStats(data.status);
        }
    }

    /**
     * Add result to results table
     */
    addResultToTable(data) {
        const tableBody = document.getElementById('resultsTableBody');
        const row = document.createElement('tr');
        row.classList.add('new-row');

        const result = data.result || {};
        const companyData = result.company_website_data || {};
        const detailedInfo = data.detailed_info || {};

        // Format data for display using enhanced information
        const emails = detailedInfo.emails_found ? detailedInfo.emails_found.slice(0, 3).join(', ') + 
                      (detailedInfo.emails_found.length > 3 ? '...' : '') : 'None';
        const phones = detailedInfo.phones_found ? detailedInfo.phones_found.slice(0, 2).join(', ') +
                      (detailedInfo.phones_found.length > 2 ? '...' : '') : 'None';
        const socialPlatforms = detailedInfo.social_links_found ? detailedInfo.social_links_found.join(', ') : 'None';
        
        // CEO profiles with better formatting
        const ceoLinkedIn = detailedInfo.linkedin_url || '';
        const ceoTwitter = detailedInfo.twitter_url || '';
        const ceoProfilesCount = detailedInfo.ceo_profiles_count || 0;

        // Status badge
        const statusClass = data.status === 'success' ? 'success' : 'error';
        const statusIcon = data.status === 'success' ? 'fas fa-check' : 'fas fa-times';
        const statusText = data.status === 'success' ? 'Success' : 'Failed';

        row.innerHTML = `
            <td><strong>${data.company}</strong></td>
            <td>
                <span class="status-badge ${statusClass}">
                    <i class="${statusIcon}"></i>
                    ${statusText}
                </span>
            </td>
            <td title="${emails}">${emails}</td>
            <td title="${phones}">${phones}</td>
            <td title="${socialPlatforms}">${socialPlatforms}</td>
            <td>
                ${ceoLinkedIn ? `<a href="${ceoLinkedIn}" target="_blank" rel="noopener" title="${ceoLinkedIn}"><i class="fab fa-linkedin"></i> LinkedIn</a>` : '<span class="text-muted">None</span>'}
            </td>
            <td>
                ${ceoTwitter ? `<a href="${ceoTwitter}" target="_blank" rel="noopener" title="${ceoTwitter}"><i class="fab fa-twitter"></i> Twitter</a>` : '<span class="text-muted">None</span>'}
            </td>
            <td>
                <span class="badge badge-info">${ceoProfilesCount} CEO profiles</span>
                ${data.status === 'success' ? '<button class="btn btn-sm btn-outline ml-2" onclick="app.viewDetails(\'' + (result.company_domain || data.company) + '\')" title="View Details"><i class="fas fa-eye"></i></button>' : ''}
            </td>
        `;

        tableBody.appendChild(row);

        // Auto-scroll to new row
        row.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    /**
     * Format social links for display
     */
    formatSocialLinks(socialLinks) {
        if (!socialLinks || Object.keys(socialLinks).length === 0) {
            return '';
        }

        const links = [];
        for (const [platform, url] of Object.entries(socialLinks)) {
            if (url) {
                links.push(`<a href="${url}" target="_blank" rel="noopener">${platform}</a>`);
            }
        }

        return links.join(', ');
    }

    /**
     * Update result statistics
     */
    updateResultStats(status) {
        if (status === 'success') {
            const successCount = document.getElementById('successCount');
            successCount.textContent = parseInt(successCount.textContent) + 1;
        } else {
            const errorCount = document.getElementById('errorCount');
            errorCount.textContent = parseInt(errorCount.textContent) + 1;
        }
    }

    /**
     * Handle log message from WebSocket
     */
    handleLogMessage(data) {
        if (data.session_id === this.currentSessionId) {
            this.addLogMessage(data);
        }
    }

    /**
     * Add log message to log container
     */
    addLogMessage(data) {
        const logContainer = document.getElementById('logContainer');
        const logMessage = document.createElement('div');
        logMessage.classList.add('log-message', data.type || 'info');

        logMessage.innerHTML = `
            <span class="log-timestamp">[${data.timestamp}]</span>
            ${data.message}
        `;

        logContainer.appendChild(logMessage);
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    /**
     * Handle processing complete event
     */
    handleProcessingComplete(data) {
        if (data.session_id === this.currentSessionId) {
            this.isProcessing = false;
            
            // Hide pause button, show download button
            document.getElementById('pauseBtn').classList.add('hidden');
            document.getElementById('resumeBtn').classList.add('hidden');
            
            if (data.csv_available) {
                document.getElementById('downloadBtn').disabled = false;
            }

            // Update current processing status
            document.getElementById('currentCompany').innerHTML = '<i class="fas fa-check"></i> Processing Complete!';

            this.showToast(`Processing completed! ${data.success_count} successful, ${data.error_count} errors`, 'success');
        }
    }

    /**
     * Handle processing paused event
     */
    handleProcessingPaused(data) {
        if (data.session_id === this.currentSessionId) {
            this.isProcessing = false;
            this.showToast('Processing paused', 'info');
            
            // Update current processing status
            document.getElementById('currentCompany').innerHTML = '<i class="fas fa-pause"></i> Processing Paused';
        }
    }

    /**
     * Setup auto-scroll for log container
     */
    setupLogAutoScroll() {
        const logContainer = document.getElementById('logContainer');
        if (logContainer) {
            const observer = new MutationObserver(() => {
                logContainer.scrollTop = logContainer.scrollHeight;
            });
            observer.observe(logContainer, { childList: true });
        }
    }

    /**
     * Remove uploaded file and reset interface
     */
    removeFile() {
        this.uploadedFile = null;
        this.currentSessionId = null;
        
        // Reset file input
        document.getElementById('fileInput').value = '';
        
        // Show upload area, hide preview
        document.getElementById('uploadArea').classList.remove('hidden');
        document.getElementById('filePreview').classList.add('hidden');
        
        // Hide processing section, show welcome
        document.getElementById('processingSection').classList.add('hidden');
        document.getElementById('welcomeSection').classList.remove('hidden');
        
        this.showToast('File removed', 'info');
    }

    /**
     * Show/hide loading overlay
     */
    showLoadingOverlay(show, message = 'Processing your file...') {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.querySelector('h3').textContent = message;
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info', duration = 5000) {
        const toastContainer = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.classList.add('toast', type);

        const icons = {
            info: 'fas fa-info-circle',
            success: 'fas fa-check-circle',
            warning: 'fas fa-exclamation-triangle',
            error: 'fas fa-times-circle'
        };

        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <i class="${icons[type] || icons.info}"></i>
                <span>${message}</span>
            </div>
        `;

        toastContainer.appendChild(toast);

        // Auto-remove toast after duration
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, duration);

        // Remove on click
        toast.addEventListener('click', () => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        });
    }

    /**
     * View detailed results for a company
     */
    async viewDetails(companyIdentifier) {
        if (!this.currentSessionId) {
            this.showToast('No session found', 'error');
            return;
        }
        
        try {
            // Extract domain from URL if it's a full URL
            let searchTerm = companyIdentifier;
            if (companyIdentifier.includes('://')) {
                const url = new URL(companyIdentifier);
                searchTerm = url.hostname.replace('www.', '');
            }
            
            this.showLoadingOverlay(true, `Loading details for ${searchTerm}...`);
            
            const response = await fetch(`/company_details/${this.currentSessionId}/${searchTerm}`);
            const result = await response.json();
            
            if (result.success) {
                this.showCompanyDetailsModal(result);
            } else {
                throw new Error(result.error || 'Failed to load company details');
            }
            
        } catch (error) {
            console.error('❌ Error loading company details:', error);
            this.showToast(`Failed to load details: ${error.message}`, 'error');
        } finally {
            this.showLoadingOverlay(false);
        }
    }
    
    /**
     * Show company details in a modal
     */
    showCompanyDetailsModal(companyData) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.id = 'companyDetailsModal';
        
        const details = companyData.details;
        
        // Build content sections
        let contentSections = [];
        
        // Company Info Section
        contentSections.push(`
            <div class="detail-section">
                <h4><i class="fas fa-building"></i> Company Information</h4>
                <div class="detail-item">
                    <strong>Company:</strong> ${companyData.company_name}
                </div>
                <div class="detail-item">
                    <strong>Website:</strong> <a href="${companyData.company_domain}" target="_blank" rel="noopener">${companyData.company_domain}</a>
                </div>
                <div class="detail-item">
                    <strong>Processed:</strong> ${companyData.timestamp}
                </div>
                <div class="detail-item">
                    <strong>Status:</strong> <span class="status-badge ${companyData.processing_status.toLowerCase()}">${companyData.processing_status}</span>
                </div>
            </div>
        `);
        
        // Emails Section
        if (details.emails && details.emails.length > 0) {
            const emailLinks = details.emails.map(email => 
                `<a href="mailto:${email}" target="_blank" rel="noopener" class="link-item"><i class="fas fa-envelope"></i> ${email}</a>`
            ).join('');
            contentSections.push(`
                <div class="detail-section">
                    <h4><i class="fas fa-envelope"></i> Email Addresses (${details.emails.length})</h4>
                    <div class="links-grid">${emailLinks}</div>
                </div>
            `);
        }
        
        // Phone Numbers Section
        if (details.phones && details.phones.length > 0) {
            const phoneLinks = details.phones.map(phone => 
                `<a href="tel:${phone}" target="_blank" rel="noopener" class="link-item"><i class="fas fa-phone"></i> ${phone}</a>`
            ).join('');
            contentSections.push(`
                <div class="detail-section">
                    <h4><i class="fas fa-phone"></i> Phone Numbers (${details.phones.length})</h4>
                    <div class="links-grid">${phoneLinks}</div>
                </div>
            `);
        }
        
        // Website Social Links Section
        if (details.website_social_links && Object.keys(details.website_social_links).length > 0) {
            const socialLinks = Object.entries(details.website_social_links).map(([platform, url]) => {
                const icon = this.getSocialIcon(platform);
                return `<a href="${url}" target="_blank" rel="noopener" class="link-item"><i class="${icon}"></i> ${platform.charAt(0).toUpperCase() + platform.slice(1)}</a>`;
            }).join('');
            contentSections.push(`
                <div class="detail-section">
                    <h4><i class="fas fa-share-alt"></i> Website Social Links (${Object.keys(details.website_social_links).length})</h4>
                    <div class="links-grid">${socialLinks}</div>
                </div>
            `);
        }
        
        // CEO Profiles Section
        if (details.ceo_profiles && Object.keys(details.ceo_profiles).length > 0) {
            const ceoLinks = Object.entries(details.ceo_profiles).map(([platform, profileData]) => {
                const icon = this.getSocialIcon(platform);
                const name = profileData.name || 'CEO Profile';
                const headline = profileData.headline || 'Profile found via Google search';
                return `
                    <a href="${profileData.url}" target="_blank" rel="noopener" class="link-item ceo-profile">
                        <div class="profile-info">
                            <div class="profile-header">
                                <i class="${icon}"></i>
                                <span class="platform-name">${platform.charAt(0).toUpperCase() + platform.slice(1)}</span>
                            </div>
                            <div class="profile-name">${name}</div>
                            <div class="profile-headline">${headline}</div>
                        </div>
                    </a>
                `;
            }).join('');
            contentSections.push(`
                <div class="detail-section">
                    <h4><i class="fas fa-user-tie"></i> CEO Profiles (${Object.keys(details.ceo_profiles).length})</h4>
                    <div class="links-grid ceo-profiles">${ceoLinks}</div>
                </div>
            `);
        }
        
        // No data found message
        if (contentSections.length === 1) { // Only company info section
            contentSections.push(`
                <div class="detail-section no-data">
                    <div class="no-data-message">
                        <i class="fas fa-info-circle"></i>
                        <p>No contact information or CEO profiles were found for this company.</p>
                    </div>
                </div>
            `);
        }
        
        modal.innerHTML = `
            <div class="modal-content company-details-modal">
                <div class="modal-header">
                    <h3><i class="fas fa-info-circle"></i> Company Details</h3>
                    <button onclick="this.closest('.modal').remove()" class="btn-close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    ${contentSections.join('')}
                </div>
                <div class="modal-footer">
                    <button onclick="this.closest('.modal').remove()" class="btn btn-outline">
                        <i class="fas fa-times"></i> Close
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
    
    /**
     * Get appropriate icon for social platform
     */
    getSocialIcon(platform) {
        const iconMap = {
            'linkedin': 'fab fa-linkedin',
            'twitter': 'fab fa-twitter',
            'x': 'fab fa-x-twitter',
            'instagram': 'fab fa-instagram',
            'facebook': 'fab fa-facebook',
            'tiktok': 'fab fa-tiktok',
            'youtube': 'fab fa-youtube',
            'github': 'fab fa-github',
            'medium': 'fab fa-medium',
            'telegram': 'fab fa-telegram',
            'discord': 'fab fa-discord',
            'snapchat': 'fab fa-snapchat',
            'pinterest': 'fab fa-pinterest',
            'reddit': 'fab fa-reddit',
            'tumblr': 'fab fa-tumblr',
            'whatsapp': 'fab fa-whatsapp'
        };
        
        return iconMap[platform.toLowerCase()] || 'fas fa-link';
    }
}

// Global functions for HTML onclick handlers
function startProcessing() {
    app.startProcessing();
}

function pauseProcessing() {
    app.pauseProcessing();
}

function resumeProcessing() {
    app.resumeProcessing();
}

function downloadResults() {
    app.downloadResults();
}

function removeFile() {
    app.removeFile();
}

function showHelp() {
    document.getElementById('helpModal').classList.remove('hidden');
}

function hideHelp() {
    document.getElementById('helpModal').classList.add('hidden');
}

// Initialize app when DOM is loaded
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new ContactFinderApp();
});

// Handle page unload - disconnect WebSocket
window.addEventListener('beforeunload', () => {
    if (app && app.socket) {
        app.socket.disconnect();
    }
});