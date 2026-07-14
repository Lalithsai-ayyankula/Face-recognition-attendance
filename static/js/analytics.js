// Debug: Log data to the console
console.log("Chart Data:", chartData);

// Check if data is available
if (chartData.dates && chartData.presentCount && chartData.absentCount && chartData.attendancePercentage) {
    // Daily Attendance Chart
    const dailyAttendanceCtx = document.getElementById('dailyAttendanceChart').getContext('2d');
    new Chart(dailyAttendanceCtx, {
        type: 'bar',
        data: {
            labels: chartData.dates,
            datasets: [
                {
                    label: 'Present',
                    data: chartData.presentCount,
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Absent',
                    data: chartData.absentCount,
                    backgroundColor: 'rgba(255, 99, 132, 0.6)',
                    borderColor: 'rgba(255, 99, 132, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of Students'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    });

    // Attendance Percentage Chart 
    const attendancePercentageCtx = document.getElementById('attendancePercentageChart').getContext('2d');
    new Chart(attendancePercentageCtx, {
        type: 'line',
        data: {
            labels: chartData.dates,
            datasets: [
                {
                    label: 'Attendance Percentage',
                    data: chartData.attendancePercentage,
                    borderColor: 'rgba(153, 102, 255, 1)',
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBackgroundColor: 'rgba(153, 102, 255, 1)'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Attendance: ${context.parsed.y.toFixed(1)}%`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Percentage (%)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Date'
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    });

    // Weekly Comparison Chart (if data is available)
    if (chartData.weeklyData && document.getElementById('weeklyComparisonChart')) {
        const weeklyComparisonCtx = document.getElementById('weeklyComparisonChart').getContext('2d');
        new Chart(weeklyComparisonCtx, {
            type: 'bar',
            data: {
                labels: chartData.weeklyData.weeks,
                datasets: [
                    {
                        label: 'Average Weekly Attendance (%)',
                        data: chartData.weeklyData.percentages,
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Average Attendance (%)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Week'
                        }
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }
} else {
    console.error("No data available to render charts.");
    
    // Display message on the page
    const chartContainers = document.querySelectorAll('.card-body');
    chartContainers.forEach(container => {
        if (container.querySelector('canvas')) {
            const noDataMessage = document.createElement('div');
            noDataMessage.className = 'alert alert-warning';
            noDataMessage.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>No attendance data available for the selected date range.';
            container.appendChild(noDataMessage);
        }
    });
}

// Date preset buttons functionality
document.querySelectorAll('.date-preset').forEach(button => {
    button.addEventListener('click', function() {
        const today = new Date();
        let startDate = new Date();
        let endDate = new Date();
        
        if (this.dataset.days) {
            // Last X days
            const days = parseInt(this.dataset.days);
            startDate.setDate(today.getDate() - days);
        } else if (this.dataset.type === 'month') {
            // This month
            startDate = new Date(today.getFullYear(), today.getMonth(), 1);
        } else if (this.dataset.type === 'year') {
            // This year
            startDate = new Date(today.getFullYear(), 0, 1);
        }
        
        // Format dates for input fields
        document.getElementById('start_date').value = formatDate(startDate);
        document.getElementById('end_date').value = formatDate(endDate);
        
        // Submit the form
        document.getElementById('dateFilterForm').submit();
    });
});

// Format date as YYYY-MM-DD
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Dark Mode Toggle
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDarkMode = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDarkMode);
    
    // Update button icon
    const darkModeBtn = document.getElementById('darkModeToggle');
    if (darkModeBtn) {
        if (isDarkMode) {
            darkModeBtn.innerHTML = '<i class="fas fa-sun"></i> Light Mode';
        } else {
            darkModeBtn.innerHTML = '<i class="fas fa-moon"></i> Dark Mode';
        }
    }
    
    // Update chart colors if they exist
    updateChartColors(isDarkMode);
}

function updateChartColors(isDarkMode) {
    // Update text color for all charts
    Chart.defaults.color = isDarkMode ? '#f8f9fa' : '#666';
    
    // Force charts to update
    Chart.instances.forEach(chart => {
        chart.update();
    });
}

// Check for saved dark mode preference
document.addEventListener('DOMContentLoaded', function() {
    if (localStorage.getItem('darkMode') === 'true') {
        document.body.classList.add('dark-mode');
        const darkModeBtn = document.getElementById('darkModeToggle');
        if (darkModeBtn) {
            darkModeBtn.innerHTML = '<i class="fas fa-sun"></i> Light Mode';
        }
        updateChartColors(true);
    }
});