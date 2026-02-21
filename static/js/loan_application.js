// Loan Application JavaScript

// Loan limits and rates configuration
const loanConfig = {
    Personal: { min: 1000, max: 50000, rate: 10.5 },
    Home: { min: 50000, max: 500000, rate: 8.5 },
    Car: { min: 10000, max: 100000, rate: 9.5 },
    Education: { min: 10000, max: 200000, rate: 7.5 },
    Business: { min: 10000, max: 250000, rate: 12.5 },
    Credit: { min: 1000, max: 25000, rate: 14.5 }
};

// Update loan limits when loan type changes
function updateLoanLimits() {
    const loanType = document.getElementById('loan_type').value;
    const amountInput = document.getElementById('requested_amount');
    const amountHelp = document.getElementById('amountHelp');
    const propertyField = document.getElementById('propertyValueField');
    const downPaymentField = document.getElementById('downPaymentField');

    if (loanType && loanConfig[loanType]) {
        const config = loanConfig[loanType];
        amountInput.min = config.min;
        amountInput.max = config.max;
        amountHelp.textContent = `Min: ₹${config.min.toLocaleString()} | Max: ₹${config.max.toLocaleString()}`;

        // Show/hide property value and down payment fields
        if (loanType === 'Home') {
            propertyField.style.display = 'block';
            downPaymentField.style.display = 'block';
        } else if (loanType === 'Car') {
            propertyField.style.display = 'none';
            downPaymentField.style.display = 'block';
        } else {
            propertyField.style.display = 'none';
            downPaymentField.style.display = 'none';
        }

        // Set default amount to minimum
        if (!amountInput.value || parseFloat(amountInput.value) < config.min) {
            amountInput.value = config.min;
        }

        // Calculate loan
        calculateLoan();
    } else {
        amountInput.min = 1000;
        amountInput.max = 500000;
        amountHelp.textContent = 'Select a loan type first';
        propertyField.style.display = 'none';
        downPaymentField.style.display = 'none';
    }
}

// Calculate loan EMI and totals
function calculateLoan() {
    const loanType = document.getElementById('loan_type').value;
    const amount = parseFloat(document.getElementById('requested_amount').value) || 0;
    const tenureMonths = parseInt(document.getElementById('tenure_months').value) || 0;

    if (!loanType || !amount || !tenureMonths) {
        resetCalculator();
        return;
    }

    const rate = loanConfig[loanType].rate;
    const monthlyRate = rate / 100 / 12;

    // Calculate EMI using standard formula
    const emi = (amount * monthlyRate * Math.pow(1 + monthlyRate, tenureMonths)) /
                (Math.pow(1 + monthlyRate, tenureMonths) - 1);

    const totalPayment = emi * tenureMonths;
    const totalInterest = totalPayment - amount;

    // Update calculator display
    document.getElementById('monthlyEMI').textContent = '₹' + emi.toLocaleString('en-IN', { maximumFractionDigits: 2 });
    document.getElementById('totalInterest').textContent = '₹' + totalInterest.toLocaleString('en-IN', { maximumFractionDigits: 2 });
    document.getElementById('totalPayment').textContent = '₹' + totalPayment.toLocaleString('en-IN', { maximumFractionDigits: 2 });

    // Check eligibility
    checkEligibility();
}

// Reset calculator display
function resetCalculator() {
    document.getElementById('monthlyEMI').textContent = '₹0';
    document.getElementById('totalInterest').textContent = '₹0';
    document.getElementById('totalPayment').textContent = '₹0';
}

// Check loan eligibility
function checkEligibility() {
    const monthlyIncome = parseFloat(document.getElementById('monthly_income').value) || 0;
    const existingLoans = parseFloat(document.getElementById('existing_loans').value) || 0;
    const existingEMI = parseFloat(document.getElementById('existing_emi').value) || 0;
    const coApplicantIncome = parseFloat(document.getElementById('co_applicant_income').value) || 0;
    const emiText = document.getElementById('monthlyEMI').textContent.replace('₹', '').replace(/,/g, '');
    const emi = parseFloat(emiText) || 0;

    const totalIncome = monthlyIncome + coApplicantIncome;
    const totalEMI = existingLoans + existingEMI + emi;
    const emiRatio = totalIncome > 0 ? (totalEMI / totalIncome) * 100 : 0;

    // Update eligibility display
    document.getElementById('incomeEligibility').textContent =
        totalIncome >= 2000 ? 'Eligible' : 'Not Eligible';
    document.getElementById('emiRatio').textContent = emiRatio.toFixed(1) + '%';

    const eligibilityStatus = document.getElementById('eligibilityStatus');
    const statusIcon = eligibilityStatus.querySelector('i');
    const statusText = eligibilityStatus.querySelector('span');

    if (totalIncome < 2000) {
        eligibilityStatus.className = 'eligibility-status status-error';
        statusIcon.className = 'fas fa-times-circle';
        statusText.textContent = 'Minimum income requirement not met';
    } else if (emiRatio > 50) {
        eligibilityStatus.className = 'eligibility-status status-warning';
        statusIcon.className = 'fas fa-exclamation-triangle';
        statusText.textContent = 'EMI ratio too high - may affect approval';
    } else if (emiRatio > 40) {
        eligibilityStatus.className = 'eligibility-status status-review';
        statusIcon.className = 'fas fa-clock';
        statusText.textContent = 'EMI ratio acceptable - under review';
    } else {
        eligibilityStatus.className = 'eligibility-status status-success';
        statusIcon.className = 'fas fa-check-circle';
        statusText.textContent = 'Good eligibility - high chance of approval';
    }
}

// Form validation before submission
function validateForm() {
    const loanType = document.getElementById('loan_type').value;
    const amount = parseFloat(document.getElementById('requested_amount').value);
    const tenure = parseInt(document.getElementById('tenure_months').value);
    const monthlyIncome = parseFloat(document.getElementById('monthly_income').value);

    if (!loanType) {
        alert('Please select a loan type.');
        return false;
    }

    if (!loanConfig[loanType]) {
        alert('Invalid loan type selected.');
        return false;
    }

    const config = loanConfig[loanType];
    if (amount < config.min || amount > config.max) {
        alert(`Loan amount must be between ₹${config.min.toLocaleString()} and ₹${config.max.toLocaleString()}.`);
        return false;
    }

    if (tenure < 12 || tenure > 360) {
        alert('Loan tenure must be between 12 and 360 months.');
        return false;
    }

    if (monthlyIncome < 1000) {
        alert('Monthly income must be at least ₹1,000.');
        return false;
    }

    return true;
}

// Initialize form when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Set default values
    updateLoanLimits();

    // Add form validation
    const form = document.getElementById('loanApplicationForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validateForm()) {
                e.preventDefault();
                return false;
            }

            // Show loading state
            const submitBtn = document.getElementById('submitBtn');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
        });
    }

    // Auto-calculate when inputs change
    const inputs = ['requested_amount', 'tenure_months', 'monthly_income', 'existing_loans', 'existing_emi', 'co_applicant_income'];
    inputs.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', function() {
                if (['requested_amount', 'tenure_months'].includes(id)) {
                    calculateLoan();
                } else {
                    checkEligibility();
                }
            });
        }
    });
});

// Handle success modal display (if redirected back with success)
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('success') === '1') {
        const applicationId = urlParams.get('app_id') || 'APP001';
        document.getElementById('applicationId').textContent = applicationId;

        const modal = new bootstrap.Modal(document.getElementById('successModal'));
        modal.show();
    }
});
