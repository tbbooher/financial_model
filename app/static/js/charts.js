/**
 * Family Office Platform - Chart.js Configurations
 * Financial charts for portfolio visualization
 */

// Chart.js Default Configuration
Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.padding = 12;

// Color Palette
const chartColors = {
    primary: '#0d6efd',
    success: '#198754',
    warning: '#ffc107',
    danger: '#dc3545',
    info: '#0dcaf0',
    secondary: '#6c757d',
    light: '#f8f9fa',
    dark: '#212529'
};

const allocationColors = [
    '#0d6efd', // Blue - Stocks
    '#198754', // Green - Bonds
    '#ffc107', // Yellow - Real Estate
    '#dc3545', // Red - Cash
    '#0dcaf0', // Cyan - Alternatives
    '#6f42c1', // Purple - Crypto
    '#fd7e14', // Orange - Commodities
    '#20c997'  // Teal - Other
];

// Chart Instances
let allocationChart = null;
let performanceChart = null;
let riskChart = null;
let smlChart = null;
let monteCarloChart = null;
let riskDistributionChart = null;

// Allocation Pie Chart
function initAllocationChart(data) {
    const ctx = document.getElementById('allocationChart');
    if (!ctx) return;

    if (allocationChart) {
        allocationChart.destroy();
    }

    const labels = Object.keys(data);
    const values = Object.values(data);
    const total = values.reduce((a, b) => a + b, 0);

    allocationChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.map(l => l.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())),
            datasets: [{
                data: values,
                backgroundColor: allocationColors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${context.label}: ${formatCurrency(value)} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });
}

// Performance Line Chart
function initPerformanceChart(labels = [], portfolioData = [], benchmarkData = []) {
    const ctx = document.getElementById('performanceChart');
    if (!ctx) return;

    if (performanceChart) {
        performanceChart.destroy();
    }

    // Generate sample data if not provided
    if (labels.length === 0) {
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        labels = months;
        portfolioData = [100, 102, 105, 103, 108, 112, 110, 115, 118, 120, 122, 125];
        benchmarkData = [100, 101, 103, 102, 105, 107, 106, 109, 111, 113, 115, 117];
    }

    performanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Portfolio',
                    data: portfolioData,
                    borderColor: chartColors.primary,
                    backgroundColor: 'rgba(13, 110, 253, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6
                },
                {
                    label: 'S&P 500',
                    data: benchmarkData,
                    borderColor: chartColors.secondary,
                    backgroundColor: 'transparent',
                    borderDash: [5, 5],
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.raw.toFixed(2)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

function updatePerformanceChart(period) {
    // Update active button
    const buttons = document.querySelectorAll('.btn-group .btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    // Fetch new data for period
    FamilyOffice.apiRequest(`/portfolio/performance?period=${period}`)
        .then(data => {
            if (data && data.data && data.data.history) {
                initPerformanceChart(
                    data.data.history.dates,
                    data.data.history.portfolio_values,
                    data.data.history.benchmark_values
                );
            }
        })
        .catch(err => console.error('Error updating performance chart:', err));
}

// Security Market Line Chart
function initSMLChart(smlData, assetData = []) {
    const ctx = document.getElementById('smlChart');
    if (!ctx) return;

    if (smlChart) {
        smlChart.destroy();
    }

    const smlPoints = smlData.betas.map((beta, i) => ({
        x: beta,
        y: smlData.expected_returns[i] * 100
    }));

    const assetPoints = assetData.map(asset => ({
        x: asset.beta,
        y: asset.actual_return * 100,
        label: asset.symbol
    }));

    smlChart = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'Security Market Line',
                    data: smlPoints,
                    type: 'line',
                    borderColor: chartColors.primary,
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    pointRadius: 0,
                    order: 2
                },
                {
                    label: 'Portfolio Assets',
                    data: assetPoints,
                    backgroundColor: assetPoints.map(p =>
                        p.y > smlData.expected_returns[Math.floor(p.x * 50)] * 100
                            ? chartColors.success
                            : chartColors.danger
                    ),
                    pointRadius: 8,
                    pointHoverRadius: 12,
                    order: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            if (context.dataset.label === 'Portfolio Assets') {
                                const point = context.raw;
                                return `${point.label}: Beta=${point.x.toFixed(2)}, Return=${point.y.toFixed(2)}%`;
                            }
                            return `Expected Return: ${context.raw.y.toFixed(2)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Beta'
                    },
                    min: 0,
                    max: 2
                },
                y: {
                    title: {
                        display: true,
                        text: 'Expected Return (%)'
                    }
                }
            }
        }
    });
}

// Monte Carlo Simulation Chart
function initMonteCarloChart(simulationData) {
    const ctx = document.getElementById('monteCarloChart');
    if (!ctx) return;

    if (monteCarloChart) {
        monteCarloChart.destroy();
    }

    const percentiles = simulationData.percentiles || {};
    const labels = Array.from({length: 12}, (_, i) => `Month ${i + 1}`);

    monteCarloChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '95th Percentile',
                    data: percentiles['95'] || [],
                    borderColor: chartColors.success,
                    backgroundColor: 'rgba(25, 135, 84, 0.1)',
                    fill: '+1',
                    tension: 0.4,
                    pointRadius: 0
                },
                {
                    label: '75th Percentile',
                    data: percentiles['75'] || [],
                    borderColor: chartColors.info,
                    backgroundColor: 'rgba(13, 202, 240, 0.1)',
                    fill: '+1',
                    tension: 0.4,
                    pointRadius: 0
                },
                {
                    label: 'Median',
                    data: percentiles['50'] || [],
                    borderColor: chartColors.primary,
                    backgroundColor: 'transparent',
                    borderWidth: 3,
                    tension: 0.4,
                    pointRadius: 0
                },
                {
                    label: '25th Percentile',
                    data: percentiles['25'] || [],
                    borderColor: chartColors.warning,
                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                    fill: '+1',
                    tension: 0.4,
                    pointRadius: 0
                },
                {
                    label: '5th Percentile',
                    data: percentiles['5'] || [],
                    borderColor: chartColors.danger,
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    fill: false,
                    tension: 0.4,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${formatCurrency(context.raw)}`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    title: {
                        display: true,
                        text: 'Portfolio Value'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            }
        }
    });
}

// Risk Distribution Chart
function initRiskDistributionChart(data) {
    const ctx = document.getElementById('riskDistributionChart');
    if (!ctx) return;

    if (riskDistributionChart) {
        riskDistributionChart.destroy();
    }

    // Generate histogram data from returns
    const returns = data.returns || [];
    const bins = 30;
    const min = Math.min(...returns);
    const max = Math.max(...returns);
    const binWidth = (max - min) / bins;

    const histogram = new Array(bins).fill(0);
    returns.forEach(r => {
        const binIndex = Math.min(Math.floor((r - min) / binWidth), bins - 1);
        histogram[binIndex]++;
    });

    const labels = histogram.map((_, i) =>
        ((min + i * binWidth) * 100).toFixed(1) + '%'
    );

    riskDistributionChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Frequency',
                data: histogram,
                backgroundColor: histogram.map((_, i) => {
                    const value = min + i * binWidth;
                    return value < 0 ? chartColors.danger : chartColors.success;
                }),
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Daily Return'
                    },
                    ticks: {
                        maxTicksLimit: 10
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Frequency'
                    }
                }
            }
        }
    });
}

// Asset Pricing Table Renderer
function renderAssetPricingTable(assets) {
    const table = document.getElementById('assetPricingTable');
    if (!table) return;

    if (!assets || assets.length === 0) {
        table.innerHTML = '<tr><td colspan="8" class="text-center text-muted py-4">No asset data available</td></tr>';
        return;
    }

    table.innerHTML = assets.map(asset => `
        <tr>
            <td><strong>${asset.symbol}</strong></td>
            <td>${asset.name || '-'}</td>
            <td class="text-end">${asset.beta?.toFixed(2) || '-'}</td>
            <td class="text-end">${formatPercent(asset.expected_return)}</td>
            <td class="text-end ${asset.actual_return >= 0 ? 'text-success' : 'text-danger'}">
                ${formatPercent(asset.actual_return)}
            </td>
            <td class="text-end ${asset.alpha >= 0 ? 'text-success' : 'text-danger'}">
                ${formatPercent(asset.alpha)}
            </td>
            <td>
                <span class="badge ${getValuationBadgeClass(asset.valuation)}">
                    ${asset.valuation?.replace('_', ' ') || '-'}
                </span>
            </td>
            <td>
                <span class="badge ${getRecommendationBadgeClass(asset.recommendation)}">
                    ${asset.recommendation?.replace('_', ' ') || '-'}
                </span>
            </td>
        </tr>
    `).join('');
}

function getValuationBadgeClass(valuation) {
    const classes = {
        'undervalued': 'bg-success',
        'fairly_valued': 'bg-secondary',
        'overvalued': 'bg-danger'
    };
    return classes[valuation] || 'bg-secondary';
}

function getRecommendationBadgeClass(recommendation) {
    const classes = {
        'strong_buy': 'bg-success',
        'buy': 'bg-success bg-opacity-75',
        'hold': 'bg-secondary',
        'sell': 'bg-danger bg-opacity-75',
        'strong_sell': 'bg-danger'
    };
    return classes[recommendation] || 'bg-secondary';
}

// Stress Test Results Renderer
function renderStressTestResults(scenarios) {
    const table = document.getElementById('stressTestTable');
    if (!table) return;

    if (!scenarios || scenarios.length === 0) {
        table.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-4">No stress test results</td></tr>';
        return;
    }

    table.innerHTML = scenarios.map(scenario => `
        <tr>
            <td><strong>${scenario.name}</strong></td>
            <td>${scenario.description}</td>
            <td class="text-end text-danger">${formatPercent(scenario.market_shock)}</td>
            <td class="text-end text-danger">${formatPercent(scenario.portfolio_impact)}</td>
            <td class="text-end text-danger">${formatCurrency(scenario.estimated_loss)}</td>
        </tr>
    `).join('');
}

// Monte Carlo Results Renderer
function renderMonteCarloResults(data) {
    const container = document.getElementById('mcResults');
    if (!container) return;

    container.innerHTML = `
        <div class="mb-3 pb-3 border-bottom">
            <div class="d-flex justify-content-between">
                <span>Mean Return</span>
                <span class="fw-bold ${data.statistics?.mean >= 0 ? 'text-success' : 'text-danger'}">
                    ${formatPercent(data.statistics?.mean)}
                </span>
            </div>
        </div>
        <div class="mb-3 pb-3 border-bottom">
            <div class="d-flex justify-content-between">
                <span>Std Deviation</span>
                <span class="fw-bold">${formatPercent(data.statistics?.std)}</span>
            </div>
        </div>
        <div class="mb-3 pb-3 border-bottom">
            <div class="d-flex justify-content-between">
                <span>5th Percentile</span>
                <span class="fw-bold text-danger">${formatCurrency(data.percentiles?.['5'])}</span>
            </div>
        </div>
        <div class="mb-3 pb-3 border-bottom">
            <div class="d-flex justify-content-between">
                <span>Median</span>
                <span class="fw-bold">${formatCurrency(data.percentiles?.['50'])}</span>
            </div>
        </div>
        <div>
            <div class="d-flex justify-content-between">
                <span>95th Percentile</span>
                <span class="fw-bold text-success">${formatCurrency(data.percentiles?.['95'])}</span>
            </div>
        </div>
    `;

    // Update chart
    if (data.percentiles) {
        initMonteCarloChart(data);
    }
}

// Export functions
window.initAllocationChart = initAllocationChart;
window.initPerformanceChart = initPerformanceChart;
window.updatePerformanceChart = updatePerformanceChart;
window.initSMLChart = initSMLChart;
window.initMonteCarloChart = initMonteCarloChart;
window.initRiskDistributionChart = initRiskDistributionChart;
window.renderAssetPricingTable = renderAssetPricingTable;
window.renderStressTestResults = renderStressTestResults;
window.renderMonteCarloResults = renderMonteCarloResults;
