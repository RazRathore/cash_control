// Transactions Page JavaScript
document.addEventListener('DOMContentLoaded', function() {
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
