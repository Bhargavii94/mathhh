# problems.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Problem, Submission, User # Import User model
from extensions import db


problems = Blueprint('problems', __name__)

@problems.route('/dashboard')
@login_required
def dashboard():
    # Get all unique topics for display
    topics = db.session.query(Problem.topic).distinct().all()
    # Flatten the list of tuples into a simple list of strings
    topics = sorted([t[0] for t in topics])

    # Get filter and sort parameters from URL query string
    selected_topic = request.args.get('topic')
    sort_order = request.args.get('sort', 'asc') # 'asc' for easy to difficult, 'desc' for difficult to easy

    query = Problem.query

    # Apply topic filter if selected
    if selected_topic and selected_topic != 'All Topics': # 'All Topics' is a special case for no filter
        query = query.filter_by(topic=selected_topic)

    # Apply sorting
    if sort_order == 'asc':
        query = query.order_by(Problem.difficulty_level.asc())
    elif sort_order == 'desc':
        query = query.order_by(Problem.difficulty_level.desc())
    else:
        # Default sorting if no valid sort_order is provided
        query = query.order_by(Problem.id.asc()) # Or by title, etc.

    all_problems = query.all()

    return render_template('dashboard.html',
                           problems=all_problems,
                           topics=topics,
                           selected_topic=selected_topic,
                           sort_order=sort_order)

@problems.route('/problem/<int:pid>', methods=['GET', 'POST'])
@login_required
def problem_detail(pid):
    problem = Problem.query.get_or_404(pid)
    result = None
    submitted_answer_value = "" # To persist user's last submitted answer

    if request.method == 'POST':
        submitted_answer = request.form['answer']
        submitted_answer_value = submitted_answer # Store for re-rendering

        # Check the submitted answer
        result = check_answer(submitted_answer, problem.answer)

        # Save the submission
        submission = Submission(user_id=current_user.id, problem_id=pid, submitted_answer=submitted_answer, result=result)
        db.session.add(submission)

        # Update user's solved problems count and score if the answer is accepted
        if result == "Accepted":
            # Check if this specific problem has been previously solved by the user
            # We only want to increment solved_problems_count and score once per unique problem
            existing_accepted_submission = Submission.query.filter_by(
                user_id=current_user.id, problem_id=pid, result='Accepted'
            ).first()

            if  existing_accepted_submission: # Only increment if it's a new accepted solution for this problem
                current_user.solved_problems_count += 1
                # You can define how much score a problem gives, e.g., based on difficulty
                current_user.score += problem.difficulty_level * 10 # Example: Easy=10, Medium=20, Hard=30 points
                
                # IMPORTANT: Add the current_user object to the session to track its changes
                db.session.add(current_user) 
        
        # Commit all changes (submission and user updates) in one go
        db.session.commit()
        flash(f"Submission Result: {result}", 'info')

    # Fetch previous submissions for this user and problem
    user_submissions = Submission.query.filter_by(
        user_id=current_user.id, problem_id=pid
    ).order_by(Submission.timestamp.desc()).all()

    return render_template('problem_detail.html',
                           problem=problem,
                           result=result,
                           submitted_answer_value=submitted_answer_value,
                           user_submissions=user_submissions)

def check_answer(submitted_answer, correct_answer):
    """
    Checks if the submitted answer matches the correct answer.
    Allows for float comparison with a tolerance for numerical problems.
    """
    try:
        # Trim whitespace from both answers for robust comparison
        clean_submitted = submitted_answer.strip()
        clean_correct = correct_answer.strip()

        # Direct string comparison first (for exact matches like "180")
        if clean_submitted == clean_correct:
            return "Accepted"

        # Attempt float comparison for numerical answers, allowing for minor precision differences
        submitted_float = float(clean_submitted)
        correct_float = float(clean_correct)
        if abs(submitted_float - correct_float) < 1e-6: # Tolerance for float comparison
            return "Accepted"

    except ValueError:
        # If conversion to float fails, it's not a valid number or not numerically equivalent
        pass # Fall through to "Wrong Answer"

    return "Wrong Answer"
