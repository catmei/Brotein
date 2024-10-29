const backendUrl = `http://${window.location.hostname}:8000`;

// Function to retrieve the JWT token from the cookie
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

// Fetch user info if it exists and pre-fill the form
async function fetchUserInfo() {
    const jwtToken = getJwtToken();

    const response = await fetch(`${backendUrl}/get_user_info`, {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${jwtToken}`,
        }
    });

    const data = await response.json();

    if (!data.error) {
        document.getElementById('height').value = data.height;
        document.getElementById('weight').value = data.weight;
        document.getElementById('age').value = data.age;
        document.getElementById('target').value = data.target;
        document.getElementById('preference').value = data.preference;
        document.getElementById('gender').value = data.gender;
        document.getElementById('activity_level').value = data.activity_level;
    }
}

// Handle User Info Form Submission
document.getElementById('user-info-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const height = document.getElementById('height').value;
    const weight = document.getElementById('weight').value;
    const age = document.getElementById('age').value;
    const target = document.getElementById('target').value;
    const preference = document.getElementById('preference').value;
    const gender = document.getElementById('gender').value;  // New field
    const activity_level = document.getElementById('activity_level').value;

    const jwtToken = getJwtToken();

    const response = await fetch(`${backendUrl}/save_user_info`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${jwtToken}`
        },
        body: JSON.stringify({
            height: height,
            weight: weight,
            age: age,
            target: target,
            preference: preference,
            gender: gender,
            activity_level: activity_level
        })
    });

    const data = await response.json();
    if (!data.error) {
        window.location.href = '/analysis';  // Redirect to analysis page
    } else {
        alert(data.error);
    }
});


// Validate form fields and enable/disable "Next" button
function validateForm() {
    const height = document.getElementById('height').value;
    const weight = document.getElementById('weight').value;
    const age = document.getElementById('age').value;
    const target = document.getElementById('target').value;
    const preference = document.getElementById('preference').value;
    const gender = document.getElementById('gender').value;
    const activity_level = document.getElementById('activity_level').value;

    const saveButton = document.getElementById('save-btn');

    // Check if all fields are filled
    if (height && weight && age) {
        saveButton.disabled = false;
    } else {
        saveButton.disabled = true;
    }
}

// Add event listeners to form fields to trigger validation
document.querySelectorAll('#user-info-form input').forEach(input => {
    input.addEventListener('input', validateForm);  // Validate form on input change
});

// Fetch existing user info on page load
fetchUserInfo();
