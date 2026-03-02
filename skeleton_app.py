from flask import Flask, render_template, jsonify
import time
import requests
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Sample form data to simulate database response
SAMPLE_FORM_DATA = {
    "title": "Customer Feedback Form",
    "fields": [
        {"type": "text", "label": "Name", "placeholder": "Enter your full name"},
        {"type": "email", "label": "Email", "placeholder": "Enter your email address"},
        {"type": "select", "label": "Rating", "options": ["Excellent", "Good", "Fair", "Poor"]},
        {"type": "textarea", "label": "Comments", "placeholder": "Share your feedback"}
    ]
}

@app.route('/')
def home():
    """Serve the main page with skeleton loading"""
    return render_template('skeleton_form.html')

@app.route('/getForm')
def get_form():
    """API endpoint that returns form data after a delay to simulate loading"""
    # Simulate network/database delay
    time.sleep(2)
    return jsonify(SAMPLE_FORM_DATA)

if __name__ == '__main__':
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)