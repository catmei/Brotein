from flask import Flask, render_template

app = Flask(__name__)


# Define the route for the home page
@app.route('/')
def index():
    return render_template('homepage.html')


# User info page
@app.route('/user_info')
def user_info():
    return render_template('user_info.html')


@app.route('/history')
def history():
    return render_template('history.html')


# Analysis page for food image analysis
@app.route('/analysis')
def analysis():
    return render_template('analysis.html')


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
