// Configuration
const API_BASE_URL = window.API_BASE_URL || '/api';
const ITEMS_PER_PAGE = 10;

// Toast notification function
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-message">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
    `;
    
    // Add to container
    const container = document.getElementById('toastContainer');
    if (!container) {
        const newContainer = document.createElement('div');
        newContainer.id = 'toastContainer';
        newContainer.className = 'toast-container';
        document.body.appendChild(newContainer);
    }
    
    document.getElementById('toastContainer').appendChild(toast);
    
    // Show toast
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Auto remove after delay
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// State
let currentPage = 1;
let sortBy = 'id';
let sortOrder = 'asc';
let currentFilters = {
    status: '',
    type: '',
    search: ''
};

// Search functionality
function initializeSearch() {
    const searchInput = document.getElementById('clientSearch');
    const searchButton = document.getElementById('searchButton');
    const clearSearchButton = document.getElementById('clearSearch');
    const searchResultsInfo = document.getElementById('searchResultsInfo');

    // Handle search button click
    searchButton.addEventListener('click', () => {
        currentFilters.search = searchInput.value.trim();
        currentPage = 1; // Reset to first page when searching
        updateSearchInfo();
        loadClients();
    });

    // Handle Enter key in search input
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            currentFilters.search = searchInput.value.trim();
            currentPage = 1;
            updateSearchInfo();
            loadClients();
        }
    });

    // Handle clear search
    clearSearchButton.addEventListener('click', () => {
        searchInput.value = '';
        currentFilters.search = '';
        currentPage = 1;
        updateSearchInfo();
        loadClients();
    });

    // Update search info text
    function updateSearchInfo() {
        if (!searchResultsInfo) return;
        
        if (currentFilters.search) {
            searchResultsInfo.textContent = `Search results for: "${currentFilters.search}"`;
            searchResultsInfo.classList.remove('text-muted');
            searchResultsInfo.classList.add('text-primary', 'fw-bold');
        } else {
            searchResultsInfo.textContent = 'Showing all clients';
            searchResultsInfo.classList.remove('text-primary', 'fw-bold');
            searchResultsInfo.classList.add('text-muted');
        }
    }
}

// DOM Elements
const clientsTableBody = document.getElementById('clientsTableBody');
const loadingState = document.getElementById('loadingState');
const emptyState = document.getElementById('emptyState');
const pagination = document.getElementById('pagination');
const prevPageBtn = document.getElementById('prevPage');
const nextPageBtn = document.getElementById('nextPage');
const statusFilter = document.getElementById('statusFilter');
const typeFilter = document.getElementById('typeFilter');
const searchInput = document.getElementById('searchInput');

// Initialize the page
document.addEventListener('DOMContentLoaded', () => {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Load initial data
    loadClients();

    // Add event listeners
    document.querySelectorAll('.sortable').forEach(header => {
        header.addEventListener('click', () => handleSort(header.dataset.sort));
    });

    statusFilter.addEventListener('change', handleFilterChange);
    typeFilter.addEventListener('change', handleFilterChange);
    searchInput.addEventListener('input', debounce(handleFilterChange, 300));
    prevPageBtn.addEventListener('click', goToPreviousPage);
    nextPageBtn.addEventListener('click', goToNextPage);
});

// Fetch clients from API
async function loadClients() {
    showLoading(true);
    
    try {
        // Build query parameters
        const params = new URLSearchParams({
            page: currentPage,
            per_page: ITEMS_PER_PAGE,
            sort_by: sortBy,
            sort_order: sortOrder,
            ...(currentFilters.status && { status: currentFilters.status }),
            ...(currentFilters.type && { type: currentFilters.type }),
            ...(currentFilters.search && { search: currentFilters.search })
        });

        console.log('Fetching clients with params:', params.toString());
        const response = await fetch(`${API_BASE_URL}/clients?${params}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Received data:', data);

        if (data && data.success) {
            renderClients(data.data || []);
            if (data.pagination) {
                console.log('Updating pagination with:', data.pagination);
                updatePagination({
                    total: data.pagination.total,
                    per_page: data.pagination.per_page,
                    page: data.pagination.page,
                    pages: data.pagination.pages
                });
            } else {
                console.warn('No pagination data received from server');
                // Initialize with default pagination
                updatePagination({
                    total: data.data ? data.data.length : 0,
                    per_page: ITEMS_PER_PAGE,
                    page: currentPage,
                    pages: Math.ceil((data.data ? data.data.length : 0) / ITEMS_PER_PAGE) || 1
                });
            }
        } else {
            console.error('Failed to load clients:', data);
            showError(data?.error || 'Failed to load clients');
        }
    } catch (error) {
        console.error('Error fetching clients:', error);
        showError('Failed to load clients. Please try again.');
    } finally {
        showLoading(false);
    }
}

// Render clients in the table
function renderClients(clients) {
    if (!clients || clients.length === 0) {
        showEmptyState();
        return;
    }

    clientsTableBody.innerHTML = clients.map(client => {
        return `
        <tr data-client-id="${client.id}">
            <td>${client.client_id || 'N/A'}</td>
            <td>
                <div class="d-flex align-items-center">
                    <div class="me-2">
                        <i class="fas ${client.client_type === 'Corporate' ? 'fa-building' : 'fa-user-tie'}"></i>
                    </div>
                    <div class="fw-bold">${escapeHtml(client.name || 'Unnamed Client')}</div>
                </div>
            </td>
            <td>${client.phone || 'N/A'}</td>
            <td>${client.email || 'N/A'}</td>
            <td class="text-end">
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-sm btn-outline-primary view-client" 
                            data-client-id="${client.id}"
                            data-bs-toggle="tooltip" 
                            title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-secondary edit-client" 
                            data-client-id="${client.id}"
                            data-bs-toggle="tooltip" 
                            title="Edit Client">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger delete-client" 
                            data-client-id="${client.id}"
                            data-bs-toggle="tooltip" 
                            title="Delete Client">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
        `;
    }).join('');
    
    // Initialize tooltips for the newly rendered elements
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Attach event listeners to action buttons
    attachClientActionHandlers();
}

// Attach event handlers for client actions
function attachClientActionHandlers() {
    // View client details
    document.querySelectorAll('.view-client').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const clientId = e.target.closest('button').dataset.clientId;
            viewClient(clientId);
        });
    });

    // Edit client
    document.querySelectorAll('.edit-client').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const clientId = e.target.closest('button').dataset.clientId;
            editClient(clientId);
        });
    });

    // Delete client
    document.querySelectorAll('.delete-client').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const clientId = e.target.closest('button').dataset.clientId;
            confirmDeleteClient(clientId);
        });
    });
}

// Update pagination controls
function updatePagination(pagination) {
    try {
        if (!pagination) {
            console.warn('No pagination data provided');
            return;
        }
        
        const { total = 0, per_page = ITEMS_PER_PAGE, page: current_page = 1, pages: last_page = 1 } = pagination;
        const paginationContainer = document.getElementById('paginationContainer');
        const paginationInfo = document.getElementById('paginationInfo');
        const paginationEl = document.getElementById('pagination');
        
        if (!paginationContainer || !paginationInfo || !paginationEl) {
            console.warn('Pagination elements not found in the DOM');
            return;
        }
        
        console.log('Updating pagination with:', { total, per_page, current_page, last_page });
        
        // Update pagination info
        const start = Math.min(((current_page - 1) * per_page) + 1, total);
        const end = Math.min(start + per_page - 1, total);
        
        const startItem = document.getElementById('startItem');
        const endItem = document.getElementById('endItem');
        const totalItems = document.getElementById('totalItems');
        
        if (startItem) startItem.textContent = start;
        if (endItem) endItem.textContent = end;
        if (totalItems) totalItems.textContent = total;
        
        // Update total pages in the pagination info
        if (paginationInfo) {
            paginationInfo.dataset.totalPages = last_page;
        }
        
        // Clear existing pagination
        paginationEl.innerHTML = '';
        
        // Only show pagination if there are multiple pages
        if (last_page <= 1) {
            paginationContainer.style.display = 'none';
            return;
        }
        
        // Show pagination container
        paginationContainer.style.display = 'flex';
        
        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${current_page === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `
            <a class="page-link" href="#" aria-label="Previous" ${current_page === 1 ? 'tabindex="-1"' : ''}>
                <span aria-hidden="true">&laquo;</span>
            </a>`;
        prevLi.addEventListener('click', (e) => {
            e.preventDefault();
            if (current_page > 1) goToPage(current_page - 1);
        });
        paginationEl.appendChild(prevLi);
        
        // Page numbers
        const pageNumbers = generatePageNumbers(current_page, last_page);
        pageNumbers.forEach((page) => {
            const li = document.createElement('li');
            
            if (page === '...') {
                li.className = 'page-item disabled';
                li.innerHTML = '<span class="page-link">...</span>';
            } else {
                li.className = `page-item ${page === current_page ? 'active' : ''}`;
                li.innerHTML = `<a class="page-link" href="#">${page}</a>`;
                
                if (page !== '...') {
                    li.addEventListener('click', (e) => {
                        e.preventDefault();
                        if (page !== current_page) goToPage(page);
                    });
                }
            }
            
            paginationEl.appendChild(li);
        });
        
        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${current_page === last_page ? 'disabled' : ''}`;
        nextLi.innerHTML = `
            <a class="page-link" href="#" aria-label="Next" ${current_page === last_page ? 'tabindex="-1"' : ''}>
                <span aria-hidden="true">&raquo;</span>
            </a>`;
        nextLi.addEventListener('click', (e) => {
            e.preventDefault();
            if (current_page < last_page) goToPage(current_page + 1);
        });
        paginationEl.appendChild(nextLi);
        
        console.log('Pagination updated successfully');
    } catch (error) {
        console.error('Error updating pagination:', error);
    }
}

// Generate page numbers with ellipsis
function generatePageNumbers(currentPage, totalPages, delta = 2) {
    const range = [];
    const rangeWithDots = [];
    let l;

    range.push(1);
    
    for (let i = currentPage - delta; i <= currentPage + delta; i++) {
        if (i < totalPages && i > 1) {
            range.push(i);
        }
    }
    
    range.push(totalPages);
    range.sort((a, b) => a - b);

    for (let i of range) {
        if (l) {
            if (i - l > 1) {
                rangeWithDots.push('...');
            }
        }
        rangeWithDots.push(i);
        l = i;
    }

    return rangeWithDots;
}

// Handle sorting
function handleSort(column) {
    if (sortBy === column) {
        sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        sortBy = column;
        sortOrder = 'asc';
    }
    
    // Update sort indicators
    document.querySelectorAll('.sortable i').forEach(icon => {
        icon.className = 'fas fa-sort';
    });
    
    const header = document.querySelector(`.sortable[data-sort="${column}"]`);
    if (header) {
        const icon = header.querySelector('i');
        if (icon) {
            icon.className = `fas fa-sort-${sortOrder === 'asc' ? 'up' : 'down'}`;
        }
    }
    
    // Reset to first page when changing sort
    currentPage = 1;
    loadClients();
}

// Handle filter changes
function handleFilterChange() {
    currentFilters = {
        status: statusFilter.value,
        type: typeFilter.value,
        search: searchInput.value.trim()
    };
    
    // Reset to first page when filters change
    currentPage = 1;
    loadClients();
}

// Pagination handlers
function goToPage(page) {
    if (page < 1 || page > getTotalPages()) return;
    currentPage = page;
    loadClients();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function goToNextPage() {
    if (currentPage < getTotalPages()) {
        goToPage(currentPage + 1);
    }
}

function goToPreviousPage() {
    if (currentPage > 1) {
        goToPage(currentPage - 1);
    }
}

function getTotalPages() {
    const paginationInfo = document.getElementById('paginationInfo');
    return paginationInfo ? parseInt(paginationInfo.dataset.totalPages) || 1 : 1;
}

// Client actions
function viewClient(clientId) {
    if (!clientId) {
        console.error('No client ID provided');
        return;
    }

    fetch(`${API_BASE_URL}/clients/${clientId}`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to fetch client details');
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Populate the view modal with client data
                const client = data.data;
                document.getElementById('clientDetailsName').textContent = client.name;
                document.getElementById('clientDetailsId').textContent = client.client_id;
                document.getElementById('clientDetailsType').textContent = client.client_type;
                document.getElementById('clientDetailsEmail').textContent = client.email || 'N/A';
                document.getElementById('clientDetailsPhone').textContent = client.phone || 'N/A';
                document.getElementById('clientDetailsAddress').textContent = client.address || 'N/A';
                document.getElementById('clientDetailsBalance').textContent = formatCurrency(client.balance || 0);
                document.getElementById('clientDetailsStatus').textContent = client.status || 'Active';
                
                // Show the modal
                const modal = new bootstrap.Modal(document.getElementById('clientDetailsModal'));
                modal.show();
            } else {
                throw new Error(data.error || 'Failed to load client details');
            }
        })
        .catch(error => {
            console.error('Error fetching client:', error);
            showToast('Error loading client details', 'error');
        });
}

function editClient(clientId) {
    if (!clientId) {
        console.error('No client ID provided');
        return;
    }

    // First, fetch the client data
    fetch(`${API_BASE_URL}/clients/${clientId}`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to fetch client data');
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const client = data.data;
                
                // Populate the edit form
                const form = document.getElementById('clientForm');
                form.reset();
                form.dataset.editMode = 'true';
                form.dataset.clientId = clientId;
                
                // Set form values
                document.getElementById('clientType').value = client.client_type || 'Individual';
                document.getElementById('clientName').value = client.name || '';
                document.getElementById('contactNumber').value = client.phone || '';
                document.getElementById('email').value = client.email || '';
                document.getElementById('address').value = client.address || '';
                document.getElementById('initialBalance').value = parseFloat(client.balance || 0).toFixed(2);
                
                // Update modal title and button text
                document.getElementById('addClientModalLabel').innerHTML = '<i class="fas fa-edit me-2"></i>Edit Client';
                document.getElementById('saveClient').textContent = 'Update Client';
                
                // Show the modal
                const modal = new bootstrap.Modal(document.getElementById('addClientModal'));
                modal.show();
            } else {
                throw new Error(data.error || 'Failed to load client data');
            }
        })
        .catch(error => {
            console.error('Error fetching client data:', error);
            showToast(error.message || 'Failed to load client data', 'error');
        });
}

function confirmDeleteClient(clientId) {
    if (!clientId) {
        console.error('No client ID provided');
        return;
    }

    // Show confirmation dialog
    Swal.fire({
        title: 'Are you sure?',
        text: "You won't be able to revert this!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Yes, delete it!',
        cancelButtonText: 'Cancel',
        reverseButtons: true
    }).then((result) => {
        if (result.isConfirmed) {
            deleteClient(clientId);
        }
    });
}

function deleteClient(clientId) {
    if (!clientId) {
        console.error('No client ID provided');
        return;
    }

    showLoading(true);
    
    fetch(`${API_BASE_URL}/clients/${clientId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Client deleted successfully', 'success');
            // Reload the clients list
            loadClients();
        } else {
            throw new Error(data.error || 'Failed to delete client');
        }
    })
    .catch(error => {
        console.error('Error deleting client:', error);
        showToast(error.message || 'Failed to delete client', 'error');
    })
    .finally(() => {
        showLoading(false);
    });
}
// Add event listener for the save client form
document.addEventListener('DOMContentLoaded', function() {
    const clientForm = document.getElementById('clientForm');
    if (clientForm) {
        clientForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const isEditMode = this.dataset.editMode === 'true';
            const clientId = this.dataset.clientId;
            
            const formData = {
                name: document.getElementById('clientName').value.trim(),
                client_type: document.getElementById('clientType').value,
                phone: document.getElementById('contactNumber').value.trim(),
                email: document.getElementById('email').value.trim(),
                address: document.getElementById('address').value.trim(),
                balance: parseFloat(document.getElementById('initialBalance').value) || 0
            };
            
            // Basic validation
            if (!formData.name) {
                showToast('Client name is required', 'error');
                return;
            }
            
            showLoading(true);
            
            const url = isEditMode ? 
                `${API_BASE_URL}/clients/${clientId}` : 
                `${API_BASE_URL}/clients`;
                
            const method = isEditMode ? 'PUT' : 'POST';
            
            fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showToast(
                        isEditMode ? 'Client updated successfully' : 'Client added successfully', 
                        'success'
                    );
                    
                    // Close the modal
                    const modal = bootstrap.Modal.getInstance(document.getElementById('addClientModal'));
                    if (modal) modal.hide();
                    
                    // Reset form and reload clients
                    clientForm.reset();
                    delete clientForm.dataset.editMode;
                    delete clientForm.dataset.clientId;
                    
                    // Reload clients list
                    loadClients();
                } else {
                    throw new Error(data.error || 'Failed to save client');
                }
            })
            .catch(error => {
                console.error('Error saving client:', error);
                showToast(error.message || 'Failed to save client', 'error');
            })
            .finally(() => {
                showLoading(false);
            });
        });
    }
    
    // Reset form when modal is hidden
    const clientModal = document.getElementById('addClientModal');
    if (clientModal) {
        clientModal.addEventListener('hidden.bs.modal', function () {
            const form = document.getElementById('clientForm');
            if (form) {
                form.reset();
                delete form.dataset.editMode;
                delete form.dataset.clientId;
                
                // Reset modal title and button text
                document.getElementById('addClientModalLabel').innerHTML = 
                    '<i class="fas fa-user-plus me-2"></i>Add New Client';
                document.getElementById('saveClient').textContent = 'Save Client';
            }
        });
    }
    
    // Initialize sortable columns
    document.querySelectorAll('.sortable').forEach(header => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', () => handleSort(header.dataset.sort));
    });
    
    // Initialize search functionality
    if (document.getElementById('clientSearch')) {
        initializeSearch();
    }
    
    // Load initial data
    loadClients();
});

// UI Helpers
function showLoading(show) {
    if (show) {
        loadingState.style.display = 'flex';
        clientsTableBody.style.display = 'none';
        emptyState.style.display = 'none';
    } else {
        loadingState.style.display = 'none';
        clientsTableBody.style.display = '';
    }
}

function showEmptyState() {
    emptyState.style.display = 'flex';
    clientsTableBody.style.display = 'none';
    loadingState.style.display = 'none';
}

function showError(message) {
    showToast(message, 'error');
}

function showToast(message, type = 'info') {
    // You can implement a more sophisticated toast notification system
    alert(`${type.toUpperCase()}: ${message}`);
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

function getStatusBadgeClass(status) {
    const statusClasses = {
        'Active': 'success',
        'Pending': 'warning',
        'Inactive': 'danger'
    };
    return statusClasses[status] || 'secondary';
}

function escapeHtml(unsafe) {
    if (!unsafe) return '';
    return unsafe
        .toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Utility: Debounce function to limit how often a function is called
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
