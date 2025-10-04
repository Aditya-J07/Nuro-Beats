/**
 * Chart utilities for NeuroBeat progress visualization
 * Handles creation and management of progress charts using Chart.js
 */

class ProgressChartManager {
    constructor() {
        this.charts = {};
        this.defaultOptions = {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            scales: {
                x: {
                    display: true,
                    grid: {
                        display: true,
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#6c757d'
                    }
                },
                y: {
                    display: true,
                    grid: {
                        display: true,
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#6c757d'
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#dee2e6',
                        usePointStyle: true,
                        padding: 20
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#007bff',
                    borderWidth: 1
                }
            }
        };
    }

    // Create a progress overview chart with multiple metrics
    createProgressChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) {
            console.error(`Canvas element with ID '${canvasId}' not found`);
            return null;
        }

        const chart = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: data.dates || [],
                datasets: [
                    {
                        label: 'Accuracy Score (%)',
                        data: data.accuracy_scores || [],
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        fill: false,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        yAxisID: 'y'
                    },
                    {
                        label: 'BPM',
                        data: data.bpm_values || [],
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        fill: false,
                        tension: 0.4,
                        pointRadius: 4,
                        pointHoverRadius: 6,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    ...this.defaultOptions.scales,
                    y: {
                        ...this.defaultOptions.scales.y,
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Accuracy (%)',
                            color: '#28a745'
                        },
                        min: 0,
                        max: 100
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'BPM',
                            color: '#007bff'
                        },
                        grid: {
                            drawOnChartArea: false,
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#6c757d'
                        }
                    }
                }
            }
        });

        // Add baseline and target lines if available
        if (data.baseline_cadence) {
            chart.data.datasets.push({
                label: 'Baseline BPM',
                data: new Array(data.dates.length).fill(data.baseline_cadence),
                borderColor: '#6c757d',
                borderDash: [5, 5],
                pointRadius: 0,
                fill: false,
                yAxisID: 'y1'
            });
        }

        if (data.target_cadence) {
            chart.data.datasets.push({
                label: 'Target BPM',
                data: new Array(data.dates.length).fill(data.target_cadence),
                borderColor: '#dc3545',
                borderDash: [5, 5],
                pointRadius: 0,
                fill: false,
                yAxisID: 'y1'
            });
        }

        chart.update();
        this.charts[canvasId] = chart;
        return chart;
    }

    // Create a real-time session chart
    createSessionChart(canvasId, maxDataPoints = 50) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) {
            console.error(`Canvas element with ID '${canvasId}' not found`);
            return null;
        }

        const chart = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Current BPM',
                        data: [],
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 2
                    }
                ]
            },
            options: {
                ...this.defaultOptions,
                animation: {
                    duration: 0
                },
                scales: {
                    ...this.defaultOptions.scales,
                    x: {
                        ...this.defaultOptions.scales.x,
                        title: {
                            display: true,
                            text: 'Time',
                            color: '#6c757d'
                        }
                    },
                    y: {
                        ...this.defaultOptions.scales.y,
                        title: {
                            display: true,
                            text: 'BPM',
                            color: '#6c757d'
                        },
                        min: 40,
                        max: 120
                    }
                }
            }
        });

        chart.maxDataPoints = maxDataPoints;
        this.charts[canvasId] = chart;
        return chart;
    }

    // Update real-time session chart
    updateSessionChart(canvasId, timestamp, bpmValue) {
        const chart = this.charts[canvasId];
        if (!chart) {
            console.error(`Chart '${canvasId}' not found`);
            return;
        }

        chart.data.labels.push(timestamp);
        chart.data.datasets[0].data.push(bpmValue);

        // Keep only the last maxDataPoints
        if (chart.data.labels.length > chart.maxDataPoints) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }

        chart.update('none'); // No animation for real-time updates
    }

    // Create accuracy distribution chart (pie chart)
    createAccuracyDistributionChart(canvasId, sessions) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) {
            console.error(`Canvas element with ID '${canvasId}' not found`);
            return null;
        }

        // Categorize sessions by accuracy
        const categories = {
            excellent: sessions.filter(s => s.accuracy_score >= 90).length,
            good: sessions.filter(s => s.accuracy_score >= 75 && s.accuracy_score < 90).length,
            fair: sessions.filter(s => s.accuracy_score >= 60 && s.accuracy_score < 75).length,
            poor: sessions.filter(s => s.accuracy_score < 60).length
        };

        const chart = new Chart(ctx.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: ['Excellent (90%+)', 'Good (75-89%)', 'Fair (60-74%)', 'Poor (<60%)'],
                datasets: [{
                    data: [categories.excellent, categories.good, categories.fair, categories.poor],
                    backgroundColor: [
                        '#28a745',
                        '#17a2b8',
                        '#ffc107',
                        '#dc3545'
                    ],
                    borderWidth: 2,
                    borderColor: '#343a40'
                }]
            },
            options: {
                ...this.defaultOptions,
                cutout: '60%',
                plugins: {
                    ...this.defaultOptions.plugins,
                    legend: {
                        ...this.defaultOptions.plugins.legend,
                        position: 'bottom'
                    }
                }
            }
        });

        this.charts[canvasId] = chart;
        return chart;
    }

    // Create weekly progress summary chart
    createWeeklyProgressChart(canvasId, weeklyData) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) {
            console.error(`Canvas element with ID '${canvasId}' not found`);
            return null;
        }

        const chart = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: weeklyData.weeks || [],
                datasets: [
                    {
                        label: 'Sessions Completed',
                        data: weeklyData.sessionCounts || [],
                        backgroundColor: 'rgba(0, 123, 255, 0.6)',
                        borderColor: '#007bff',
                        borderWidth: 1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Average Accuracy',
                        data: weeklyData.avgAccuracy || [],
                        type: 'line',
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        fill: false,
                        tension: 0.4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                ...this.defaultOptions,
                scales: {
                    ...this.defaultOptions.scales,
                    y: {
                        ...this.defaultOptions.scales.y,
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Sessions',
                            color: '#007bff'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Accuracy (%)',
                            color: '#28a745'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                        min: 0,
                        max: 100
                    }
                }
            }
        });

        this.charts[canvasId] = chart;
        return chart;
    }

    // Destroy a specific chart
    destroyChart(canvasId) {
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
            delete this.charts[canvasId];
        }
    }

    // Destroy all charts
    destroyAllCharts() {
        Object.keys(this.charts).forEach(canvasId => {
            this.charts[canvasId].destroy();
        });
        this.charts = {};
    }

    // Update chart theme (for theme switching)
    updateChartTheme(isDarkMode = true) {
        const textColor = isDarkMode ? '#dee2e6' : '#495057';
        const gridColor = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';

        Object.values(this.charts).forEach(chart => {
            chart.options.scales.x.ticks.color = textColor;
            chart.options.scales.y.ticks.color = textColor;
            chart.options.scales.x.grid.color = gridColor;
            chart.options.scales.y.grid.color = gridColor;
            
            if (chart.options.scales.y1) {
                chart.options.scales.y1.ticks.color = textColor;
                chart.options.scales.y1.grid.color = gridColor;
            }
            
            chart.options.plugins.legend.labels.color = textColor;
            chart.update();
        });
    }

    // Export chart data as JSON
    exportChartData(canvasId) {
        const chart = this.charts[canvasId];
        if (chart) {
            return {
                labels: chart.data.labels,
                datasets: chart.data.datasets.map(dataset => ({
                    label: dataset.label,
                    data: dataset.data
                }))
            };
        }
        return null;
    }
}

// Global chart manager instance
const chartManager = new ProgressChartManager();

// Utility functions for chart creation
function createProgressChart(canvasId, data) {
    return chartManager.createProgressChart(canvasId, data);
}

function createSessionChart(canvasId, maxDataPoints = 50) {
    return chartManager.createSessionChart(canvasId, maxDataPoints);
}

function updateSessionChart(canvasId, timestamp, bpmValue) {
    chartManager.updateSessionChart(canvasId, timestamp, bpmValue);
}

function createAccuracyDistributionChart(canvasId, sessions) {
    return chartManager.createAccuracyDistributionChart(canvasId, sessions);
}

function createWeeklyProgressChart(canvasId, weeklyData) {
    return chartManager.createWeeklyProgressChart(canvasId, weeklyData);
}

// Clean up charts when leaving page
window.addEventListener('beforeunload', () => {
    chartManager.destroyAllCharts();
});
