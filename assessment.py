# assessment.py

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from flask_login import login_required # Keep this import if used elsewhere, but not for submit_test
from datetime import datetime
import os
import json

# Create the Blueprint
assessment_bp = Blueprint('assessment', __name__, url_prefix='/assessment')

# --- Google Sheets Setup ---
# The path to the JSON key file is made robust here
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
json_keyfile_path = os.path.join(os.path.dirname(__file__), 'numerify-468407-2c84f80eaebd.json')
CREDS = ServiceAccountCredentials.from_json_keyfile_name(json_keyfile_path, SCOPE)
CLIENT = gspread.authorize(CREDS)
SHEET = CLIENT.open('numerify quiz').sheet1

# --- Define the headers for your Google Sheet ---
SHEET_HEADERS = [
    "Timestamp", "Name", "Class", "School", "Register Number", 
    "Questions Attempted", "Score", "Score Percentage"
]

def ensure_headers_exist():
    """Ensures that the Google Sheet has proper headers in the first row"""
    try:
        # Get all values in the sheet
        all_values = SHEET.get_all_values()
        
        # If sheet is empty or first row doesn't match our headers
        if not all_values or all_values[0] != SHEET_HEADERS:
            print("Setting up headers in Google Sheet...")
            
            # Clear the sheet and add headers
            SHEET.clear()
            SHEET.append_row(SHEET_HEADERS)
            
            # Make headers bold and freeze the first row
            SHEET.format('1:1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })
            
            print("Headers successfully added to Google Sheet.")
            return True
        else:
            print("Headers already exist in Google Sheet.")
            return False
            
    except Exception as e:
        print(f"Error ensuring headers exist: {e}")
        return False

# --- This route is correct and does not need changes ---
@assessment_bp.route('/take', methods=['GET', 'POST'])
def take_assessment():
    if request.method == 'POST':
        session['student_details'] = {
            "name": request.form.get('name'),
            "class": request.form.get('class'),
            "school": request.form.get('school'),
            "register_number": request.form.get('register_number', '')
        }
        flash('Student details saved temporarily. Please review the rules before starting.', 'success')
        return redirect(url_for('assessment.show_rules'))
        
    return render_template('assessment_form.html')

# --- This route is correct and does not need changes ---
@assessment_bp.route('/rules')
def show_rules():
    return render_template('rules.html')

# --- This route is correct and does not need changes ---
@assessment_bp.route('/test')
def start_test():
    if 'student_details' not in session:
        flash('Please enter your details before starting the test.', 'info')
        return redirect(url_for('assessment.take_assessment'))
    
    selected_class = session['student_details'].get('class')
    if not selected_class:
        flash('Class information is missing. Please re-enter your details.', 'danger')
        return redirect(url_for('assessment.take_assessment'))

    try:
        file_path = os.path.join(os.path.dirname(__file__), 'test_questions.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            all_questions_data = json.load(f)

        return render_template('test.html', test_questions=all_questions_data, selected_class=selected_class)
    except FileNotFoundError:
        flash('The test questions could not be loaded. Please contact an administrator.', 'danger')
        return redirect(url_for('home'))
    except KeyError:
        flash(f'No questions found for class {selected_class}. Please check the class or contact an administrator.', 'danger')
        return redirect(url_for('assessment.take_assessment'))

# --- UPDATED: This function now properly handles headers and data insertion ---
@assessment_bp.route('/submit', methods=['POST'])
def submit_test():
    """Evaluates text answers, retrieves details from session, and writes everything to Google Sheets."""
    
    print("--- SUBMIT TEST ROUTE TRIGGERED ---")
    print("Session data upon submission:", session)

    user_answers = request.form
    score = 0
    
    if 'student_details' not in session:
        flash('Your session expired. Please enter your details again.', 'warning')
        return redirect(url_for('assessment.take_assessment'))

    selected_class = session['student_details'].get('class')
    if not selected_class:
        flash('Class information is missing. Cannot submit test.', 'danger')
        return redirect(url_for('assessment.take_assessment'))

    try:
        file_path = os.path.join(os.path.dirname(__file__), 'test_questions.json')
        with open(file_path, 'r', encoding='utf-8') as f:
            all_questions_data = json.load(f)
        
        class_questions = all_questions_data.get(selected_class, [])
        if not class_questions:
            flash(f'No questions found for class {selected_class} to evaluate. Contact administrator.', 'danger')
            return redirect(url_for('assessment.take_assessment'))

        total_questions = len(class_questions)
        correct_answers_dict = {str(q['id']): q['answer'] for q in class_questions}
        
        questions_attempted = 0
        for q_id, correct_ans in correct_answers_dict.items():
            user_ans = user_answers.get(f'question_{q_id}')
            
            if user_ans and user_ans.strip() != '':
                questions_attempted += 1
                if user_ans.strip().lower() == correct_ans.strip().lower():
                    score += 1

        student_details = session.pop('student_details')
        score_percentage = f"{(score / total_questions) * 100:.0f}%" if total_questions > 0 else "0%"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create a dictionary mapping headers to values for better readability
        data_dict = {
            "Timestamp": timestamp,
            "Name": student_details.get('name', ''),
            "Class": student_details.get('class', ''),
            "School": student_details.get('school', ''),
            "Register Number": student_details.get('register_number', ''),
            "Questions Attempted": questions_attempted,
            "Score": score,
            "Score Percentage": score_percentage
        }
        
        # Convert to list in the correct order
        row_to_insert = [data_dict[header] for header in SHEET_HEADERS]

        print("Data prepared:")
        for header, value in data_dict.items():
            print(f"  {header}: {value}")

        print("Ensuring headers exist in Google Sheet...")
        ensure_headers_exist()

        print("Attempting to write data to Google Sheet...")
        SHEET.append_row(row_to_insert)
        
        print("Successfully wrote to Google Sheet.")
        print(f"Row inserted: {row_to_insert}")
        
        flash('Your test has been submitted successfully!', 'success')
        return redirect(url_for('assessment.thank_you'))

    except Exception as e:
        print(f"An error occurred during submission: {e}")
        import traceback
        traceback.print_exc()
        flash('Could not submit results due to a server error. Please try again.', 'danger')
        return redirect(url_for('assessment.start_test'))

# --- This route is correct and does not need changes ---
@assessment_bp.route('/thank_you')
def thank_you():
    return render_template('thank.html')

# --- Optional: Add a route to manually reset headers if needed ---
@assessment_bp.route('/admin/reset-headers', methods=['POST'])
def reset_headers():
    """Admin route to manually reset headers in Google Sheet"""
    try:
        ensure_headers_exist()
        return jsonify({"status": "success", "message": "Headers reset successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})