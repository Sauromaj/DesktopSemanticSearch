// Main JavaScript for Semantic Document Search

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            const alert = bootstrap.Alert.getOrCreateInstance(message);
            alert.close();
        }, 5000);
    });

    // Handle search form submission
    const searchForm = document.querySelector('form[action*="search"]');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            const searchInput = this.querySelector('input[name="query"]');
            if (!searchInput.value.trim()) {
                e.preventDefault();
                searchInput.classList.add('is-invalid');
                
                // Create error message if it doesn't exist
                let errorMessage = searchInput.nextElementSibling;
                if (!errorMessage || !errorMessage.classList.contains('invalid-feedback')) {
                    errorMessage = document.createElement('div');
                    errorMessage.classList.add('invalid-feedback');
                    errorMessage.textContent = 'Please enter a search query';
                    searchInput.after(errorMessage);
                }
                
                // Focus the input
                searchInput.focus();
            }
        });
    }

    // File upload preview
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            // Get selected files
            const fileList = this.files;
            
            // Create or find preview element
            let filePreview = document.getElementById('file-preview');
            if (!filePreview) {
                filePreview = document.createElement('div');
                filePreview.id = 'file-preview';
                filePreview.classList.add('mt-3');
                this.parentNode.appendChild(filePreview);
            }
            
            // Clear previous preview
            filePreview.innerHTML = '';
            
            // If files selected, show preview
            if (fileList.length > 0) {
                const heading = document.createElement('h6');
                heading.textContent = 'Selected Files:';
                filePreview.appendChild(heading);
                
                const list = document.createElement('ul');
                list.classList.add('list-group');
                
                for (let i = 0; i < fileList.length; i++) {
                    const file = fileList[i];
                    const listItem = document.createElement('li');
                    listItem.classList.add('list-group-item', 'd-flex', 'justify-content-between', 'align-items-center');
                    
                    // Determine file icon based on extension
                    const extension = file.name.split('.').pop().toLowerCase();
                    let iconClass = 'bi-file-earmark';
                    
                    if (['pdf'].includes(extension)) {
                        iconClass = 'bi-file-earmark-pdf';
                    } else if (['doc', 'docx'].includes(extension)) {
                        iconClass = 'bi-file-earmark-word';
                    } else if (['xls', 'xlsx'].includes(extension)) {
                        iconClass = 'bi-file-earmark-spreadsheet';
                    } else if (['csv'].includes(extension)) {
                        iconClass = 'bi-file-earmark-text';
                    }
                    
                    // Create file info
                    listItem.innerHTML = `
                        <div>
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi ${iconClass} me-2" viewBox="0 0 16 16">
                                <path d="M14 14V4.5L9.5 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2zM9.5 3A1.5 1.5 0 0 1 11 4.5h2V14a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1h5.5v2z"/>
                            </svg>
                            ${file.name}
                        </div>
                        <span class="badge bg-primary rounded-pill">${formatFileSize(file.size)}</span>
                    `;
                    
                    list.appendChild(listItem);
                }
                
                filePreview.appendChild(list);
            }
        });
    }
});

// Helper function to format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}