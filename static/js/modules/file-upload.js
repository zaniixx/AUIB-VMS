/**
 * File Upload Module
 * Handles drag-and-drop file uploads with validation and preview
 */

class FileUploader {
  constructor(options = {}) {
    this.options = {
      maxFiles: options.maxFiles || 5,
      maxFileSize: options.maxFileSize || 10 * 1024 * 1024, // 10MB
      allowedTypes: options.allowedTypes || [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf',
        'text/plain',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      ],
      dropZone: options.dropZone,
      fileInput: options.fileInput,
      fileList: options.fileList,
      ...options
    };

    this.files = [];
    this.dragCounter = 0;

    this.init();
  }

  init() {
    if (this.options.dropZone) {
      this.setupDropZone();
    }

    if (this.options.fileInput) {
      this.setupFileInput();
    }

    this.renderFileList();
  }

  setupDropZone() {
    const dropZone = this.options.dropZone;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, this.preventDefaults.bind(this), false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, this.handleDragEnter.bind(this), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, this.handleDragLeave.bind(this), false);
    });

    dropZone.addEventListener('drop', this.handleDrop.bind(this), false);
  }

  setupFileInput() {
    this.options.fileInput.addEventListener('change', (e) => {
      this.handleFileSelect(e.target.files);
    });
  }

  preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  handleDragEnter(e) {
    this.dragCounter++;
    if (this.dragCounter === 1) {
      this.options.dropZone.classList.add('dragover');
    }
  }

  handleDragLeave(e) {
    this.dragCounter--;
    if (this.dragCounter === 0) {
      this.options.dropZone.classList.remove('dragover');
    }
  }

  handleDrop(e) {
    this.dragCounter = 0;
    this.options.dropZone.classList.remove('dragover');

    const files = e.dataTransfer.files;
    this.handleFileSelect(files);
  }

  handleFileSelect(fileList) {
    const files = Array.from(fileList);

    // Check total file count
    if (this.files.length + files.length > this.options.maxFiles) {
      this.showError(`Maximum ${this.options.maxFiles} files allowed`);
      return;
    }

    // Validate and add files
    const validFiles = [];
    const errors = [];

    files.forEach(file => {
      const validation = this.validateFile(file);
      if (validation.valid) {
        validFiles.push(file);
      } else {
        errors.push(`${file.name}: ${validation.error}`);
      }
    });

    if (errors.length > 0) {
      this.showError('Some files were not added:\n' + errors.join('\n'));
    }

    if (validFiles.length > 0) {
      this.addFiles(validFiles);
    }
  }

  validateFile(file) {
    // Check file type
    if (!this.options.allowedTypes.includes(file.type)) {
      return {
        valid: false,
        error: 'File type not allowed'
      };
    }

    // Check file size
    if (file.size > this.options.maxFileSize) {
      const maxSizeMB = Math.round(this.options.maxFileSize / (1024 * 1024));
      return {
        valid: false,
        error: `File size exceeds ${maxSizeMB}MB limit`
      };
    }

    // Check for duplicate names
    const isDuplicate = this.files.some(existingFile =>
      existingFile.name === file.name && existingFile.size === file.size
    );

    if (isDuplicate) {
      return {
        valid: false,
        error: 'File already added'
      };
    }

    return { valid: true };
  }

  addFiles(files) {
    files.forEach(file => {
      const fileData = {
        file: file,
        id: this.generateId(),
        name: file.name,
        size: file.size,
        type: file.type,
        url: URL.createObjectURL(file)
      };
      this.files.push(fileData);
    });

    this.renderFileList();
    this.updateFileInput();
    this.dispatchEvent('files:added', { files: files });
  }

  removeFile(fileId) {
    const index = this.files.findIndex(f => f.id === fileId);
    if (index !== -1) {
      const removedFile = this.files.splice(index, 1)[0];
      URL.revokeObjectURL(removedFile.url);
      this.renderFileList();
      this.updateFileInput();
      this.dispatchEvent('file:removed', { file: removedFile });
    }
  }

  generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  getFileIcon(type) {
    if (type.startsWith('image/')) return '🖼️';
    if (type === 'application/pdf') return '📄';
    if (type.includes('word') || type.includes('document')) return '📝';
    if (type === 'text/plain') return '📃';
    return '📎';
  }

  renderFileList() {
    if (!this.options.fileList) return;

    this.options.fileList.innerHTML = '';

    if (this.files.length === 0) {
      this.options.fileList.innerHTML = '<p class="no-files">No files selected</p>';
      return;
    }

    this.files.forEach(fileData => {
      const fileItem = document.createElement('div');
      fileItem.className = 'file-item';
      fileItem.innerHTML = `
        <div class="file-info">
          <div class="file-icon">${this.getFileIcon(fileData.type)}</div>
          <div class="file-details">
            <div class="file-name">${fileData.name}</div>
            <div class="file-size">${this.formatFileSize(fileData.size)}</div>
          </div>
        </div>
        <button type="button" class="file-remove" data-file-id="${fileData.id}" aria-label="Remove ${fileData.name}">
          ✕
        </button>
      `;

      // Add remove event listener
      const removeBtn = fileItem.querySelector('.file-remove');
      removeBtn.addEventListener('click', () => this.removeFile(fileData.id));

      this.options.fileList.appendChild(fileItem);
    });
  }

  updateFileInput() {
    if (!this.options.fileInput) return;

    // Create a new DataTransfer object to update the file input
    const dt = new DataTransfer();
    this.files.forEach(fileData => {
      dt.items.add(fileData.file);
    });

    this.options.fileInput.files = dt.files;
  }

  showError(message) {
    // Create and show error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'upload-error';
    errorDiv.setAttribute('role', 'alert');
    errorDiv.innerHTML = `
      <div class="error-icon">⚠️</div>
      <div class="error-content">${message}</div>
    `;

    // Insert after drop zone
    const dropZone = this.options.dropZone;
    const existingError = dropZone.parentNode.querySelector('.upload-error');
    if (existingError) {
      existingError.remove();
    }

    dropZone.parentNode.insertBefore(errorDiv, dropZone.nextSibling);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (errorDiv.parentNode) {
        errorDiv.remove();
      }
    }, 5000);
  }

  dispatchEvent(eventName, detail = {}) {
    const event = new CustomEvent(eventName, {
      detail: { uploader: this, ...detail }
    });

    if (this.options.dropZone) {
      this.options.dropZone.dispatchEvent(event);
    }
  }

  // Public API methods
  getFiles() {
    return this.files.map(f => f.file);
  }

  getFileCount() {
    return this.files.length;
  }

  clearFiles() {
    this.files.forEach(fileData => {
      URL.revokeObjectURL(fileData.url);
    });
    this.files = [];
    this.renderFileList();
    this.updateFileInput();
    this.dispatchEvent('files:cleared');
  }

  setMaxFiles(max) {
    this.options.maxFiles = max;
  }

  setMaxFileSize(size) {
    this.options.maxFileSize = size;
  }

  setAllowedTypes(types) {
    this.options.allowedTypes = types;
  }
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = FileUploader;
}

// Make available globally
window.FileUploader = FileUploader;