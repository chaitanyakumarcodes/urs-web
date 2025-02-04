// Chart variables
let salesChart, pointsChart, customerChart, hourlyChart;

// Tab switching function
function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });
    
    // Remove active state from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('border-blue-500', 'text-blue-600');
        btn.classList.add('border-transparent', 'text-gray-500');
    });
    
    // Show selected tab content
    document.getElementById(`${tabName}-tab`).classList.remove('hidden');
    
    // Activate selected tab button
    const activeBtn = document.querySelector(`[data-tab="${tabName}"]`);
    activeBtn.classList.add('border-blue-500', 'text-blue-600');
    activeBtn.classList.remove('border-transparent', 'text-gray-500');
}

// Initialize charts
async function initializeCharts() {
    try {
        const response = await fetch('/api/analytics');
        if (!response.ok) throw new Error('Failed to fetch analytics');
        
        const analytics = await response.json();
        
        // Update summary cards
        document.getElementById('totalSales').textContent = 
            `₹${Object.values(analytics.daily_sales)[Object.values(analytics.daily_sales).length - 1].toFixed(2)}`;
        document.getElementById('pointsIssued').textContent = analytics.points_metrics.total_earned;
        document.getElementById('pointsRedeemed').textContent = analytics.points_metrics.total_redeemed;
        document.getElementById('uniqueCustomers').textContent = analytics.unique_customers;
        document.getElementById('avgTransaction').textContent = analytics.avg_transaction ? analytics.avg_transaction.toFixed(2) : '0.00';

        // Sales Chart
        const salesCtx = document.getElementById('salesChart').getContext('2d');
        if (salesChart) salesChart.destroy();
        salesChart = new Chart(salesCtx, {
            type: 'line',
            data: {
                labels: Object.keys(analytics.daily_sales),
                datasets: [{
                    label: 'Daily Sales (₹)',
                    data: Object.values(analytics.daily_sales),
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '₹' + value;
                            }
                        }
                    }
                }
            }
        });

        // Points Chart
        const pointsCtx = document.getElementById('pointsChart').getContext('2d');
        if (pointsChart) pointsChart.destroy();
        pointsChart = new Chart(pointsCtx, {
            type: 'bar',
            data: {
                labels: ['Points Earned', 'Points Redeemed'],
                datasets: [{
                    label: 'Points',
                    data: [
                        analytics.points_metrics.total_earned,
                        analytics.points_metrics.total_redeemed
                    ],
                    backgroundColor: [
                        'rgba(75, 192, 192, 0.2)',
                        'rgba(255, 99, 132, 0.2)'
                    ],
                    borderColor: [
                        'rgb(75, 192, 192)',
                        'rgb(255, 99, 132)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        // Customer Activity Chart
        const customerCtx = document.getElementById('customerChart').getContext('2d');
        if (customerChart) customerChart.destroy();
        customerChart = new Chart(customerCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(analytics.customer_activity),
                datasets: [{
                    label: 'Active Customers',
                    data: Object.values(analytics.customer_activity),
                    backgroundColor: 'rgba(147, 51, 234, 0.2)',
                    borderColor: 'rgb(147, 51, 234)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });

        // Hourly Distribution Chart
        const hourlyCtx = document.getElementById('hourlyChart').getContext('2d');
        if (hourlyChart) hourlyChart.destroy();
        hourlyChart = new Chart(hourlyCtx, {
            type: 'line',
            data: {
                labels: Object.keys(analytics.hourly_distribution),
                datasets: [{
                    label: 'Transactions',
                    data: Object.values(analytics.hourly_distribution),
                    borderColor: 'rgb(234, 88, 12)',
                    tension: 0.1,
                    fill: true,
                    backgroundColor: 'rgba(234, 88, 12, 0.1)'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error initializing charts:', error);
    }
}

// Fetch and display transactions
async function loadTransactions() {
    try {
        const response = await fetch('/api/transactions');
        const transactions = await response.json();
        
        const tableBody = document.getElementById('transactionsTable');
        tableBody.innerHTML = transactions.map(t => {
            // Format the timestamp properly
            const timestamp = new Date(t.timestamp);
            const formattedDate = timestamp.toLocaleDateString('en-IN', {
                day: 'numeric',
                month: 'numeric',
                year: 'numeric'
            });
            const formattedTime = timestamp.toLocaleTimeString('en-IN', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: true
            });

            return `
                <tr class="hover:bg-gray-50">
                    <td class="px-6 py-4 whitespace-nowrap">${t.id}</td>
                    <td class="px-6 py-4 whitespace-nowrap">₹${t.amount.toFixed(2)}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${t.points_earned}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${t.points_redeemed}</td>
                    <td class="px-6 py-4 whitespace-nowrap">${formattedDate}, ${formattedTime}</td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Error loading transactions:', error);
    }
}

// Setup date range selector
function setupDateRangeSelector() {
    const dateRangeSelector = document.createElement('div');
    dateRangeSelector.className = 'mb-6 bg-white rounded-lg shadow p-4';
    dateRangeSelector.innerHTML = `
        <h3 class="text-lg font-medium mb-4">Select Date Range</h3>
        <div class="flex space-x-4">
            <button onclick="updateDateRange(7)" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">Last 7 Days</button>
            <button onclick="updateDateRange(30)" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">Last 30 Days</button>
            <button onclick="updateDateRange(90)" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">Last 90 Days</button>
            <div class="flex items-center space-x-2">
                <input type="date" id="startDate" class="border rounded px-2 py-1">
                <span>to</span>
                <input type="date" id="endDate" class="border rounded px-2 py-1">
                <button onclick="updateCustomDateRange()" class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">Apply</button>
            </div>
        </div>
    `;
    
    document.querySelector('#analytics-tab').insertBefore(dateRangeSelector, document.querySelector('.grid'));
}

// Update date range
async function updateDateRange(days) {
    try {
        const response = await fetch(`/api/analytics?days=${days}`);
        const analytics = await response.json();
        initializeCharts();
        loadTransactions();
    } catch (error) {
        console.error('Error updating date range:', error);
    }
}

// Update custom date range
async function updateCustomDateRange() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    if (!startDate || !endDate) {
        alert('Please select both start and end dates');
        return;
    }

    try {
        const response = await fetch(`/api/analytics?start=${startDate}&end=${endDate}`);
        const analytics = await response.json();
        initializeCharts();
        loadTransactions();
    } catch (error) {
        console.error('Error updating custom date range:', error);
    }
}

function exportTransactions(format) {
    window.location.href = `/api/export?format=${format}`;
}

// Export transactions
async function exportTransactions(format) {
    try {
        const response = await fetch(`/api/export?format=${format}`);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `transactions_${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('Error exporting transactions:', error);
    }
}

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    loadTransactions();
    
    // Set Check Customer as default tab
    switchTab('check-customer');
    
    // Refresh data every 5 minutes
    setInterval(() => {
        initializeCharts();
        loadTransactions();
    }, 300000);
});

function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });
    
    // Remove active state from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('border-blue-500', 'text-blue-600');
        btn.classList.add('border-transparent', 'text-gray-500');
    });
    
    // Show selected tab content
    document.getElementById(`${tabName}-tab`).classList.remove('hidden');
    
    // Activate selected tab button
    const activeBtn = document.querySelector(`[data-tab="${tabName}"]`);
    activeBtn.classList.add('border-blue-500', 'text-blue-600');
    activeBtn.classList.remove('border-transparent', 'text-gray-500');
}