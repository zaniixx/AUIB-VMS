/**
 * Ticket Form Validation Module
 * Handles all form validation logic for the ticket submission form
 */

class TicketFormValidator {
  constructor(form) {
    this.form = form;
    this.errors = new Map();
    this.rules = {
      required: (value) => value && value.trim().length > 0,
      email: (value) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value),
      minLength: (value, min) => value && value.length >= min,
      maxLength: (value, max) => !value || value.length <= max,
      pattern: (value, pattern) => !value || pattern.test(value),
      fileType: (files, allowedTypes) => {
        if (!files || files.length === 0) return true;
        return Array.from(files).every(file => allowedTypes.includes(file.type));
      },
      fileSize: (files, maxSize) => {
        if (!files || files.length === 0) return true;
        return Array.from(files).every(file => file.size <= maxSize);
      }
    };

    this.messages = {
      required: 'This field is required',
      email: 'Please enter a valid email address',
      minLength: (field, min) => `${field} must be at least ${min} characters`,
      maxLength: (field, max) => `${field} must not exceed ${max} characters`,
      pattern: 'Please enter a valid value',
      fileType: 'File type not allowed. Allowed types: ',
      fileSize: 'File size exceeds the maximum limit'
    };

    this.init();
  }

  init() {
    this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    this.form.addEventListener('input', (e) => this.handleInput(e));
    this.form.addEventListener('blur', (e) => this.handleBlur(e), true);
  }

  handleSubmit(e) {
    const isValid = this.validateForm();
    if (!isValid) {
      e.preventDefault();
      this.showFirstError();
      this.dispatchEvent('validation:failed', { errors: this.errors });
    } else {
      this.dispatchEvent('validation:passed');
    }
  }

  handleInput(e) {
    const field = e.target;
    if (field.hasAttribute('data-validate')) {
      this.validateField(field);
    }
  }

  handleBlur(e) {
    const field = e.target;
    if (field.hasAttribute('data-validate')) {
      this.validateField(field);
    }
  }

  validateForm() {
    this.clearErrors();
    let isValid = true;

    const fields = this.form.querySelectorAll('[data-validate]');
    fields.forEach(field => {
      if (!this.validateField(field)) {
        isValid = false;
      }
    });

    return isValid;
  }

  validateField(field) {
    const rules = field.getAttribute('data-validate').split(',');
    const fieldName = field.getAttribute('data-field-name') || field.name;
    let isValid = true;
    const fieldErrors = [];

    rules.forEach(rule => {
      const [ruleName, param] = rule.trim().split(':');
      if (!this.checkRule(field, ruleName, param)) {
        isValid = false;
        fieldErrors.push(this.getErrorMessage(ruleName, fieldName, param));
      }
    });

    if (!isValid) {
      this.showFieldError(field, fieldErrors);
      this.errors.set(field.name, fieldErrors);
    } else {
      this.clearFieldError(field);
      this.errors.delete(field.name);
    }

    return isValid;
  }

  checkRule(field, ruleName, param) {
    const value = this.getFieldValue(field);
    const rule = this.rules[ruleName];

    if (!rule) {
      console.warn(`Validation rule "${ruleName}" not found`);
      return true;
    }

    switch (ruleName) {
      case 'required':
        return rule(value);
      case 'email':
        return rule(value);
      case 'minLength':
        return rule(value, parseInt(param));
      case 'maxLength':
        return rule(value, parseInt(param));
      case 'pattern':
        return rule(value, new RegExp(param));
      case 'fileType':
        return rule(field.files, param.split('|'));
      case 'fileSize':
        return rule(field.files, parseInt(param) * 1024 * 1024); // Convert MB to bytes
      default:
        return true;
    }
  }

  getFieldValue(field) {
    if (field.type === 'checkbox' || field.type === 'radio') {
      return field.checked ? field.value : '';
    }
    if (field.tagName === 'SELECT') {
      return field.value;
    }
    return field.value;
  }

  getErrorMessage(ruleName, fieldName, param) {
    const message = this.messages[ruleName];
    if (typeof message === 'function') {
      return message(fieldName, param);
    }

    if (ruleName === 'fileType') {
      return message + param.split('|').join(', ');
    }

    return message;
  }

  showFieldError(field, errors) {
    this.clearFieldError(field);

    const errorContainer = document.createElement('div');
    errorContainer.className = 'field-error';
    errorContainer.setAttribute('role', 'alert');
    errorContainer.setAttribute('aria-live', 'polite');

    errors.forEach(error => {
      const errorElement = document.createElement('div');
      errorElement.className = 'error-message';
      errorElement.textContent = error;
      errorContainer.appendChild(errorElement);
    });

    field.setAttribute('aria-invalid', 'true');
    field.setAttribute('aria-describedby', `error-${field.name}`);

    const fieldGroup = field.closest('.form-group');
    if (fieldGroup) {
      fieldGroup.appendChild(errorContainer);
    }
  }

  clearFieldError(field) {
    field.removeAttribute('aria-invalid');
    field.removeAttribute('aria-describedby');

    const fieldGroup = field.closest('.form-group');
    if (fieldGroup) {
      const existingError = fieldGroup.querySelector('.field-error');
      if (existingError) {
        existingError.remove();
      }
    }
  }

  clearErrors() {
    this.errors.clear();
    this.form.querySelectorAll('.field-error').forEach(error => error.remove());
    this.form.querySelectorAll('[aria-invalid]').forEach(field => {
      field.removeAttribute('aria-invalid');
      field.removeAttribute('aria-describedby');
    });
  }

  showFirstError() {
    const firstErrorField = this.form.querySelector('[aria-invalid="true"]');
    if (firstErrorField) {
      firstErrorField.focus();
      firstErrorField.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  dispatchEvent(eventName, detail = {}) {
    const event = new CustomEvent(eventName, {
      detail: { validator: this, ...detail }
    });
    this.form.dispatchEvent(event);
  }

  // Public API methods
  isValid() {
    return this.validateForm();
  }

  getErrors() {
    return Object.fromEntries(this.errors);
  }

  addRule(name, rule, message) {
    this.rules[name] = rule;
    this.messages[name] = message;
  }

  removeRule(name) {
    delete this.rules[name];
    delete this.messages[name];
  }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TicketFormValidator;
}

// Make available globally
window.TicketFormValidator = TicketFormValidator;