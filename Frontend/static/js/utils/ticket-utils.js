/**
 * Utility Functions for Ticket Form
 * Common helper functions and utilities
 */

/**
 * DOM manipulation utilities
 */
const DOMUtils = {
  /**
   * Create an element with attributes and content
   */
  createElement(tag, attributes = {}, content = '') {
    const element = document.createElement(tag);

    Object.keys(attributes).forEach(key => {
      if (key === 'className') {
        element.className = attributes[key];
      } else if (key === 'textContent') {
        element.textContent = attributes[key];
      } else if (key === 'innerHTML') {
        element.innerHTML = attributes[key];
      } else if (key.startsWith('data-')) {
        element.setAttribute(key, attributes[key]);
      } else {
        element.setAttribute(key, attributes[key]);
      }
    });

    if (content && !attributes.textContent && !attributes.innerHTML) {
      element.textContent = content;
    }

    return element;
  },

  /**
   * Add event listener with automatic cleanup tracking
   */
  addEventListener(element, event, handler, options = {}) {
    element.addEventListener(event, handler, options);

    // Track for cleanup if needed
    if (!element._eventListeners) {
      element._eventListeners = [];
    }
    element._eventListeners.push({ event, handler, options });
  },

  /**
   * Remove all tracked event listeners
   */
  removeAllEventListeners(element) {
    if (element._eventListeners) {
      element._eventListeners.forEach(({ event, handler, options }) => {
        element.removeEventListener(event, handler, options);
      });
      element._eventListeners = [];
    }
  },

  /**
   * Toggle element visibility
   */
  toggleVisibility(element, show = null) {
    const willShow = show !== null ? show : element.style.display === 'none';
    element.style.display = willShow ? '' : 'none';
    return willShow;
  },

  /**
   * Add CSS class temporarily
   */
  addClassTemporarily(element, className, duration = 1000) {
    element.classList.add(className);
    setTimeout(() => element.classList.remove(className), duration);
  }
};

/**
 * Form utilities
 */
const FormUtils = {
  /**
   * Serialize form data to object
   */
  serialize(form) {
    const data = {};
    const formData = new FormData(form);

    for (let [key, value] of formData.entries()) {
      if (data[key]) {
        if (Array.isArray(data[key])) {
          data[key].push(value);
        } else {
          data[key] = [data[key], value];
        }
      } else {
        data[key] = value;
      }
    }

    return data;
  },

  /**
   * Check if form has changes
   */
  hasChanges(form, originalData = {}) {
    const currentData = this.serialize(form);

    for (let key in currentData) {
      if (currentData[key] !== originalData[key]) {
        return true;
      }
    }

    for (let key in originalData) {
      if (!(key in currentData)) {
        return true;
      }
    }

    return false;
  },

  /**
   * Reset form with confirmation
   */
  resetWithConfirmation(form, message = 'Are you sure you want to reset the form? All changes will be lost.') {
    if (confirm(message)) {
      form.reset();
      // Trigger change events for any custom components
      const event = new Event('reset', { bubbles: true });
      form.dispatchEvent(event);
    }
  }
};

/**
 * Validation utilities
 */
const ValidationUtils = {
  /**
   * Common validation patterns
   */
  patterns: {
    email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    phone: /^[\+]?[1-9][\d]{0,15}$/,
    url: /^https?:\/\/.+/,
    alphanumeric: /^[a-zA-Z0-9]+$/,
    numeric: /^\d+$/
  },

  /**
   * Validate email format
   */
  isValidEmail(email) {
    return this.patterns.email.test(email);
  },

  /**
   * Validate phone number (basic)
   */
  isValidPhone(phone) {
    return this.patterns.phone.test(phone.replace(/[\s\-\(\)]/g, ''));
  },

  /**
   * Check if value is empty
   */
  isEmpty(value) {
    return !value || value.toString().trim().length === 0;
  },

  /**
   * Check string length
   */
  hasValidLength(value, min = 0, max = Infinity) {
    if (!value) return min === 0;
    const length = value.toString().trim().length;
    return length >= min && length <= max;
  }
};

/**
 * File utilities
 */
const FileUtils = {
  /**
   * Format file size in human readable format
   */
  formatSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  /**
   * Get file extension
   */
  getExtension(filename) {
    return filename.split('.').pop().toLowerCase();
  },

  /**
   * Get file type icon
   */
  getFileIcon(mimeType) {
    const icons = {
      'image/': '🖼️',
      'video/': '🎥',
      'audio/': '🎵',
      'application/pdf': '📄',
      'application/msword': '📝',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '📝',
      'text/': '📃',
      'application/zip': '📦',
      'application/x-rar-compressed': '📦'
    };

    for (let [type, icon] of Object.entries(icons)) {
      if (mimeType.startsWith(type)) {
        return icon;
      }
    }

    return '📎';
  },

  /**
   * Validate file against constraints
   */
  validateFile(file, constraints = {}) {
    const errors = [];

    if (constraints.maxSize && file.size > constraints.maxSize) {
      errors.push(`File size exceeds ${this.formatSize(constraints.maxSize)}`);
    }

    if (constraints.allowedTypes && !constraints.allowedTypes.includes(file.type)) {
      errors.push(`File type ${file.type} not allowed`);
    }

    if (constraints.allowedExtensions) {
      const ext = this.getExtension(file.name);
      if (!constraints.allowedExtensions.includes(ext)) {
        errors.push(`File extension .${ext} not allowed`);
      }
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }
};

/**
 * Animation utilities
 */
const AnimationUtils = {
  /**
   * Smooth scroll to element
   */
  scrollTo(element, offset = 0) {
    const elementPosition = element.getBoundingClientRect().top;
    const offsetPosition = elementPosition + window.pageYOffset - offset;

    window.scrollTo({
      top: offsetPosition,
      behavior: 'smooth'
    });
  },

  /**
   * Fade in element
   */
  fadeIn(element, duration = 300) {
    element.style.opacity = '0';
    element.style.display = 'block';

    const start = performance.now();

    const fade = (timestamp) => {
      const elapsed = timestamp - start;
      const progress = elapsed / duration;

      if (progress < 1) {
        element.style.opacity = progress;
        requestAnimationFrame(fade);
      } else {
        element.style.opacity = '1';
      }
    };

    requestAnimationFrame(fade);
  },

  /**
   * Fade out element
   */
  fadeOut(element, duration = 300) {
    const start = performance.now();
    const startOpacity = parseFloat(getComputedStyle(element).opacity) || 1;

    const fade = (timestamp) => {
      const elapsed = timestamp - start;
      const progress = elapsed / duration;

      if (progress < 1) {
        element.style.opacity = startOpacity * (1 - progress);
        requestAnimationFrame(fade);
      } else {
        element.style.opacity = '0';
        element.style.display = 'none';
      }
    };

    requestAnimationFrame(fade);
  }
};

/**
 * Accessibility utilities
 */
const A11yUtils = {
  /**
   * Announce message to screen readers
   */
  announce(message, priority = 'polite') {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', priority);
    announcement.setAttribute('aria-atomic', 'true');
    announcement.style.position = 'absolute';
    announcement.style.left = '-10000px';
    announcement.style.width = '1px';
    announcement.style.height = '1px';
    announcement.style.overflow = 'hidden';

    announcement.textContent = message;
    document.body.appendChild(announcement);

    setTimeout(() => {
      document.body.removeChild(announcement);
    }, 1000);
  },

  /**
   * Trap focus within element
   */
  trapFocus(element) {
    const focusableElements = element.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            lastElement.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastElement) {
            firstElement.focus();
            e.preventDefault();
          }
        }
      }
    };

    element.addEventListener('keydown', handleTabKey);

    return () => element.removeEventListener('keydown', handleTabKey);
  },

  /**
   * Set up ARIA attributes for expandable content
   */
  setupExpandable(element, trigger, expanded = false) {
    trigger.setAttribute('aria-expanded', expanded.toString());
    element.setAttribute('aria-hidden', (!expanded).toString());

    trigger.addEventListener('click', () => {
      const isExpanded = trigger.getAttribute('aria-expanded') === 'true';
      trigger.setAttribute('aria-expanded', (!isExpanded).toString());
      element.setAttribute('aria-hidden', isExpanded.toString());
    });
  }
};

/**
 * Local storage utilities with error handling
 */
const StorageUtils = {
  /**
   * Get item from localStorage
   */
  get(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : defaultValue;
    } catch (e) {
      console.warn('Error reading from localStorage:', e);
      return defaultValue;
    }
  },

  /**
   * Set item in localStorage
   */
  set(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (e) {
      console.warn('Error writing to localStorage:', e);
      return false;
    }
  },

  /**
   * Remove item from localStorage
   */
  remove(key) {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (e) {
      console.warn('Error removing from localStorage:', e);
      return false;
    }
  },

  /**
   * Clear all localStorage
   */
  clear() {
    try {
      localStorage.clear();
      return true;
    } catch (e) {
      console.warn('Error clearing localStorage:', e);
      return false;
    }
  }
};

// Export utilities
const Utils = {
  DOM: DOMUtils,
  Form: FormUtils,
  Validation: ValidationUtils,
  File: FileUtils,
  Animation: AnimationUtils,
  A11y: A11yUtils,
  Storage: StorageUtils
};

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Utils;
}

// Make available globally
window.TicketFormUtils = Utils;