// Main JavaScript for AI Credit Scoring System

document.addEventListener('DOMContentLoaded', function() {
    // Form validation for customer ID input
    const customerIdForm = document.querySelector('form[action*="predict"]');
    if (customerIdForm) {
        customerIdForm.addEventListener('submit', function(e) {
            const customerId = document.getElementById('customer_id');
            if (customerId && customerId.value.trim() === '') {
                e.preventDefault();
                alert('Please enter a valid Customer ID.');
                customerId.focus();
                return false;
            }
        });
    }

    // Form validation for add customer form
    const addCustomerForm = document.querySelector('form[action*="add_customer"]');
    if (addCustomerForm) {
        addCustomerForm.addEventListener('submit', function(e) {
            const requiredFields = addCustomerForm.querySelectorAll('input[required], select[required], textarea[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (field.value.trim() === '') {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });

            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields.');
                return false;
            }

            // Show loading state
            const submitBtn = addCustomerForm.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adding Customer...';
            }
        });
    }

    // Auto-format number inputs
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value && this.step === '0.01') {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    });

    // Confirm before re-running predictions
    const rerunButtons = document.querySelectorAll('button[onclick*="predict"]');
    rerunButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to re-run the credit score prediction for this customer?')) {
                e.preventDefault();
                return false;
            }
        });
    });

    // Smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (!alert.querySelector('.btn-close')) {
            setTimeout(() => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            }, 5000);
        }
    });

    // Table sorting functionality (basic)
    const tables = document.querySelectorAll('.table');
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        headers.forEach((header, index) => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', function() {
                sortTable(table, index);
            });
        });
    });

    function sortTable(table, column) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const isNumeric = rows.some(row => !isNaN(parseFloat(row.cells[column].textContent.trim())));

        rows.sort((a, b) => {
            const aVal = a.cells[column].textContent.trim();
            const bVal = b.cells[column].textContent.trim();

            if (isNumeric) {
                return parseFloat(aVal) - parseFloat(bVal);
            } else {
                return aVal.localeCompare(bVal);
            }
        });

        rows.forEach(row => tbody.appendChild(row));
    }

    // Print functionality enhancement
    const printButtons = document.querySelectorAll('button[onclick*="print"]');
    printButtons.forEach(button => {
        button.addEventListener('click', function() {
            window.print();
        });
    });

    console.log('AI Credit Scoring System JavaScript loaded successfully');
});
