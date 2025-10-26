/**
 * Ticket Form Application
 * Main entry point that coordinates all ticket form modules
 */

class TicketFormApp {
  constructor(options = {}) {
    this.options = {
      formSelector: options.formSelector || '#ticket-form',
      ...options
    };

    this.form = null;
    this.validator = null;
    this.uploader = null;
    this.ui = null;

    this.init();
  }

  init() {
    this.form = document.querySelector(this.options.formSelector);

    if (!this.form) {
      console.error('Ticket form not found');
      return;
    }

    this.initializeModules();
    this.bindEvents();
    this.loadSavedData();
  }

  initializeModules() {
    // Initialize validation
    this.validator = new TicketFormValidator(this.form);

    // Initialize file uploader
    const dropZone = this.form.querySelector('.file-upload-area');
    const fileInput = this.form.querySelector('#attachments');
    const fileList = this.form.querySelector('.file-list');

    if (dropZone && fileInput && fileList) {
      this.uploader = new FileUploader({
        dropZone: dropZone,
        fileInput: fileInput,
        fileList: fileList,
        maxFiles: 5,
        maxFileSize: 10 * 1024 * 1024, // 10MB
        allowedTypes: [
          'image/jpeg', 'image/png', 'image/gif', 'image/webp',
          'application/pdf',
          'text/plain',
          'application/msword',
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
      });
    }

    // Initialize UI
    this.ui = new TicketFormUI(this.form);
  }

  bindEvents() {
    // Form submission
    this.form.addEventListener('submit', (e) => this.handleSubmit(e));

    // Auto-save form data
    let autoSaveTimeout;
    this.form.addEventListener('input', () => {
      clearTimeout(autoSaveTimeout);
      autoSaveTimeout = setTimeout(() => this.saveFormData(), 1000);
    });

    // Handle browser back/forward
    window.addEventListener('popstate', (e) => {
      if (e.state && e.state.step) {
        this.ui.goToStep(e.state.step);
      }
    });

    // Handle beforeunload to warn about unsaved changes
    window.addEventListener('beforeunload', (e) => {
      if (this.hasUnsavedChanges()) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
      }
    });
  }

  handleSubmit(e) {
    e.preventDefault();

    if (this.validator.isValid()) {
      this.showLoadingState();

      // Simulate form submission (replace with actual API call)
      setTimeout(() => {
        this.handleSubmitSuccess();
      }, 2000);
    }
  }

  handleSubmitSuccess() {
    this.hideLoadingState();
    this.clearSavedData();
    this.ui.showSuccess();

    // Announce success to screen readers
    TicketFormUtils.A11y.announce('Ticket submitted successfully', 'assertive');
  }

  showLoadingState() {
    const submitBtn = this.form.querySelector('.btn-submit');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = '<span class="spinner"></span> Submitting...';
    }
  }

  hideLoadingState() {
    const submitBtn = this.form.querySelector('.btn-submit');
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = 'Submit Ticket';
    }
  }

  saveFormData() {
    const formData = TicketFormUtils.Form.serialize(this.form);
    const step = this.ui.getCurrentStep();

    const saveData = {
      formData: formData,
      step: step,
      timestamp: Date.now()
    };

    TicketFormUtils.Storage.set('ticket-form-draft', saveData);
  }

  loadSavedData() {
    const savedData = TicketFormUtils.Storage.get('ticket-form-draft');

    if (savedData && this.shouldRestoreData(savedData)) {
      // Restore form data
      Object.keys(savedData.formData).forEach(key => {
        const field = this.form.querySelector(`[name="${key}"]`);
        if (field && key !== 'attachments') {
          field.value = savedData.formData[key];
        }
      });

      // Restore step
      if (savedData.step) {
        this.ui.goToStep(savedData.step);
      }

      // Show restore message
      this.showRestoreMessage();
    }
  }

  shouldRestoreData(savedData) {
    // Don't restore if it's older than 24 hours
    const oneDay = 24 * 60 * 60 * 1000;
    return (Date.now() - savedData.timestamp) < oneDay;
  }

  showRestoreMessage() {
    const message = TicketFormUtils.DOM.createElement('div', {
      className: 'restore-message',
      innerHTML: `
        <div class="restore-icon">📝</div>
        <div class="restore-content">
          <strong>Draft restored</strong>
          <p>Your previous work has been restored. <button type="button" class="restore-dismiss">Dismiss</button></p>
        </div>
      `
    });

    const formContainer = this.form.closest('.ticket-form-container');
    formContainer.insertBefore(message, formContainer.firstChild);

    // Auto-dismiss after 10 seconds or on button click
    const dismissBtn = message.querySelector('.restore-dismiss');
    dismissBtn.addEventListener('click', () => message.remove());

    setTimeout(() => {
      if (message.parentNode) {
        message.remove();
      }
    }, 10000);
  }

  clearSavedData() {
    TicketFormUtils.Storage.remove('ticket-form-draft');
  }

  hasUnsavedChanges() {
    const savedData = TicketFormUtils.Storage.get('ticket-form-draft');
    if (!savedData) return false;

    const currentData = TicketFormUtils.Form.serialize(this.form);
    return TicketFormUtils.Form.hasChanges(this.form, savedData.formData);
  }

  // Public API methods
  reset() {
    TicketFormUtils.Form.resetWithConfirmation(this.form);
    this.clearSavedData();
    this.ui.goToStep(1);
  }

  getFormData() {
    return TicketFormUtils.Form.serialize(this.form);
  }

  isValid() {
    return this.validator.isValid();
  }

  getErrors() {
    return this.validator.getErrors();
  }

  destroy() {
    // Clean up event listeners and modules
    if (this.validator) {
      // Validator cleanup if needed
    }

    if (this.uploader) {
      this.uploader.clearFiles();
    }

    if (this.ui) {
      // UI cleanup if needed
    }

    // Clear saved data
    this.clearSavedData();
  }
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Check if ticket form exists on the page
  if (document.querySelector('#ticket-form')) {
    window.ticketFormApp = new TicketFormApp();
  }
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TicketFormApp;
}

// Make available globally
window.TicketFormApp = TicketFormApp;