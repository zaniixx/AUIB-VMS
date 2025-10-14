/**
 * Ticket Form JavaScript - Best Practices Implementation
 * Handles form validation, file uploads, progress tracking, and preview functionality
 */

(function() {
  'use strict';

  // Configuration
  const CONFIG = {
    maxFileSize: 10 * 1024 * 1024, // 10MB
    allowedFileTypes: [
      'text/plain',
      'application/pdf',
      'image/png',
      'image/jpeg',
      'image/gif',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/zip',
      'application/x-rar-compressed'
    ],
    maxDescriptionLength: 2000,
    maxTitleLength: 200
  };

  // DOM Elements
  const elements = {};

  // State management
  let state = {
    currentStep: 1,
    selectedFiles: [],
    isSubmitting: false
  };

  /**
   * Initialize the form when DOM is ready
   */
  function init() {
    cacheElements();
    setupEventListeners();
    setupFormValidation();
    setupFileUpload();
    setupCharacterCounters();
    setupPriorityIndicator();
    updateProgress();
    setupAccessibility();
  }

  /**
   * Cache DOM elements for performance
   */
  function cacheElements() {
    elements.form = document.getElementById('ticketForm');
    elements.submitBtn = document.getElementById('submitBtn');
    elements.previewBtn = document.getElementById('previewBtn');
    elements.previewModal = document.getElementById('previewModal');
    elements.previewContent = document.getElementById('previewContent');
    elements.previewClose = document.getElementById('previewClose');
    elements.editBtn = document.getElementById('editBtn');
    elements.confirmSubmitBtn = document.getElementById('confirmSubmitBtn');
    elements.fileUploadArea = document.getElementById('fileUploadArea');
    elements.fileList = document.getElementById('fileList');
    elements.attachmentsInput = document.getElementById('attachments');
    elements.titleInput = document.getElementById('title');
    elements.categorySelect = document.getElementById('category');
    elements.prioritySelect = document.getElementById('priority');
    elements.descriptionTextarea = document.getElementById('description');
    elements.progressFill = document.getElementById('progressFill');
    elements.priorityIndicator = document.getElementById('priorityIndicator');
  }

  /**
   * Setup all event listeners
   */
  function setupEventListeners() {
    // Form submission
    elements.form.addEventListener('submit', handleFormSubmit);

    // Preview functionality
    elements.previewBtn.addEventListener('click', showPreview);
    elements.previewClose.addEventListener('click', hidePreview);
    elements.editBtn.addEventListener('click', hidePreview);
    elements.confirmSubmitBtn.addEventListener('click', submitFromPreview);

    // Modal overlay click to close
    elements.previewModal.addEventListener('click', function(e) {
      if (e.target === elements.previewModal) {
        hidePreview();
      }
    });

    // Keyboard navigation
    document.addEventListener('keydown', handleKeyboardNavigation);

    // Priority change
    elements.prioritySelect.addEventListener('change', updatePriorityIndicator);

    // Step navigation (scroll-based)
    setupIntersectionObserver();
  }

  /**
   * Setup form validation
   */
  function setupFormValidation() {
    const inputs = elements.form.querySelectorAll('input, select, textarea');

    inputs.forEach(input => {
      input.addEventListener('blur', function() {
        validateField(this);
      });

      input.addEventListener('input', function() {
        if (this.classList.contains('is-invalid')) {
          validateField(this);
        }
      });
    });
  }

  /**
   * Setup file upload functionality
   */
  function setupFileUpload() {
    // Click to upload
    elements.fileUploadArea.addEventListener('click', () => {
      elements.attachmentsInput.click();
    });

    // Keyboard activation
    elements.fileUploadArea.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        elements.attachmentsInput.click();
      }
    });

    // Drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      elements.fileUploadArea.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      elements.fileUploadArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      elements.fileUploadArea.addEventListener(eventName, unhighlight, false);
    });

    elements.fileUploadArea.addEventListener('drop', handleDrop, false);
    elements.attachmentsInput.addEventListener('change', handleFileSelect);
  }

  /**
   * Setup character counters
   */
  function setupCharacterCounters() {
    setupCharacterCounter(elements.titleInput, CONFIG.maxTitleLength, 'titleCounter');
    setupCharacterCounter(elements.descriptionTextarea, CONFIG.maxDescriptionLength, 'descriptionCounter');
  }

  /**
   * Setup priority indicator
   */
  function setupPriorityIndicator() {
    updatePriorityIndicator();
  }

  /**
   * Setup accessibility features
   */
  function setupAccessibility() {
    // Ensure all form controls have proper labels
    const controls = elements.form.querySelectorAll('input, select, textarea');
    controls.forEach(control => {
      if (!control.getAttribute('aria-describedby') && control.hasAttribute('id')) {
        const helpId = control.id + 'Help';
        const helpElement = document.getElementById(helpId);
        if (helpElement) {
          control.setAttribute('aria-describedby', helpId);
        }
      }
    });

    // Add live region for dynamic content
    const liveRegion = document.createElement('div');
    liveRegion.setAttribute('aria-live', 'polite');
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.className = 'sr-only';
    liveRegion.id = 'liveRegion';
    document.body.appendChild(liveRegion);
  }

  /**
   * Setup intersection observer for step tracking
   */
  function setupIntersectionObserver() {
    const observerOptions = {
      threshold: 0.5,
      rootMargin: '-50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const step = parseInt(entry.target.id.replace('reviewSection', '3').replace('detailsSection', '2').replace('basicInfoSection', '1'));
          if (step && step !== state.currentStep) {
            state.currentStep = step;
            updateProgress();
          }
        }
      });
    }, observerOptions);

    // Observe form sections
    document.querySelectorAll('.form-section').forEach(section => {
      observer.observe(section);
    });
  }

  /**
   * Handle form submission
   */
  function handleFormSubmit(e) {
    if (!validateForm()) {
      e.preventDefault();
      focusFirstInvalidField();
      return false;
    }

    if (!state.isSubmitting) {
      state.isSubmitting = true;
      updateSubmitButton(true);
    }
  }

  /**
   * Show preview modal
   */
  function showPreview() {
    if (!validateForm()) {
      focusFirstInvalidField();
      return;
    }

    updatePreviewContent();
    elements.previewModal.hidden = false;
    elements.previewModal.setAttribute('aria-hidden', 'false');
    elements.editBtn.focus();

    // Announce to screen readers
    announceToScreenReader('Ticket preview opened');
  }

  /**
   * Hide preview modal
   */
  function hidePreview() {
    elements.previewModal.hidden = true;
    elements.previewModal.setAttribute('aria-hidden', 'true');
    elements.previewBtn.focus();

    // Announce to screen readers
    announceToScreenReader('Ticket preview closed');
  }

  /**
   * Submit form from preview
   */
  function submitFromPreview() {
    hidePreview();
    state.isSubmitting = true;
    updateSubmitButton(true);
    elements.form.submit();
  }

  /**
   * Handle keyboard navigation
   */
  function handleKeyboardNavigation(e) {
    if (e.key === 'Escape' && !elements.previewModal.hidden) {
      hidePreview();
    }
  }

  /**
   * Prevent default drag/drop behavior
   */
  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  /**
   * Highlight drag area
   */
  function highlight() {
    elements.fileUploadArea.classList.add('dragover');
  }

  /**
   * Unhighlight drag area
   */
  function unhighlight() {
    elements.fileUploadArea.classList.remove('dragover');
  }

  /**
   * Handle file drop
   */
  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
  }

  /**
   * Handle file selection
   */
  function handleFileSelect(e) {
    const files = e.target.files;
    handleFiles(files);
  }

  /**
   * Process selected files
   */
  function handleFiles(files) {
    [...files].forEach(file => {
      if (validateFile(file)) {
        state.selectedFiles.push(file);
      }
    });
    updateFileList();
    updateFileInput();
    announceFileCount();
  }

  /**
   * Validate individual file
   */
  function validateFile(file) {
    if (!CONFIG.allowedFileTypes.includes(file.type)) {
      showAlert(`File type not supported: ${file.name}`, 'error');
      return false;
    }

    if (file.size > CONFIG.maxFileSize) {
      showAlert(`File too large: ${file.name} (max 10MB)`, 'error');
      return false;
    }

    return true;
  }

  /**
   * Update file list display
   */
  function updateFileList() {
    elements.fileList.innerHTML = '';

    if (state.selectedFiles.length === 0) return;

    state.selectedFiles.forEach((file, index) => {
      const fileItem = createFileItem(file, index);
      elements.fileList.appendChild(fileItem);
    });
  }

  /**
   * Create file item element
   */
  function createFileItem(file, index) {
    const item = document.createElement('div');
    item.className = 'file-item';
    item.setAttribute('role', 'listitem');

    item.innerHTML = `
      <div class="file-info">
        <div class="file-icon">
          <i class="fas fa-${getFileIcon(file.type)}" aria-hidden="true"></i>
        </div>
        <div class="file-details">
          <p class="file-name">${escapeHtml(file.name)}</p>
          <p class="file-size">${formatFileSize(file.size)}</p>
        </div>
      </div>
      <button type="button" class="file-remove" onclick="removeFile(${index})"
              aria-label="Remove ${escapeHtml(file.name)}">
        <i class="fas fa-times" aria-hidden="true"></i>
      </button>
    `;

    return item;
  }

  /**
   * Update the hidden file input
   */
  function updateFileInput() {
    const dt = new DataTransfer();
    state.selectedFiles.forEach(file => dt.items.add(file));
    elements.attachmentsInput.files = dt.files;
  }

  /**
   * Remove file from selection
   */
  function removeFile(index) {
    const removedFile = state.selectedFiles[index];
    state.selectedFiles.splice(index, 1);
    updateFileList();
    updateFileInput();

    announceToScreenReader(`Removed file: ${removedFile.name}`);
  }

  // Make removeFile available globally for onclick handlers
  window.removeFile = removeFile;

  /**
   * Setup character counter for input
   */
  function setupCharacterCounter(input, maxLength, counterId) {
    const counter = document.getElementById(counterId);

    function updateCounter() {
      const length = input.value.length;
      counter.textContent = `${length}/${maxLength}`;

      // Update color based on usage
      counter.className = 'character-counter';
      if (length > maxLength) {
        counter.classList.add('error');
      } else if (length > maxLength * 0.9) {
        counter.classList.add('warning');
      }

      // Announce to screen readers for significant changes
      if (length === maxLength) {
        announceToScreenReader(`Character limit reached for ${input.name || input.id}`);
      }
    }

    input.addEventListener('input', updateCounter);
    updateCounter(); // Initial count
  }

  /**
   * Update priority indicator
   */
  function updatePriorityIndicator() {
    const priority = elements.prioritySelect.value;
    const indicator = elements.priorityIndicator;

    if (!priority) {
      indicator.innerHTML = '';
      indicator.removeAttribute('data-priority');
      return;
    }

    const priorityData = {
      low: { text: 'This will be addressed when time permits.', icon: 'arrow-down' },
      normal: { text: 'Standard response time applies.', icon: 'minus' },
      high: { text: 'This will be prioritized over normal issues.', icon: 'arrow-up' },
      urgent: { text: 'This requires immediate attention.', icon: 'exclamation-triangle' }
    };

    const data = priorityData[priority];
    indicator.innerHTML = `
      <i class="fas fa-${data.icon}" aria-hidden="true"></i>
      ${data.text}
    `;
    indicator.setAttribute('data-priority', priority);

    announceToScreenReader(`Priority set to ${priority}: ${data.text}`);
  }

  /**
   * Update progress indicator
   */
  function updateProgress() {
    const progress = ((state.currentStep - 1) / 3) * 100;
    elements.progressFill.style.width = `${progress}%`;

    // Update step indicators
    document.querySelectorAll('.progress-step').forEach((step, index) => {
      const stepNumber = index + 1;
      step.classList.toggle('active', stepNumber === state.currentStep);
      step.classList.toggle('completed', stepNumber < state.currentStep);
    });
  }

  /**
   * Validate individual field
   */
  function validateField(field) {
    const value = field.value.trim();
    const fieldName = field.name || field.id;
    let isValid = true;
    let errorMessage = '';

    switch (fieldName) {
      case 'title':
        if (!value) {
          isValid = false;
          errorMessage = 'Title is required.';
        } else if (value.length < 5) {
          isValid = false;
          errorMessage = 'Title must be at least 5 characters long.';
        } else if (value.length > CONFIG.maxTitleLength) {
          isValid = false;
          errorMessage = `Title must be less than ${CONFIG.maxTitleLength} characters.`;
        }
        break;

      case 'category':
        if (!value) {
          isValid = false;
          errorMessage = 'Please select a category.';
        }
        break;

      case 'priority':
        if (!value) {
          isValid = false;
          errorMessage = 'Please select a priority level.';
        }
        break;

      case 'description':
        if (!value) {
          isValid = false;
          errorMessage = 'Description is required.';
        } else if (value.length < 10) {
          isValid = false;
          errorMessage = 'Description must be at least 10 characters long.';
        } else if (value.length > CONFIG.maxDescriptionLength) {
          isValid = false;
          errorMessage = `Description must be less than ${CONFIG.maxDescriptionLength} characters.`;
        }
        break;
    }

    updateFieldValidationUI(field, isValid, errorMessage);
    return isValid;
  }

  /**
   * Update field validation UI
   */
  function updateFieldValidationUI(field, isValid, errorMessage) {
    const errorElement = document.getElementById(field.id + 'Error');

    field.classList.toggle('is-valid', isValid && field.value.trim());
    field.classList.toggle('is-invalid', !isValid);

    if (errorElement) {
      errorElement.textContent = errorMessage;
      errorElement.style.display = errorMessage ? 'block' : 'none';
    }
  }

  /**
   * Validate entire form
   */
  function validateForm() {
    const fields = ['title', 'category', 'priority', 'description'];
    let isValid = true;

    fields.forEach(fieldName => {
      const field = document.getElementById(fieldName);
      if (!validateField(field)) {
        isValid = false;
      }
    });

    return isValid;
  }

  /**
   * Focus first invalid field
   */
  function focusFirstInvalidField() {
    const firstInvalid = elements.form.querySelector('.is-invalid');
    if (firstInvalid) {
      firstInvalid.focus();
      firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  /**
   * Update preview content
   */
  function updatePreviewContent() {
    const title = elements.titleInput.value;
    const category = elements.categorySelect.options[elements.categorySelect.selectedIndex].text;
    const priority = elements.prioritySelect.value;
    const description = elements.descriptionTextarea.value;

    elements.previewContent.innerHTML = `
      <div class="preview-section">
        <div class="preview-label">Title</div>
        <div class="preview-value">${escapeHtml(title)}</div>
      </div>

      <div class="preview-section">
        <div class="preview-label">Category & Priority</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
          <div class="preview-value">${escapeHtml(category)}</div>
          <div class="preview-value priority" data-priority="${priority}">${escapeHtml(elements.prioritySelect.options[elements.prioritySelect.selectedIndex].text)}</div>
        </div>
      </div>

      <div class="preview-section">
        <div class="preview-label">Description</div>
        <div class="preview-value">${escapeHtml(description).replace(/\n/g, '<br>')}</div>
      </div>

      ${state.selectedFiles.length > 0 ? `
      <div class="preview-section">
        <div class="preview-label">Attachments (${state.selectedFiles.length})</div>
        <div class="preview-value">
          ${state.selectedFiles.map(file => `
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
              <i class="fas fa-${getFileIcon(file.type)}" aria-hidden="true"></i>
              <span>${escapeHtml(file.name)} (${formatFileSize(file.size)})</span>
            </div>
          `).join('')}
        </div>
      </div>
      ` : ''}
    `;
  }

  /**
   * Update submit button state
   */
  function updateSubmitButton(isLoading) {
    elements.submitBtn.disabled = isLoading;
    elements.confirmSubmitBtn.disabled = isLoading;

    if (isLoading) {
      elements.submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin" aria-hidden="true"></i> Submitting...';
      elements.confirmSubmitBtn.innerHTML = '<i class="fas fa-spinner fa-spin" aria-hidden="true"></i> Submitting...';
    } else {
      elements.submitBtn.innerHTML = '<i class="fas fa-paper-plane" aria-hidden="true"></i> Submit Ticket';
      elements.confirmSubmitBtn.innerHTML = '<i class="fas fa-paper-plane" aria-hidden="true"></i> Submit Ticket';
    }
  }

  /**
   * Show alert message
   */
  function showAlert(message, type = 'info') {
    const alertContainer = document.querySelector('.alert-container') || createAlertContainer();

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.setAttribute('role', 'alert');
    alert.innerHTML = `
      <div class="alert-icon">
        <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : 'info-circle'}" aria-hidden="true"></i>
      </div>
      <div class="alert-content">
        <p class="alert-message">${escapeHtml(message)}</p>
      </div>
      <button type="button" class="alert-close" onclick="this.parentElement.remove()" aria-label="Close alert">
        <i class="fas fa-times" aria-hidden="true"></i>
      </button>
    `;

    alertContainer.appendChild(alert);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
      if (alert.parentElement) {
        alert.remove();
      }
    }, 5000);
  }

  /**
   * Create alert container if it doesn't exist
   */
  function createAlertContainer() {
    const container = document.createElement('div');
    container.className = 'alert-container';
    elements.form.parentNode.insertBefore(container, elements.form);
    return container;
  }

  /**
   * Announce to screen readers
   */
  function announceToScreenReader(message) {
    const liveRegion = document.getElementById('liveRegion');
    if (liveRegion) {
      liveRegion.textContent = message;
    }
  }

  /**
   * Announce file count to screen readers
   */
  function announceFileCount() {
    const count = state.selectedFiles.length;
    const message = count === 1 ? '1 file selected' : `${count} files selected`;
    announceToScreenReader(message);
  }

  /**
   * Get file icon based on MIME type
   */
  function getFileIcon(mimeType) {
    if (mimeType.startsWith('image/')) return 'image';
    if (mimeType === 'application/pdf') return 'file-pdf';
    if (mimeType.includes('word')) return 'file-word';
    if (mimeType.includes('excel') || mimeType.includes('spreadsheet')) return 'file-excel';
    if (mimeType.includes('zip') || mimeType.includes('rar')) return 'file-archive';
    return 'file';
  }

  /**
   * Format file size
   */
  function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Escape HTML to prevent XSS
   */
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Export for testing (if needed)
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      validateField,
      validateForm,
      formatFileSize,
      getFileIcon
    };
  }

})();