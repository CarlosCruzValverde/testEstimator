// Helper function for consistent currency formatting
function formatCurrency(value) {
    return parseFloat(value || 0).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

// Format input as currency while typing
function formatInputAsCurrency(input) {
    // Store cursor position
    let cursorPosition = input.selectionStart;
    let originalLength = input.value.length;
    
    // Get value and remove all non-digit characters except decimal point
    let value = input.value.replace(/[^\d.]/g, '');
    
    // If empty, set to 0
    if (value === '') {
        value = '0';
    }
    
    // Parse as float
    let number = parseFloat(value);
    
    // If not a valid number, set to 0
    if (isNaN(number)) {
        number = 0;
    }
    
    // Format with commas and 2 decimal places
    input.value = number.toLocaleString('en-US', {
        style: 'decimal',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
    
    // Adjust cursor position
    let newLength = input.value.length;
    cursorPosition = cursorPosition + (newLength - originalLength);
    input.setSelectionRange(cursorPosition, cursorPosition);
    
    return number; // Return the numeric value
}

// Precise calculation helper (handles floating-point issues)
function calculateWithTax(baseValue, percentage) {
    // Convert to cents (integers) to avoid floating-point errors
    const baseInCents = Math.round(baseValue * 100);
    const taxInCents = Math.round(baseInCents * (percentage || 0) / 100);
    const totalInCents = baseInCents + taxInCents;

    // Convert back to dollars
    return totalInCents / 100;
}

let calculatedBaseCosts = {
    awg: 0,
    conduit: 0,
    misc: 0,
    equipment: 0
};

document.addEventListener('DOMContentLoaded', function () {
    // Load existing data from previous estimations
    loadEstimationData();

    // Set up event listeners
    setupEventListeners();
    
    // Set up currency input formatting
    setupCurrencyInputs();
});

function setupCurrencyInputs() {
    const currencyInputs = [
        document.getElementById('total-submitted'),
        document.getElementById('approved-amount')
    ];
    
    currencyInputs.forEach(input => {
        if (!input) return;
        
        input.addEventListener('input', function(e) {
            formatInputAsCurrency(this);
            calculateAllTotals();
        });
        
        input.addEventListener('blur', function() {
            formatInputAsCurrency(this);
        });
        
        // Initial format if value exists
        if (input.value) {
            formatInputAsCurrency(input);
        }
    });
}

function loadEstimationData() {
    const projectId = document.getElementById('projectId').value;

    fetch(`/portfolio/get_estimation_data?project_id=${projectId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Calculate all base costs with precise tax calculations
                calculatedBaseCosts.awg = calculateWithTax(data.awg_total, data.tax_percentage);
                calculatedBaseCosts.conduit = calculateWithTax(data.conduit_total, data.tax_percentage);
                calculatedBaseCosts.misc = calculateWithTax(data.misc_total, data.tax_percentage);
                calculatedBaseCosts.equipment = calculateWithTax(data.equipment_total, data.tax_percentage);

                // Populate base costs using stored values
                document.getElementById('awg-base-cost').textContent = `$${formatCurrency(calculatedBaseCosts.awg)}`;
                document.getElementById('conduit-base-cost').textContent = `$${formatCurrency(calculatedBaseCosts.conduit)}`;
                document.getElementById('misc-base-cost').textContent = `$${formatCurrency(calculatedBaseCosts.misc)}`;
                document.getElementById('equipment-base-cost').textContent = `$${formatCurrency(calculatedBaseCosts.equipment)}`;
                document.getElementById('labor-base-cost').textContent = `$${formatCurrency(data.labor_total)}`;
                document.getElementById('low-voltage-base-cost').textContent = `$${formatCurrency(data.low_voltage_total)}`;

                // Set charger count if available
                if (data.chargers_count) {
                    document.getElementById('chargers-count').textContent = data.chargers_count;
                }

                // Set approval radio buttons
                if (data.approved !== undefined) {
                    const radioId = data.approved ? 'approved-yes' : 'approved-no';
                    document.getElementById(radioId).checked = true;
                }

                // Set total submitted and approved amount if available
                if (data.total_submitted !== undefined) {
                    document.getElementById('total-submitted').value = formatCurrency(data.total_submitted);
                }
                if (data.approved_amount !== undefined) {
                    document.getElementById('approved-amount').value = formatCurrency(data.approved_amount);
                }

                // Calculate initial totals
                calculateAllTotals();
            }
        });
}

function setupEventListeners() {
    // Markup inputs
    document.querySelectorAll('.markup-input').forEach(input => {
        input.addEventListener('input', calculateAllTotals);
    });

    // Base cost inputs
    document.querySelectorAll('.base-input').forEach(input => {
        input.addEventListener('input', calculateAllTotals);
    });

    // Percentage inputs for tax and overhead
    document.getElementById('tax-percentage').addEventListener('input', calculateAllTotals);
    document.getElementById('overhead-percentage').addEventListener('input', calculateAllTotals);

    // listener for total-submitted input
    document.getElementById('total-submitted').addEventListener('input', calculateAllTotals);
}

function calculateAllTotals() {
    // Calculate each category
    calculateCategoryTotal('awg');
    calculateCategoryTotal('conduit');
    calculateCategoryTotal('misc');
    calculateCategoryTotal('equipment');
    calculateCategoryTotal('labor');
    calculateCategoryTotal('low-voltage');
    calculateCategoryTotal('permits');

    // Calculate Income Tax (30% of sum of profits from specific categories)
    calculateIncomeTax();

    // Calculate Overhead Margin (8.5% of grand subtotal of specific categories)
    calculateOverheadMargin();

    // Calculate grand totals
    calculateGrandTotals();

    calculatePricePerChargerFromSubmitted();
}

function calculateCategoryTotal(category) {
    const baseCostElement = document.getElementById(`${category}-base-cost`);
    const baseCost = parseFloat(baseCostElement.textContent.replace(/[^0-9.-]/g, '')) ||
        parseFloat(baseCostElement.value) || 0;
    const markup = parseFloat(document.getElementById(`${category}-markup`).value) || 1.0;

    const subtotal = baseCost * markup;
    const profit = subtotal - baseCost;

    document.getElementById(`${category}-subtotal`).textContent = `$${formatCurrency(subtotal)}`;
    document.getElementById(`${category}-profit`).textContent = `$${formatCurrency(profit)}`;
}

function calculateIncomeTax() {
    const taxableCategories = ['awg', 'conduit', 'misc', 'equipment', 'labor', 'low-voltage', 'permits'];
    let totalProfit = 0;

    taxableCategories.forEach(category => {
        const profit = parseFloat(document.getElementById(`${category}-profit`).textContent.replace(/[^0-9.-]/g, '')) || 0;
        totalProfit += profit;
    });

    const taxPercentage = parseFloat(document.getElementById('tax-percentage').value) || 30;
    const incomeTax = totalProfit * (taxPercentage / 100);

    // Update percentage display
    document.getElementById('tax-percentage-display').textContent = taxPercentage;

    // Update tax fields
    document.getElementById('tax-base-cost').textContent = `$${formatCurrency(totalProfit)}`;
    document.getElementById('tax-base-cost1').textContent = `$${formatCurrency(totalProfit)}`;
    document.getElementById('tax-subtotal').textContent = `$${formatCurrency(incomeTax)}`;
    document.getElementById('tax-summary').textContent = `$${formatCurrency(incomeTax)}`;
}


function calculateOverheadMargin() {
    const overheadCategories = ['awg', 'conduit', 'misc', 'equipment', 'labor', 'low-voltage', 'permits'];
    let grandSubtotal = 0;

    overheadCategories.forEach(category => {
        const subtotal = parseFloat(document.getElementById(`${category}-subtotal`).textContent.replace(/[^0-9.-]/g, '')) || 0;
        grandSubtotal += subtotal;
    });

    const overheadPercentage = parseFloat(document.getElementById('overhead-percentage').value) || 8.5;
    const overheadMargin = grandSubtotal * (overheadPercentage / 100);

    // Update percentage display
    document.getElementById('overhead-percentage-display').textContent = overheadPercentage;

    // Update overhead fields
    document.getElementById('overhead-base-cost').textContent = `$${formatCurrency(grandSubtotal)}`;
    document.getElementById('overhead-subtotal').textContent = `$${formatCurrency(overheadMargin)}`;
    document.getElementById('overhead-summary').textContent = `$${formatCurrency(overheadMargin)}`;
}


function calculateGrandTotals() {
    const categories = ['awg', 'conduit', 'misc', 'equipment', 'labor', 'low-voltage', 'permits', 'tax', 'overhead'];
    const categories1 = ['awg', 'conduit', 'misc', 'equipment', 'labor', 'permits', 'tax', 'overhead'];
    let grandSubtotal = 0;
    let grandTotal = 0;
    let grandSubtotal1 = 0;
    let grandTotal1 = 0;

    // Calculate grand subtotal (without tax and overhead)
    const mainCategories = ['awg', 'conduit', 'misc', 'equipment', 'labor', 'low-voltage', 'permits'];
    mainCategories.forEach(category => {
        const subtotal = parseFloat(document.getElementById(`${category}-subtotal`).textContent.replace(/[^0-9.-]/g, '')) || 0;
        grandSubtotal += subtotal;
    });

    // Calculate grand subtotal1 (without tax, overhead, and low voltage)
    const mainCategories1 = ['awg', 'conduit', 'misc', 'equipment', 'labor', 'permits'];
    mainCategories1.forEach(category => {
        const subtotal = parseFloat(document.getElementById(`${category}-subtotal`).textContent.replace(/[^0-9.-]/g, '')) || 0;
        grandSubtotal1 += subtotal;
    });

    // Calculate grand total (including tax and overhead)
    categories.forEach(category => {
        const subtotal = parseFloat(document.getElementById(`${category}-subtotal`).textContent.replace(/[^0-9.-]/g, '')) || 0;
        grandTotal += subtotal;
    });

    // Calculate grand total1 with out low voltage (including tax and overhead)
    categories1.forEach(category => {
        const subtotal = parseFloat(document.getElementById(`${category}-subtotal`).textContent.replace(/[^0-9.-]/g, '')) || 0;
        grandTotal1 += subtotal;
    });

    // Update displays
    document.getElementById('grand-subtotal').textContent = `$${formatCurrency(grandSubtotal)}`;
    document.getElementById('grand-total').textContent = `$${formatCurrency(grandTotal)}`;

    // Pass the value directly to the other function
    calculatePricePerCharger(grandTotal1);
}

function calculatePricePerCharger(grandTotal1) {
    const chargersCount = parseInt(document.getElementById('chargers-count').textContent) || 0;

    if (chargersCount > 0) {
        const pricePerCharger = grandTotal1 / chargersCount;
        document.getElementById('price-per-charger').textContent = `$${formatCurrency(pricePerCharger)}`;
    } else {
        document.getElementById('price-per-charger').textContent = '$0.00';
    }
}

function calculatePricePerChargerFromSubmitted() {
    const chargersCount = parseInt(document.getElementById('chargers-count').textContent) || 0;
    const totalSubmitted = parseFloat(document.getElementById('total-submitted').value) || 0;
    const lowVoltageBaseCost = parseFloat(
        document.getElementById('low-voltage-base-cost').textContent.replace(/[^0-9.-]/g, '')
    ) || 0;

    if (chargersCount > 0 && totalSubmitted > 0) {
        const pricePerCharger = (totalSubmitted - lowVoltageBaseCost) / chargersCount;
        document.getElementById('price-per-charger-submitted').textContent = `$${formatCurrency(pricePerCharger)}`;
    } else {
        document.getElementById('price-per-charger-submitted').textContent = '$0.00';
    }
}


// Form submission
document.getElementById('summaryForm').addEventListener('submit', function (e) {
    e.preventDefault();

    const formData = {
        project_id: document.getElementById('projectId').value,

        // AWG
        awg_base_cost: calculatedBaseCosts.awg,
        awg_markup: parseFloat(document.getElementById('awg-markup').value) || 1.0,
        awg_subtotal: parseFloat(document.getElementById('awg-subtotal').textContent.replace(/[^0-9.-]/g, '')) || 0,
        awg_profit: parseFloat(document.getElementById('awg-profit').textContent.replace(/[^0-9.-]/g, '')) || 0,

        // Conduit
        conduit_base_cost: calculatedBaseCosts.conduit,
        conduit_markup: parseFloat(document.getElementById('conduit-markup').value) || 1.0,
        conduit_subtotal: parseFloat(document.getElementById('conduit-subtotal').textContent.replace(/[^0-9.-]/g, '')) || 0,
        conduit_profit: parseFloat(document.getElementById('conduit-profit').textContent.replace(/[^0-9.-]/g, '')) || 0,

        // Miscellaneous
        misc_base_cost: calculatedBaseCosts.misc,
        misc_markup: parseFloat(document.getElementById('misc-markup').value) || 1.0,
        misc_subtotal: parseFloat(document.getElementById('misc-subtotal').textContent.replace(/[^0-9.-]/g, '')) || 0,
        misc_profit: parseFloat(document.getElementById('misc-profit').textContent.replace(/[^0-9.-]/g, '')) || 0,

        // Equipment
        equipment_base_cost: calculatedBaseCosts.equipment,
        equipment_markup: parseFloat(document.getElementById('equipment-markup').value) || 1.0,
        equipment_subtotal: parseFloat(document.getElementById('equipment-subtotal').textContent.replace(/[^0-9.-]/g, '')) || 0,
        equipment_profit: parseFloat(document.getElementById('equipment-profit').textContent.replace(/[^0-9.-]/g, '')) || 0,

        // Labor
        labor_base_cost: parseFloat(document.getElementById('labor-base-cost').textContent.replace(/[^0-9.-]/g, '')) || 0,
        labor_markup: parseFloat(document.getElementById('labor-markup').value) || 1.0,
        labor_subtotal: parseFloat(document.getElementById('labor-subtotal').textContent.replace(/[^0-9.-]/g, '')) || 0,
        labor_profit: parseFloat(document.getElementById('labor-profit').textContent.replace(/[^0-9.-]/g, '')) || 0,

        // Low Voltage
        low_voltage_base_cost: parseFloat(document.getElementById('low-voltage-base-cost').textContent.replace(/[^0-9.-]/g, '')) || 0,
        low_voltage_markup: parseFloat(document.getElementById('low-voltage-markup').value) || 1.0,
        low_voltage_subtotal: parseFloat(document.getElementById('low-voltage-subtotal').textContent.replace(/[^0-9.-]/g, '')) || 0,
        low_voltage_profit: parseFloat(document.getElementById('low-voltage-profit').textContent.replace(/[^0-9.-]/g, '')) || 0,

        // Permits
        permits_base_cost: parseFloat(document.getElementById('permits-base-cost').value) || 0,
        permits_markup: parseFloat(document.getElementById('permits-markup').value) || 1.0,
        permits_subtotal: parseFloat(document.getElementById('permits-subtotal').textContent.replace(/[^0-9.-]/g, '')) || 0,
        permits_profit: parseFloat(document.getElementById('permits-profit').textContent.replace(/[^0-9.-]/g, '')) || 0,

        // Income Tax
        tax_base_cost: parseFloat(document.getElementById('tax-base-cost').textContent.replace(/[^0-9.-]/g, '')) || 0,
        tax_percentage: parseFloat(document.getElementById('tax-percentage').value) || 0,
        tax_subtotal: parseFloat(document.getElementById('tax-subtotal').textContent.replace(/[^0-9.-]/g, '')) || 0,

        // Overhead
        overhead_base_cost: parseFloat(document.getElementById('overhead-base-cost').textContent.replace(/[^0-9.-]/g, '')) || 0,
        overhead_percentage: parseFloat(document.getElementById('overhead-percentage').value) || 0,
        overhead_subtotal: parseFloat(document.getElementById('overhead-subtotal').textContent.replace(/[^0-9.-]/g, '')) || 0,

        // Totals
        grand_subtotal: parseFloat(document.getElementById('grand-subtotal').textContent.replace(/[$,]/g, '')) || 0,
        grand_total: parseFloat(document.getElementById('grand-total').textContent.replace(/[$,]/g, '')) || 0,

        // Charger Information
        price_per_charger: parseFloat(document.getElementById('price-per-charger').textContent.replace(/[$,]/g, '')) || 0,

        // Approval
        approved: document.querySelector('input[name="approved"]:checked')?.value === 'true',

        total_submitted: parseFloat(document.getElementById('total-submitted').value) || 0,
        approved_amount: parseFloat(document.getElementById('approved-amount').value) || 0,

        price_per_charger_submitted: parseFloat(document.getElementById('price-per-charger-submitted').textContent.replace(/[$,]/g, '')) || 0,

        // Notes
        notes: document.getElementById('summary-notes').value
    };

    saveSummary(formData);
});

function saveSummary(formData) {
    fetch('/portfolio/save_summary', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Success!',
                    text: 'Project summary saved successfully!'
                }).then(() => {
                    // Redirect to the next tab or wherever appropriate
                    window.location.href = `/portfolio/projects?project_id=${formData.project_id}`;
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: data.message || 'Failed to save summary'
                });
            }
        });
}
