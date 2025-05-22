// Add ripple effect to buttons
function createRipple(event) {
    if (!event.currentTarget) return;
    
    const button = event.currentTarget;
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    
    // Remove any existing ripples
    const existingRipples = button.getElementsByClassName('ripple');
    while (existingRipples[0]) {
        existingRipples[0].remove();
    }
    
    button.appendChild(ripple);
    
    // Remove ripple after animation completes
    setTimeout(() => {
        if (ripple.parentNode === button) {
            ripple.remove();
        }
    }, 600);
}

// Transactions Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Add ripple effect to the Add Transaction button
    const addButton = document.getElementById('addTransactionBtn');
    if (addButton) {
        addButton.addEventListener('click', createRipple);
    }
    
    // Initialize search functionality
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    const clearSearchBtn = document.getElementById('clearSearch');
    let searchTimeout;
    
    if (searchInput && searchResults && clearSearchBtn) {
        // Toggle clear button visibility
        const toggleClearButton = () => {
            clearSearchBtn.style.display = searchInput.value.trim() ? 'block' : 'none';
        };
        
        // Clear search input and results
        const clearSearch = () => {
            searchInput.value = '';
            searchInput.focus();
            searchResults.classList.remove('active');
            clearSearchBtn.style.display = 'none';
            // Trigger any additional clear logic here
        };
        
        // Initialize clear button state
        toggleClearButton();
        
        // Handle search input
        const handleSearch = () => {
            const query = searchInput.value.trim();
            clearSearchBtn.style.display = query ? 'block' : 'none';
            
            if (query.length > 1) {
                // Show loading state
                searchResults.innerHTML = '<div class="search-result-item"><i class="fas fa-spinner fa-spin"></i> Searching transactions...</div>';
                searchResults.classList.add('active');
                
                // Clear previous timeout
                clearTimeout(searchTimeout);
                
                // Set new timeout for debouncing
                searchTimeout = setTimeout(() => {
                    // This is a mock response - replace with actual API call
                    const mockResults = [
                        { id: 1, name: 'Sample Transaction #1', type: 'credit', amount: 1500, date: '2023-05-22' },
                        { id: 2, name: 'Sample Transaction #2', type: 'debit', amount: 750, date: '2023-05-21' },
                        { id: 3, name: 'Sample Payment #3', type: 'credit', amount: 2500, date: '2023-05-20' },
                    ];
                    
                    // Filter mock results based on query
                    const filteredResults = mockResults.filter(item => 
                        item.name.toLowerCase().includes(query.toLowerCase()) ||
                        item.amount.toString().includes(query) ||
                        item.date.includes(query)
                    );
                    
                    if (filteredResults.length > 0) {
                        let resultsHTML = '';
                        filteredResults.forEach(result => {
                            const icon = result.type === 'credit' ? 'arrow-down' : 'arrow-up';
                            const amountClass = result.type === 'credit' ? 'credit-amount' : 'debit-amount';
                            resultsHTML += `
                                <div class="search-result-item" data-id="${result.id}">
                                    <i class="fas fa-${icon}"></i>
                                    <div style="flex: 1;">
                                        <div style="font-weight: 500;">${result.name}</div>
                                        <div style="display: flex; justify-content: space-between; margin-top: 3px;">
                                            <small class="text-muted">${new Date(result.date).toLocaleDateString()}</small>
                                            <small class="${amountClass}" style="font-weight: 600;">₹${result.amount.toLocaleString()}</small>
                                        </div>
                                    </div>
                                </div>`;
                        });
                        searchResults.innerHTML = resultsHTML;
                    } else {
                        searchResults.innerHTML = `
                            <div class="search-result-item">
                                <i class="fas fa-search"></i>
                                <div>No results found for "${query}"</div>
                            </div>`;
                    }
                }, 500); // 500ms debounce time
            } else if (query.length === 0) {
                searchResults.classList.remove('active');
            } else {
                searchResults.innerHTML = '<div class="search-result-item"><i class="fas fa-info-circle"></i> Enter at least 2 characters to search</div>';
                searchResults.classList.add('active');
            }
        };
        
        // Event listeners
        searchInput.addEventListener('input', handleSearch);
        searchInput.addEventListener('focus', () => {
            if (searchInput.value.trim().length > 1) {
                searchResults.classList.add('active');
            }
        });
        
        clearSearchBtn.addEventListener('click', clearSearch);
        
        // Close search results when clicking outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
                searchResults.classList.remove('active');
            }
        });
        
        // Handle keyboard navigation
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                searchResults.classList.remove('active');
                searchInput.blur();
            }
        });
    }
    
    // Initialize date range picker
    const dateRangeInput = document.getElementById('dateRange');
    if (dateRangeInput) {
        flatpickr(dateRangeInput, {
            mode: 'range',
            dateFormat: 'Y-m-d',
            maxDate: 'today',
            defaultDate: [dateRangeInput.dataset.startDate || '', dateRangeInput.dataset.endDate || ''],
            onChange: function(selectedDates, dateStr) {
                if (selectedDates.length === 2) {
                    const [startDate, endDate] = selectedDates;
                    const url = new URL(window.location.href);
                    url.searchParams.set('start_date', startDate.toISOString().split('T')[0]);
                    url.searchParams.set('end_date', endDate.toISOString().split('T')[0]);
                    window.location.href = url.toString();
                }
            }
        });
    }

    // Handle contact search
    const contactSearch = document.getElementById('contactSearch');
    const contactResults = document.getElementById('contactResults');
    const contactIdInput = document.getElementById('contactId');
    
    if (contactSearch) {
        let searchTimeout;
        
        contactSearch.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length < 2) {
                contactResults.innerHTML = '';
                contactResults.classList.add('d-none');
                contactIdInput.value = '';
                return;
            }
            
            searchTimeout = setTimeout(() => {
                fetch(`/api/contacts/search?q=${encodeURIComponent(query)}`)
                    .then(response => response.json())
                    .then(contacts => {
                        contactResults.innerHTML = '';
                        
                        if (contacts.length === 0) {
                            const noResults = document.createElement('div');
                            noResults.className = 'dropdown-item';
                            noResults.textContent = 'No contacts found';
                            contactResults.appendChild(noResults);
                        } else {
                            contacts.forEach(contact => {
                                const item = document.createElement('a');
                                item.href = '#';
                                item.className = 'dropdown-item d-flex justify-content-between align-items-center';
                                item.innerHTML = `
                                    <div>
                                        <div class="fw-bold">${contact.name}</div>
                                        <small class="text-muted">${contact.phone}</small>
                                    </div>
                                    <span class="badge bg-primary rounded-pill">${contact.transaction_count || 0}</span>
                                `;
                                
                                item.addEventListener('click', function(e) {
                                    e.preventDefault();
                                    contactSearch.value = contact.name;
                                    contactIdInput.value = contact.id;
                                    contactResults.classList.add('d-none');
                                    
                                    // Update URL with contact filter
                                    const url = new URL(window.location.href);
                                    url.searchParams.set('contact_id', contact.id);
                                    url.searchParams.delete('q');
                                    window.location.href = url.toString();
                                });
                                
                                contactResults.appendChild(item);
                            });
                        }
                        
                        contactResults.classList.remove('d-none');
                    })
                    .catch(error => {
                        console.error('Error searching contacts:', error);
                        contactResults.innerHTML = '';
                        const errorItem = document.createElement('div');
                        errorItem.className = 'dropdown-item text-danger';
                        errorItem.textContent = 'Error searching contacts';
                        contactResults.appendChild(errorItem);
                        contactResults.classList.remove('d-none');
                    });
            }, 300);
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!contactSearch.contains(e.target) && !contactResults.contains(e.target)) {
                contactResults.classList.add('d-none');
            }
        });
    }
    
    // Handle new transaction form submission
    const newTransactionForm = document.getElementById('newTransactionForm');
    if (newTransactionForm) {
        newTransactionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const transactionData = {
                date: formData.get('date'),
                contact_id: formData.get('contact_id'),
                type: formData.get('type'),
                amount: parseFloat(formData.get('amount')),
                description: formData.get('description')
            };
            
            // Show loading state
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';
            
            // Send request
            fetch('/transaction/new', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                },
                body: JSON.stringify(transactionData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Show success message
                    Swal.fire({
                        title: 'Success!',
                        text: 'Transaction added successfully',
                        icon: 'success',
                        timer: 2000,
                        showConfirmButton: false,
                        willClose: () => {
                            // Close modal and refresh page
                            const modal = bootstrap.Modal.getInstance(document.getElementById('newTransactionModal'));
                            modal.hide();
                            window.location.reload();
                        }
                    });
                } else {
                    throw new Error(data.message || 'Failed to add transaction');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire({
                    title: 'Error!',
                    text: error.message || 'Failed to add transaction',
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
            })
            .finally(() => {
                // Reset button state
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            });
        });
    }
    
    // Toggle between credit/debit in new transaction form
    const transactionTypeBtns = document.querySelectorAll('.transaction-type-btn');
    transactionTypeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const type = this.dataset.type;
            const amountInput = document.getElementById('amount');
            
            // Update active state
            document.querySelectorAll('.transaction-type-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // Update hidden input
            document.getElementById('transactionType').value = type;
            
            // Update amount input placeholder
            amountInput.placeholder = `Enter ${type} amount`;
            
            // Focus amount input
            amountInput.focus();
        });
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Format currency inputs
    const currencyInputs = document.querySelectorAll('.currency-input');
    currencyInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            // Remove non-numeric characters except decimal point
            let value = this.value.replace(/[^0-9.]/g, '');
            
            // Ensure only one decimal point
            const decimalCount = (value.match(/\./g) || []).length;
            if (decimalCount > 1) {
                value = value.substring(0, value.lastIndexOf('.'));
            }
            
            // Limit to 2 decimal places
            const parts = value.split('.');
            if (parts.length > 1 && parts[1].length > 2) {
                value = parts[0] + '.' + parts[1].substring(0, 2);
            }
            
            this.value = value;
        });
    });
    
    // Handle clear filters button
    const clearFiltersBtn = document.getElementById('clearFilters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function() {
            window.location.href = window.location.pathname;
        });
    }
});
