const backendUrl = `http://${window.location.hostname}:8000`;

document.addEventListener('DOMContentLoaded', function () {
    // Fetch diet history when the page loads
    fetchDietHistory();
});

async function fetchDietHistory() {
    const jwtToken = getJwtToken();

    // Send GET request to fetch diet history
    const response = await fetch(`${backendUrl}/get_diet_history`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${jwtToken}`,
        }
    });

    const data = await response.json();

    if (data.error) {
        console.error('Error fetching diet history:', data.error);
    } else {
        renderDietHistory(data.diet_history);
    }
}

function renderDietHistory(history) {
    const historyAccordion = document.getElementById('historyAccordion');
    let groupedByDate = {};

    // Group the diet history by date
    history.forEach(entry => {
        const utcDate = new Date(entry.datetime);

        // Adjust the UTC date to the client's local time
        const localDateTime = new Date(utcDate.getTime() - utcDate.getTimezoneOffset() * 60000);

        // Format the local date
        const localDate = localDateTime.toLocaleDateString(); // Format to local date

        if (!groupedByDate[localDate]) {
            groupedByDate[localDate] = [];
        }
        groupedByDate[localDate].push({
            ...entry,
            localDateTime: localDateTime.toLocaleString(undefined, {
                year: 'numeric',
                month: 'numeric',
                day: 'numeric',
                hour: 'numeric',
                minute: 'numeric',
                second: 'numeric'
            })
        });
    });

    // Build the accordion content
    let accordionHTML = '';
    Object.keys(groupedByDate).forEach((date, index) => {
        accordionHTML += `
        <div class="accordion-item">
            <h2 class="accordion-header" id="heading${index}">
                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse${index}" aria-expanded="false" aria-controls="collapse${index}">
                    ${date}
                </button>
            </h2>
            <div id="collapse${index}" class="accordion-collapse collapse" aria-labelledby="heading${index}" data-bs-parent="#historyAccordion">
                <div class="accordion-body">
                    ${groupedByDate[date].map(meal => `
                        <div class="meal-record">
                            <div class="meal-text">
                                <strong>Time:</strong> ${meal.localDateTime}<br>
                                <strong>Calories:</strong> ${meal.calories} kcal<br>
                                <strong>Protein:</strong> ${meal.protein}g<br>
                                <strong>Carbohydrates:</strong> ${meal.carbohydrates}g<br>
                                <strong>Fat:</strong> ${meal.fat}g<br>
                            </div>
                            ${meal.img_url ? `
                                <div class="meal-image">
                                    <img src="${meal.img_url}" alt="Meal Image">
                                </div>
                            ` : ''}
                        </div>
                        <hr>
                    `).join('')}
                </div>
            </div>
        </div>
        `;
    });

    // Set the generated HTML to the accordion
    historyAccordion.innerHTML = accordionHTML;
}


// Function to retrieve JWT token from cookies
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
