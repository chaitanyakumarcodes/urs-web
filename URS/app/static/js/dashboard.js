let salesChart, pointsChart;

// Initialize charts
async function initializeCharts() {
    try {
        const response = await fetch('/api/analytics');
        if (!response.ok) throw new Error('Failed to fetch analytics');
        
        const analytics = await response.json();
        console.log('Analytics data:', analytics); // Debug log
        
        // Sales Chart
        const salesCtx = document.getElementById('salesChart').getContext('2d');
        const dates = Object.keys(analytics.daily_sales);
        const sales = Object.values(analytics.daily_sales);
        
        salesChart = new Chart(salesCtx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Daily Sales (₹)',
                    data: sales,
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
    } catch (error) {
        console.error('Error initializing charts:', error);
    }
}

// Fetch and display transactions
async function loadTransactions() {
    const response = await fetch('/api/transactions');
    const transactions = await response.json();
    
    const tableBody = document.getElementById('transactionsTable');
    tableBody.innerHTML = transactions.map(t => `
        <tr>
            <td class="px-6 py-4 whitespace-nowrap">${t.id}</td>
            <td class="px-6 py-4 whitespace-nowrap">₹${t.amount.toFixed(2)}</td>
            <td class="px-6 py-4 whitespace-nowrap">${t.points_earned}</td>
            <td class="px-6 py-4 whitespace-nowrap">${t.points_redeemed}</td>
            <td class="px-6 py-4 whitespace-nowrap">${new Date(t.timestamp).toLocaleString()}</td>
        </tr>
    `).join('');
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
    
    document.querySelector('.max-w-7xl').insertBefore(dateRangeSelector, document.querySelector('.grid'));
}

// Update charts and data based on date range
async function updateDateRange(days) {
    const response = await fetch(`/api/analytics?days=${days}`);
    const analytics = await response.json();
    updateCharts(analytics);
    loadTransactions();
}

async function updateCustomDateRange() {
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    
    if (!startDate || !endDate) {
        alert('Please select both start and end dates');
        return;
    }

    const response = await fetch(`/api/analytics?start=${startDate}&end=${endDate}`);
    const analytics = await response.json();
    updateCharts(analytics);
    loadTransactions();
}

// Update chart data
function updateCharts(analytics) {
    salesChart.data.labels = Object.keys(analytics.daily_sales);
    salesChart.data.datasets[0].data = Object.values(analytics.daily_sales);
    salesChart.update();

    pointsChart.data.datasets[0].data = [
        analytics.points_metrics.total_earned,
        analytics.points_metrics.total_redeemed
    ];
    pointsChart.update();

    // Update summary cards
    document.querySelector('#totalSales').textContent = 
        `₹${Object.values(analytics.daily_sales)[Object.values(analytics.daily_sales).length - 1].toFixed(2)}`;
    document.querySelector('#pointsIssued').textContent = analytics.points_metrics.total_earned;
    document.querySelector('#pointsRedeemed').textContent = analytics.points_metrics.total_redeemed;
}

// Setup export buttons
function setupExportButtons() {
    const exportButtons = document.createElement('div');
    exportButtons.className = 'mt-6 flex space-x-4';
    exportButtons.innerHTML = `
        <button onclick="exportTransactions('csv')" class="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">
            Export to CSV
        </button>
        <button onclick="exportTransactions('pdf')" class="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
            Export to PDF
        </button>
    `;
    
    document.querySelector('.max-w-7xl').appendChild(exportButtons);
}

// Export transaction data
async function exportTransactions(format) {
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
}

// Initialize everything when the page loads
document.addEventListener('DOMContentLoaded', () => {
    initializeCharts();
    loadTransactions();
    setupDateRangeSelector();
    setupExportButtons();
    
    // Refresh data every 5 minutes
    setInterval(() => {
        loadTransactions();
        initializeCharts();
    }, 300000);
});