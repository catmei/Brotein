const backendUrl = `http://${window.location.hostname}:8000`;

// Global variables
let resultData = null;
let pieChartInstance = null;
let summaryChart;

// Utility function to retrieve the JWT token from the cookie
function getJwtToken() {
    const cookies = document.cookie.split('; ');
    for (let cookie of cookies) {
        const [name, value] = cookie.split('=');
        if (name === 'jwtToken') {
            return value;
        }
    }
    return null;
}

// Function to update target intake values in the UI
function updateTargetValues(intake_target) {
    document.getElementById('tdee-value').textContent = intake_target.calories + ' kcal';
    document.getElementById('protein-target').textContent = intake_target.protein + ' g';
    document.getElementById('carbs-target').textContent = intake_target.carbohydrates + ' g';
    document.getElementById('fat-target').textContent = intake_target.fat + ' g';
}

// Function to calculate percentages based on the target
function calculatePercentage(part, total) {
    return total > 0 ? (part / total) : 0;
}

// Function to render the calories pie chart
function renderCaloriesPieChart(intake_current) {
    // Check if the analysis returned valid values or if it's all zeros
    if (intake_current.protein === 0 && intake_current.carbohydrates === 0 && intake_current.fat === 0 && intake_current.calories === 0) {
        // Clear the canvas or replace with a message
        console.log('No food identified');
        const ctx = document.getElementById('caloriesPieChart').getContext('2d');
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height); // Clear the canvas

        // Display the "no food identified" message
        ctx.font = '20px Arial';
        ctx.fillStyle = 'red';
        ctx.textAlign = 'center';
        ctx.fillText('No food identified', ctx.canvas.width / 2, ctx.canvas.height / 2);

        return;  // Exit without rendering the chart
    }

    // Calculate the calories from protein, carbohydrates, and fat
    const caloriesFromProtein = intake_current.protein * 4;
    const caloriesFromCarbohydrates = intake_current.carbohydrates * 4;
    const caloriesFromFat = intake_current.fat * 9;

    // Total calories from protein, carbohydrates, and fat
    const totalCalories = caloriesFromProtein + caloriesFromCarbohydrates + caloriesFromFat;

    // Define the data for the pie chart
    const pieData = {
        labels: ['Protein', 'Carbohydrates', 'Fat'],
        datasets: [{
            data: [caloriesFromProtein, caloriesFromCarbohydrates, caloriesFromFat],
            backgroundColor: ['#76b5c5', '#ffd56b', '#76c893'],
        }]
    };

    // Define the custom plugin to display the total calories in the center of the doughnut
    const totalCaloriesPlugin = {
        id: 'totalCaloriesPlugin',
        beforeDraw: function(chart) {
            const width = chart.width,
                  height = chart.height,
                  ctx = chart.ctx;

            ctx.restore();
            const fontSize = (height / 228).toFixed(2);  // Adjust font size
            ctx.font = fontSize + "em sans-serif";
            ctx.textBaseline = "middle";

            const text = totalCalories + " kcal";
            const textX = Math.round((width - ctx.measureText(text).width) / 2);
            const textY = height / 2;

            ctx.fillText(text, textX, textY);
            ctx.save();
        }
    };

    // Define the options for the pie chart
    const pieOptions = {
        responsive: true,
        plugins: {
            tooltip: {
                callbacks: {
                    // Customize the tooltip to display ingredient values (grams), calories, and percentage of total calories
                    label: function(tooltipItem) {
                        const data = tooltipItem.raw;
                        const index = tooltipItem.dataIndex;
                        const label = tooltipItem.label;
                        let valueText = '';

                        // Get the corresponding grams for each macronutrient
                        const grams = [intake_current.protein, intake_current.carbohydrates, intake_current.fat];

                        // Calculate the percentage of total calories
                        const percentage = (data / totalCalories * 100).toFixed(2);

                        // Construct the tooltip text
                        valueText = `${label}: ${grams[index]}g (${data.toFixed(2)} kcal, ${percentage}%)`;

                        return valueText;
                    }
                }
            },
            // Plugin to display ingredient values directly on the chart
            datalabels: {
                color: '#000',  // Text color for labels
                font: {
                    size: 14
                },
                formatter: function(value, context) {
                    const index = context.dataIndex;
                    const grams = [intake_current.protein, intake_current.carbohydrates, intake_current.fat];
                    const labels = ['Protein', 'Carbohydrates', 'Fat'];
                    return `${labels[index]}: ${grams[index]}g`;  // Display category and value in grams
                },
                anchor: 'center',  // Position the label in the center of the slice
                align: 'center',   // Align the label in the center
            }
        }
    };

    // Check if a pie chart already exists and destroy it to avoid overlapping
    if (pieChartInstance) {
        pieChartInstance.destroy();
    }

    // Render the new pie chart
    const ctx = document.getElementById('caloriesPieChart').getContext('2d');
    pieChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: pieData,
        options: pieOptions,
        plugins: [ChartDataLabels, totalCaloriesPlugin]  // Use the custom plugin for total calories
    });
}

// Function to render the summary chart
function renderSummaryChart(intake_current, intake_prior, intake_target) {
    // Calculate the percentage for each part of the stacked bars
    const prior_percentage = {
        calories: calculatePercentage(intake_prior.calories, intake_target.calories),
        protein: calculatePercentage(intake_prior.protein, intake_target.protein),
        carbohydrates: calculatePercentage(intake_prior.carbohydrates, intake_target.carbohydrates),
        fat: calculatePercentage(intake_prior.fat, intake_target.fat)
    };

    const current_percentage = {
        calories: calculatePercentage(intake_current.calories, intake_target.calories),
        protein: calculatePercentage(intake_current.protein, intake_target.protein),
        carbohydrates: calculatePercentage(intake_current.carbohydrates, intake_target.carbohydrates),
        fat: calculatePercentage(intake_current.fat, intake_target.fat)
    };

    const cumulative_percentage = {
        calories: prior_percentage.calories + current_percentage.calories,
        protein: prior_percentage.protein + current_percentage.protein,
        carbohydrates: prior_percentage.carbohydrates + current_percentage.carbohydrates,
        fat: prior_percentage.fat + current_percentage.fat
    };

    const remaining_percentage = {
        calories: Math.max(1 - cumulative_percentage.calories, 0),
        protein: Math.max(1 - cumulative_percentage.protein, 0),
        carbohydrates: Math.max(1 - cumulative_percentage.carbohydrates, 0),
        fat: Math.max(1 - cumulative_percentage.fat, 0)
    };

    const max_percentage = Math.max(
        cumulative_percentage.calories,
        cumulative_percentage.protein,
        cumulative_percentage.carbohydrates,
        cumulative_percentage.fat,
        1.2
    );

    const newData = {
        labels: ['Calories', 'Protein', 'Carbohydrates', 'Fat'],
        datasets: [
            {
                label: 'Prior',
                backgroundColor: '#76b5c5',
                data: [
                    prior_percentage.calories,
                    prior_percentage.protein,
                    prior_percentage.carbohydrates,
                    prior_percentage.fat
                ],
                absoluteData: [intake_prior.calories, intake_prior.protein, intake_prior.carbohydrates, intake_prior.fat]
            },
            {
                label: 'Current',
                backgroundColor: '#ffd56b',
                data: [
                    current_percentage.calories,
                    current_percentage.protein,
                    current_percentage.carbohydrates,
                    current_percentage.fat
                ],
                absoluteData: [intake_current.calories, intake_current.protein, intake_current.carbohydrates, intake_current.fat]
            },
            {
                label: 'Remaining',
                backgroundColor: '#76c893',
                data: [
                    remaining_percentage.calories,
                    remaining_percentage.protein,
                    remaining_percentage.carbohydrates,
                    remaining_percentage.fat
                ],
                absoluteData: [
                    intake_target.calories - (intake_prior.calories + intake_current.calories),
                    intake_target.protein - (intake_prior.protein + intake_current.protein),
                    intake_target.carbohydrates - (intake_prior.carbohydrates + intake_current.carbohydrates),
                    intake_target.fat - (intake_prior.fat + intake_current.fat)
                ]
            }
        ]
    };

    // Plugin for drawing the vertical red dotted line at 100% and showing the target values
    const dottedLinePlugin = {
        id: 'dottedLinePlugin',
        afterDraw: function(chart) {
            const ctx = chart.ctx;
            const yAxis = chart.scales.y;
            const xAxis = chart.scales.x;

            // Get the pixel position of the 100% mark
            const x100Percent = xAxis.getPixelForValue(1);  // 1 represents 100%

            // Set the style for the dotted red line
            ctx.save();
            ctx.beginPath();
            ctx.setLineDash([5, 5]);  // Dotted line
            ctx.strokeStyle = 'red';  // Red color
            ctx.lineWidth = 2;
            ctx.moveTo(x100Percent, yAxis.top);  // Start at the top of the Y-axis
            ctx.lineTo(x100Percent, yAxis.bottom);  // Draw to the bottom of the Y-axis
            ctx.stroke();
            ctx.restore();

            // Get the bar elements from the first dataset
            const barElements = chart.getDatasetMeta(0).data;

            ctx.font = '12px Arial';
            ctx.fillStyle = 'red';
            ctx.textAlign = 'left';  // Align text to the left so it's placed to the right of the dotted line

            barElements.forEach(function(bar, index) {
                const centerY = bar.getCenterPoint().y;
                let valueText = '';
                switch (index) {
                    case 0:
                        valueText = intake_target.calories + ' kcal';
                        break;
                    case 1:
                        valueText = intake_target.protein + ' g';
                        break;
                    case 2:
                        valueText = intake_target.carbohydrates + ' g';
                        break;
                    case 3:
                        valueText = intake_target.fat + ' g';
                        break;
                }
                // Place the text slightly offset to the right of the dotted line
                ctx.fillText(valueText, x100Percent + 5, centerY);
            });
        }
    };

    const chartOptions = {
        responsive: true,
        indexAxis: 'y',  // Change the chart direction to horizontal
        scales: {
            x: {
                stacked: true,
                min: 0,
                max: Math.ceil(max_percentage * 10) / 10,
                ticks: {
                    callback: function(value) {
                        return (value * 100) + '%';  // Convert to percentage labels
                    }
                }
            },
            y: {
                stacked: true
            }
        },
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(tooltipItem) {
                        const dataset = tooltipItem.dataset;
                        const value = dataset.absoluteData ? dataset.absoluteData[tooltipItem.dataIndex] : null;
                        return value !== null ? dataset.label + ': ' + value : dataset.label;
                    }
                }
            }
        }
    };

    // If the chart already exists, update its data and options
    if (summaryChart) {
        summaryChart.data = newData;
        summaryChart.options.scales.x.max = Math.ceil(max_percentage * 10) / 10;  // Update max value if needed
        summaryChart.update();  // Update the chart
    } else {
        // Create a new chart if it doesn't exist
        const ctx = document.getElementById('summaryChart').getContext('2d');
        summaryChart = new Chart(ctx, {
            type: 'bar',
            data: newData,
            options: chartOptions,
            plugins: [dottedLinePlugin]  // Include the custom plugin for the dotted red line and target values
        });
    }
}

// Event listener for DOMContentLoaded
document.addEventListener('DOMContentLoaded', async function () {
    // Get JWT token from the cookie
    const jwtToken = getJwtToken();

    try {
        // Fetch user info from the backend
        const response = await fetch(`${backendUrl}/get_user_info`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${jwtToken}`,
            },
        });

        const data = await response.json();

        if (data.error) {
            console.error('Error fetching user info:', data.error);
        } else {
            // Populate the target values in the target intake box
            updateTargetValues({
                calories: data.tdee,
                protein: data.target_protein,
                carbohydrates: data.target_carbohydrates,
                fat: data.target_fat
            });
        }
    } catch (error) {
        console.error('Error fetching user info:', error);
    }

});

// Handle '+'
document.getElementById('upload-icon').addEventListener('click', function () {
    // Clear the existing preview image
    const imagePreview = document.getElementById('image-preview');
    imagePreview.src = '';  // Clear the src of the image
    imagePreview.style.display = 'none';  // Hide the preview image

    // Trigger file input click to select a new image
    document.getElementById('food-image').click();
});


// Event listener for image selection
document.getElementById('food-image').addEventListener('change', function () {
    document.getElementById('manual-protein').value = '';
    document.getElementById('manual-carbohydrates').value = '';
    document.getElementById('manual-fat').value = '';

    document.getElementById('analyze-button').style.display = 'block';
    document.getElementById('save-button').style.display = 'none';

    const file = this.files[0];
    const uploadIcon = document.getElementById('upload-icon');
    const imagePreview = document.getElementById('image-preview');

    if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            imagePreview.src = e.target.result;
            imagePreview.style.display = 'block';  // Show the image preview
        };
        reader.readAsDataURL(file);
    }
});


// Handle 'Analyze' button click
document.getElementById('food-upload-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const analyzeButton = document.getElementById('analyze-button'); // Select the analyze button

    // Disable the button and add a loading animation
    analyzeButton.disabled = true;
    analyzeButton.innerHTML = 'Analyzing...';  // Change the button text
    analyzeButton.classList.add('loading');  // Add a class for animation

    const formData = new FormData();
    const imageFile = document.getElementById('food-image').files[0];
    const manualProtein = document.getElementById('manual-protein').value;
    const manualCarbohydrates = document.getElementById('manual-carbohydrates').value;
    const manualFat = document.getElementById('manual-fat').value;

    // Helper function to check if input is a valid integer
    function isValidInteger(value) {
        const parsedValue = Number(value);
        return Number.isInteger(parsedValue) && parsedValue >= 0;  // Ensure it's an integer and non-negative
    }

    // Function to reset the button after validation failure
    function resetAnalyzeButton() {
        analyzeButton.disabled = false;  // Re-enable the button
        analyzeButton.innerHTML = 'Analyze';  // Revert button text
        analyzeButton.classList.remove('loading');  // Remove the loading class
    }

    // Validation: Ensure that either an image is provided or manual inputs are fully filled
    if (!imageFile && !(manualProtein || manualCarbohydrates || manualFat)) {
        // Case 1: Neither an image nor manual inputs are provided
        alert('You must provide at least an image or manual nutrient values.');
        resetAnalyzeButton();
        return;  // Stop further execution
    }

    // Validation: Ensure that if manual inputs are provided, all fields must be filled
    if ((manualProtein || manualCarbohydrates || manualFat) && !(manualProtein && manualCarbohydrates && manualFat)) {
        // Case 2: Partial manual inputs are provided, but not all three fields
        alert('Please fill in all manual nutrient values: protein, carbohydrates, and fat.');
        resetAnalyzeButton();
        return;  // Stop further execution
    }

    if (!isValidInteger(manualProtein) || !isValidInteger(manualCarbohydrates) || !isValidInteger(manualFat)) {
        alert('Please provide valid integer values for protein, carbohydrates, and fat.');
        resetAnalyzeButton();
        return;
    }

    // If an image is provided, append it to the formData
    if (imageFile) {
        formData.append('food_img', imageFile);
    }

    // If manual input values are provided, append them to the formData
    if (manualProtein && manualCarbohydrates && manualFat) {
        formData.append('manual_protein', manualProtein);
        formData.append('manual_carbohydrates', manualCarbohydrates);
        formData.append('manual_fat', manualFat);
    }

    // Get the client's time zone
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    formData.append('time_zone', timeZone);  // Append time zone to the form data

    // Get the JWT token from the cookie
    const jwtToken = getJwtToken();

    try {
        // Send the formData to the backend for analysis
        const response = await fetch(`${backendUrl}/analyze`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${jwtToken}`,  // Include the JWT in the Authorization header
            },
            body: formData
        });

        const data = await response.json();
        resultData = data.result; // Store the result data temporarily

        // Only show the canvas if analysis is successful
        document.getElementById('caloriesPieChart').style.display = 'block';
        document.getElementById('summaryChart').style.display = 'block';

        updateTargetValues(resultData.intake_target);
        renderCaloriesPieChart(resultData.intake_current);
        renderSummaryChart(resultData.intake_current, resultData.intake_prior, resultData.intake_target);
        document.getElementById('save-button').style.display = 'block';

    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while analyzing the image.');

        // Hide the canvas elements in case of an error
        document.getElementById('caloriesPieChart').style.display = 'none';
        document.getElementById('summaryChart').style.display = 'none';
    } finally {
        // Restore the button state
        analyzeButton.disabled = false;
        analyzeButton.innerHTML = 'Analyze';  // Revert button text
        analyzeButton.classList.remove('loading');  // Remove the loading class
    }
});


// Handle 'Save' button click
document.getElementById('save-button').addEventListener('click', async function () {
    const saveButton = document.getElementById('save-button'); // Select the save button

    // Disable the button and add a loading animation
    saveButton.disabled = true;
    saveButton.innerHTML = 'Saving...';  // Change the button text
    saveButton.classList.add('loading');  // Add a class for animation

    if (!resultData) {
        alert('No data available to save.');
        saveButton.disabled = false;
        saveButton.innerHTML = 'Save';  // Restore the button text
        saveButton.classList.remove('loading');  // Remove the loading animation
        return;
    }

    const formData = new FormData();

    // Check if image upload was used
    const imageFile = document.getElementById('food-image').files[0];
    if (imageFile) {
        formData.append('food_img', imageFile);
    }

    formData.append('calories', resultData.intake_current.calories);
    formData.append('protein', resultData.intake_current.protein);
    formData.append('carbohydrates', resultData.intake_current.carbohydrates);
    formData.append('fat', resultData.intake_current.fat);

    const jwtToken = getJwtToken();

    try {
        // Send the result data to the backend to save it in the diet history
        const response = await fetch(`${backendUrl}/save_diet_history`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${jwtToken}`,
            },
            body: formData
        });

        const saveResponse = await response.json();

        alert('Diet history saved successfully!');
        renderSummaryChart(resultData.intake_current, resultData.intake_prior, resultData.intake_target);
        document.getElementById('save-button').style.display = 'none';  // Hide the save button after saving
    } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while saving the diet history.');
    } finally {
        // Restore the button state
        saveButton.disabled = false;
        saveButton.innerHTML = 'Save';  // Revert button text
        saveButton.classList.remove('loading');  // Remove the loading class
    }
});
