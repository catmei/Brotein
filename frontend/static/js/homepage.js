const backendUrl = `http://${window.location.hostname}:8000`;

// Handle Signup Form Submission
document.getElementById('signup-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const username = document.getElementById('signup-username').value;
    const password = document.getElementById('signup-password').value;

    const response = await fetch(`${backendUrl}/signup`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            password: password,
        }),
    });

    const data = await response.json();
    if (data.error) {
        alert(data.error);
    } else {
        // Store the JWT token in a cookie
        document.cookie = `jwtToken=${data.jwtToken}; path=/; SameSite=Lax`;
        // Redirect to analysis page after successful login
        showSuccessMessage();
    }
});

// Handle Login Form Submission
document.getElementById('login-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    const response = await fetch(`${backendUrl}/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            username: username,
            password: password,
        }),
    });

    const data = await response.json();
    if (data.error) {
        alert(data.error);
    }  else {
        // Store the JWT token in a cookie
        document.cookie = `jwtToken=${data.jwtToken}; path=/; SameSite=Lax`;
        // Redirect to analysis page after successful login
        showSuccessMessage();
    }
});

// Display the success message and redirect to the user info page
function showSuccessMessage() {
    document.getElementById('success-message').style.display = 'block';
    setTimeout(() => {
        // Always redirect to the user info page after login
        window.location.href = '/user_info';
    }, 2000);
}