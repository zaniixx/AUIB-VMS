/**
 * UI Module for Ticket Form
 * Handles progress indicators, modals, and UI interactions
 */

class TicketFormUI {
  constructor(form) {
    this.form = form;
    this.currentStep = 1;
    this.totalSteps = 3;
    this.modal = null;

    this.init();
  }

  init() {
    this.setupProgressIndicator();
    this.setupFormSteps();
    this.setupModal();
    this.setupCharacterCounters();
    this.setupPriorityIndicator();
    this.bindEvents();
  }

  setupProgressIndicator() {
    this.progressContainer = this.form.querySelector('.progress-container');
    this.progressSteps = this.form.querySelectorAll('.progress-step');
    this.progressFill = this.form.querySelector('.progress-fill');

    this.updateProgress();
  }

  setupFormSteps() {
    this.formSections = this.form.querySelectorAll('.form-section');
    this.showCurrentStep();
  }

  setupModal() {
    this.modal = document.getElementById('preview-modal');
    if (this.modal) {
      this.modalCloseBtn = this.modal.querySelector('.modal-close');
      this.modalOverlay = this.modal.querySelector('.modal-overlay');

      this.modalCloseBtn?.addEventListener('click', () => this.closeModal());
      this.modalOverlay?.addEventListener('click', () => this.closeModal());

      // Keyboard navigation
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.modal.classList.contains('active')) {
          this.closeModal();
        }
      });
    }
  }

  setupCharacterCounters() {
    const textareas = this.form.querySelectorAll('textarea[data-max-length]');
    textareas.forEach(textarea => {
      const maxLength = parseInt(textarea.getAttribute('data-max-length'));
      const counter = document.createElement('div');
      counter.className = 'character-counter';
      counter.setAttribute('aria-live', 'polite');

      const updateCounter = () => {
        const remaining = maxLength - textarea.value.length;
        counter.textContent = `${remaining} characters remaining`;

        counter.classList.remove('warning', 'error');
        if (remaining < 50) {
          counter.classList.add('warning');
        }
        if (remaining < 0) {
          counter.classList.add('error');
        }
      };

      textarea.parentNode.appendChild(counter);
      textarea.addEventListener('input', updateCounter);
      updateCounter(); // Initial update
    });
  }

  setupPriorityIndicator() {
    const prioritySelect = this.form.querySelector('#priority');
    const priorityIndicator = this.form.querySelector('.priority-indicator');

    if (prioritySelect && priorityIndicator) {
      const updatePriorityIndicator = () => {
        const priority = prioritySelect.value;
        if (priority) {
          priorityIndicator.setAttribute('data-priority', priority);
          priorityIndicator.innerHTML = `
            <span class="priority-icon">${this.getPriorityIcon(priority)}</span>
            <span class="priority-text">${priority.charAt(0).toUpperCase() + priority.slice(1)} Priority</span>
          `;
          priorityIndicator.style.display = 'flex';
        } else {
          priorityIndicator.style.display = 'none';
        }
      };

      prioritySelect.addEventListener('change', updatePriorityIndicator);
      updatePriorityIndicator(); // Initial update
    }
  }

  getPriorityIcon(priority) {
    const icons = {
      low: '🟢',
      normal: '🟡',
      high: '🟠',
      urgent: '🔴'
    };
    return icons[priority] || '⚪';
  }

  bindEvents() {
    // Navigation buttons
    this.form.addEventListener('click', (e) => {
      if (e.target.matches('.btn-next')) {
        e.preventDefault();
        this.nextStep();
      }

      if (e.target.matches('.btn-prev')) {
        e.preventDefault();
        this.prevStep();
      }

      if (e.target.matches('.btn-preview')) {
        e.preventDefault();
        this.showPreview();
      }
    });

    // Form validation events
    this.form.addEventListener('validation:passed', () => {
      this.showSuccess();
    });

    this.form.addEventListener('validation:failed', (e) => {
      this.showValidationErrors(e.detail.errors);
    });
  }

  updateProgress() {
    const progress = ((this.currentStep - 1) / (this.totalSteps - 1)) * 100;
    this.progressFill.style.width = `${progress}%`;

    this.progressSteps.forEach((step, index) => {
      const stepNumber = index + 1;
      step.classList.remove('active', 'completed');

      if (stepNumber === this.currentStep) {
        step.classList.add('active');
      } else if (stepNumber < this.currentStep) {
        step.classList.add('completed');
      }
    });
  }

  showCurrentStep() {
    this.formSections.forEach((section, index) => {
      if (index + 1 === this.currentStep) {
        section.style.display = 'block';
        // Focus first input in the section
        const firstInput = section.querySelector('input, select, textarea');
        if (firstInput) {
          setTimeout(() => firstInput.focus(), 100);
        }
      } else {
        section.style.display = 'none';
      }
    });

    this.updateNavigationButtons();
  }

  updateNavigationButtons() {
    const prevBtn = this.form.querySelector('.btn-prev');
    const nextBtn = this.form.querySelector('.btn-next');
    const submitBtn = this.form.querySelector('.btn-submit');
    const previewBtn = this.form.querySelector('.btn-preview');

    if (prevBtn) {
      prevBtn.style.display = this.currentStep > 1 ? 'inline-flex' : 'none';
    }

    if (nextBtn) {
      nextBtn.style.display = this.currentStep < this.totalSteps ? 'inline-flex' : 'none';
    }

    if (submitBtn) {
      submitBtn.style.display = this.currentStep === this.totalSteps ? 'inline-flex' : 'none';
    }

    if (previewBtn) {
      previewBtn.style.display = this.currentStep === this.totalSteps ? 'inline-flex' : 'none';
    }
  }

  nextStep() {
    if (this.currentStep < this.totalSteps) {
      // Validate current step before proceeding
      if (this.validateCurrentStep()) {
        this.currentStep++;
        this.updateProgress();
        this.showCurrentStep();
        this.dispatchEvent('step:changed', { step: this.currentStep });
      }
    }
  }

  prevStep() {
    if (this.currentStep > 1) {
      this.currentStep--;
      this.updateProgress();
      this.showCurrentStep();
      this.dispatchEvent('step:changed', { step: this.currentStep });
    }
  }

  validateCurrentStep() {
    const currentSection = this.formSections[this.currentStep - 1];
    const requiredFields = currentSection.querySelectorAll('[required]');

    let isValid = true;
    requiredFields.forEach(field => {
      if (!field.value.trim()) {
        field.focus();
        isValid = false;
      }
    });

    return isValid;
  }

  showPreview() {
    if (!this.modal) return;

    const previewContent = this.generatePreviewContent();
    const modalBody = this.modal.querySelector('.modal-body');

    if (modalBody) {
      modalBody.innerHTML = previewContent;
    }

    this.openModal();
  }

  generatePreviewContent() {
    const data = this.getFormData();
    return `
      <div class="preview-content">
        <h3>Ticket Preview</h3>
        <div class="preview-grid">
          <div class="preview-section">
            <div class="preview-label">Subject</div>
            <div class="preview-value">${this.escapeHtml(data.subject || 'Not provided')}</div>
          </div>

          <div class="preview-section">
            <div class="preview-label">Category</div>
            <div class="preview-value">${this.escapeHtml(data.category || 'Not provided')}</div>
          </div>

          <div class="preview-section">
            <div class="preview-label">Priority</div>
            <div class="preview-value priority" data-priority="${data.priority || 'normal'}">
              <span class="priority-icon">${this.getPriorityIcon(data.priority || 'normal')}</span>
              <span class="priority-text">${(data.priority || 'normal').charAt(0).toUpperCase() + (data.priority || 'normal').slice(1)} Priority</span>
            </div>
          </div>

          <div class="preview-section">
            <div class="preview-label">Description</div>
            <div class="preview-value">${this.escapeHtml(data.description || 'Not provided')}</div>
          </div>

          <div class="preview-section">
            <div class="preview-label">Contact Email</div>
            <div class="preview-value">${this.escapeHtml(data.email || 'Not provided')}</div>
          </div>

          <div class="preview-section">
            <div class="preview-label">Phone (Optional)</div>
            <div class="preview-value">${this.escapeHtml(data.phone || 'Not provided')}</div>
          </div>

          ${data.attachments && data.attachments.length > 0 ? `
            <div class="preview-section">
              <div class="preview-label">Attachments</div>
              <div class="preview-value">
                ${data.attachments.map(file => `<div>• ${this.escapeHtml(file.name)} (${this.formatFileSize(file.size)})</div>`).join('')}
              </div>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }

  getFormData() {
    const formData = new FormData(this.form);
    const data = {};

    for (let [key, value] of formData.entries()) {
      if (key === 'attachments') {
        if (!data.attachments) data.attachments = [];
        data.attachments.push({
          name: value.name,
          size: value.size,
          type: value.type
        });
      } else {
        data[key] = value;
      }
    }

    return data;
  }

  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  openModal() {
    if (this.modal) {
      this.modal.classList.add('active');
      document.body.style.overflow = 'hidden';

      // Focus management
      const focusableElements = this.modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (focusableElements.length > 0) {
        focusableElements[0].focus();
      }
    }
  }

  closeModal() {
    if (this.modal) {
      this.modal.classList.remove('active');
      document.body.style.overflow = '';

      // Return focus to trigger element
      const previewBtn = this.form.querySelector('.btn-preview');
      if (previewBtn) {
        previewBtn.focus();
      }
    }
  }

  showSuccess() {
    // Show success message
    const successMessage = document.createElement('div');
    successMessage.className = 'success-message';
    successMessage.innerHTML = `
      <div class="success-icon">✅</div>
      <div class="success-content">
        <h3>Ticket Submitted Successfully!</h3>
        <p>Your support ticket has been submitted. You'll receive a confirmation email shortly.</p>
      </div>
    `;

    // Replace form content with success message
    this.form.innerHTML = '';
    this.form.appendChild(successMessage);

    this.dispatchEvent('form:submitted');
  }

  showValidationErrors(errors) {
    // Show summary of validation errors
    console.log('Validation errors:', errors);
    // Could show a toast or summary message here
  }

  dispatchEvent(eventName, detail = {}) {
    const event = new CustomEvent(eventName, {
      detail: { ui: this, ...detail }
    });
    this.form.dispatchEvent(event);
  }

  // Public API methods
  goToStep(step) {
    if (step >= 1 && step <= this.totalSteps) {
      this.currentStep = step;
      this.updateProgress();
      this.showCurrentStep();
    }
  }

  getCurrentStep() {
    return this.currentStep;
  }

  refresh() {
    this.updateProgress();
    this.showCurrentStep();
  }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TicketFormUI;
}

// Make available globally
window.TicketFormUI = TicketFormUI;