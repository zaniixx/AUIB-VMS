/**
 * AUIB VMS Progressive Enhancement
 * Minimal, accessible JavaScript for enhanced UX
 * Graceful degradation for no-JS environments
 */

(function() {
  'use strict';

  // ========== Form Validation ========== //
  function enhanceForms() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
      form.addEventListener('submit', function(e) {
        const inputs = form.querySelectorAll('[required]');
        let isValid = true;

        inputs.forEach(input => {
          if (!input.value.trim()) {
            isValid = false;
            input.classList.add('form-input--error');
            
            // Show error message if not already shown
            let errorEl = input.nextElementSibling;
            if (!errorEl || !errorEl.classList.contains('form-error')) {
              errorEl = document.createElement('span');
              errorEl.className = 'form-error';
              errorEl.textContent = input.dataset.errorMessage || 'This field is required';
              input.parentNode.insertBefore(errorEl, input.nextSibling);
            }
          } else {
            input.classList.remove('form-input--error');
            const errorEl = input.nextElementSibling;
            if (errorEl && errorEl.classList.contains('form-error')) {
              errorEl.remove();
            }
          }
        });

        if (!isValid) {
          e.preventDefault();
          // Focus first invalid input
          const firstInvalid = form.querySelector('.form-input--error');
          if (firstInvalid) {
            firstInvalid.focus();
          }
        }
      });

      // Remove error on input
      const inputs = form.querySelectorAll('[required]');
      inputs.forEach(input => {
        input.addEventListener('input', function() {
          if (this.value.trim()) {
            this.classList.remove('form-input--error');
            const errorEl = this.nextElementSibling;
            if (errorEl && errorEl.classList.contains('form-error')) {
              errorEl.remove();
            }
          }
        });
      });
    });
  }

  // ========== Confirmation Dialogs ========== //
  function enhanceConfirmations() {
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    
    confirmButtons.forEach(button => {
      button.addEventListener('click', function(e) {
        const message = this.dataset.confirm || 'Are you sure?';
        if (!confirm(message)) {
          e.preventDefault();
        }
      });
    });
  }

  // ========== Alert Dismissal ========== //
  function enhanceAlerts() {
    const alerts = document.querySelectorAll('[data-dismissible]');
    
    alerts.forEach(alert => {
      // Add close button if not exists
      if (!alert.querySelector('.alert__close')) {
        const closeBtn = document.createElement('button');
        closeBtn.type = 'button';
        closeBtn.className = 'alert__close btn--ghost btn--sm';
        closeBtn.innerHTML = '×';
        closeBtn.setAttribute('aria-label', 'Close alert');
        closeBtn.style.cssText = 'margin-left: auto; padding: 0.25rem 0.5rem; font-size: 1.5rem; line-height: 1;';
        
        closeBtn.addEventListener('click', function() {
          alert.style.transition = 'opacity 0.2s ease-out, transform 0.2s ease-out';
          alert.style.opacity = '0';
          alert.style.transform = 'translateY(-0.5rem)';
          setTimeout(() => alert.remove(), 200);
        });
        
        alert.appendChild(closeBtn);
      }
    });
  }

  // ========== Loading States ========== //
  function enhanceSubmitButtons() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
      form.addEventListener('submit', function() {
        const submitBtn = this.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn && !submitBtn.disabled) {
          const originalText = submitBtn.textContent || submitBtn.value;
          submitBtn.disabled = true;
          
          if (submitBtn.tagName === 'BUTTON') {
            submitBtn.innerHTML = '<span class="spinner"></span> Processing...';
          }
          
          // Re-enable after 10 seconds as fallback
          setTimeout(() => {
            submitBtn.disabled = false;
            if (submitBtn.tagName === 'BUTTON') {
              submitBtn.textContent = originalText;
            }
          }, 10000);
        }
      });
    });
  }

  // ========== Auto-hide Flash Messages ========== //
  function autoHideFlashMessages() {
    const flashMessages = document.querySelectorAll('.alert[data-auto-hide]');
    
    flashMessages.forEach(alert => {
      const delay = parseInt(alert.dataset.autoHide) || 5000;
      setTimeout(() => {
        alert.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-1rem)';
        setTimeout(() => alert.remove(), 300);
      }, delay);
    });
  }

  // ========== Filter Tables (Client-side) ========== //
  function enhanceTableFilters() {
    const filterInputs = document.querySelectorAll('[data-filter-table]');
    
    filterInputs.forEach(input => {
      const tableId = input.dataset.filterTable;
      const table = document.getElementById(tableId);
      
      if (!table) return;
      
      input.addEventListener('input', function() {
        const filterValue = this.value.toLowerCase();
        const rows = table.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
          const text = row.textContent.toLowerCase();
          row.style.display = text.includes(filterValue) ? '' : 'none';
        });
        
        // Show "no results" message if all rows hidden
        const visibleRows = table.querySelectorAll('tbody tr:not([style*="display: none"])');
        let noResultsRow = table.querySelector('.no-results-row');
        
        if (visibleRows.length === 0) {
          if (!noResultsRow) {
            noResultsRow = document.createElement('tr');
            noResultsRow.className = 'no-results-row';
            noResultsRow.innerHTML = '<td colspan="100" class="text-center" style="padding: 2rem;">No results found</td>';
            table.querySelector('tbody').appendChild(noResultsRow);
          }
        } else if (noResultsRow) {
          noResultsRow.remove();
        }
      });
    });
  }

  // ========== Accessible Dropdown Menus ========== //
  function enhanceDropdowns() {
    // Handle data-attribute dropdowns
    const dropdownToggles = document.querySelectorAll('[data-dropdown-toggle]');
    
    dropdownToggles.forEach(toggle => {
      const menuId = toggle.dataset.dropdownToggle;
      const menu = document.getElementById(menuId);
      
      if (!menu) return;
      
      toggle.addEventListener('click', function(e) {
        e.stopPropagation();
        const isOpen = menu.style.display === 'block';
        
        // Close all other dropdowns
        document.querySelectorAll('[data-dropdown-menu]').forEach(m => {
          m.style.display = 'none';
        });
        
        menu.style.display = isOpen ? 'none' : 'block';
      });
      
      // Close on outside click
      document.addEventListener('click', function() {
        menu.style.display = 'none';
      });
      
      // Close on escape
      document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
          menu.style.display = 'none';
          toggle.focus();
        }
      });
    });

    // Handle navigation dropdowns
    const navDropdowns = document.querySelectorAll('.nav__dropdown');
    
    navDropdowns.forEach(dropdown => {
      const toggle = dropdown.querySelector('.nav__dropdown-toggle');
      const menu = dropdown.querySelector('.nav__dropdown-menu');
      
      if (!toggle || !menu) return;
      
      toggle.addEventListener('click', function(e) {
        e.stopPropagation();
        const isExpanded = toggle.getAttribute('aria-expanded') === 'true';
        
        // Close all other nav dropdowns
        document.querySelectorAll('.nav__dropdown-toggle').forEach(t => {
          t.setAttribute('aria-expanded', 'false');
        });
        document.querySelectorAll('.nav__dropdown-menu').forEach(m => {
          m.style.opacity = '0';
          m.style.visibility = 'hidden';
          m.style.transform = 'translateY(-10px)';
        });
        
        if (!isExpanded) {
          toggle.setAttribute('aria-expanded', 'true');
          menu.style.opacity = '1';
          menu.style.visibility = 'visible';
          menu.style.transform = 'translateY(0)';
        }
      });
      
      // Close on outside click
      document.addEventListener('click', function() {
        toggle.setAttribute('aria-expanded', 'false');
        menu.style.opacity = '0';
        menu.style.visibility = 'hidden';
        menu.style.transform = 'translateY(-10px)';
      });
      
      // Close on escape
      document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
          toggle.setAttribute('aria-expanded', 'false');
          menu.style.opacity = '0';
          menu.style.visibility = 'hidden';
          menu.style.transform = 'translateY(-10px)';
          toggle.focus();
        }
      });
    });
  }

  // ========== Copy to Clipboard ========== //
  function enhanceCopyButtons() {
    const copyButtons = document.querySelectorAll('[data-copy]');
    
    copyButtons.forEach(button => {
      button.addEventListener('click', async function() {
        const textToCopy = this.dataset.copy;
        
        try {
          await navigator.clipboard.writeText(textToCopy);
          
          const originalText = this.textContent;
          this.textContent = '✓ Copied!';
          this.classList.add('btn--success');
          
          setTimeout(() => {
            this.textContent = originalText;
            this.classList.remove('btn--success');
          }, 2000);
        } catch (err) {
          console.error('Failed to copy:', err);
        }
      });
    });
  }

  // ========== Initialize All Enhancements ========== //
  function init() {
    // Check if DOM is ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
      return;
    }

    enhanceForms();
    enhanceConfirmations();
    enhanceAlerts();
    enhanceSubmitButtons();
    autoHideFlashMessages();
    enhanceTableFilters();
    enhanceDropdowns();
    enhanceCopyButtons();
  }

  // Run initialization
  init();
})();
