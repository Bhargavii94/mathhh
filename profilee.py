# profilee.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import User, Submission, Problem # Import necessary models
from extensions import db
from sqlalchemy import func # Import func for aggregation

profile = Blueprint('profile', __name__)

@profile.route('/profile')
@login_required
def view_profile():
    user = current_user

    # Calculate statistics like solved problems, total attempts
    solved_problems_query = db.session.query(Submission.problem_id)\
                                    .filter(Submission.user_id == user.id, Submission.result == 'Accepted')\
                                    .distinct()
    solved_problems_count = solved_problems_query.count()

    total_submissions = Submission.query.filter_by(user_id=user.id).count()

    # Update user's profile stats (optional, could be done periodically or on submission)
    # This ensures the counts are up-to-date when viewing the profile
    user.solved_problems_count = solved_problems_count
    user.total_problems_attempted = total_submissions
    db.session.commit()

    # Fetch recent accepted submissions (joining with Problem to get title)
    recent_submissions = db.session.query(Submission, Problem.title)\
                                    .join(Problem, Submission.problem_id == Problem.id)\
                                    .filter(Submission.user_id == user.id, Submission.result == 'Accepted')\
                                    .order_by(Submission.timestamp.desc())\
                                    .limit(5).all() # Get last 5 accepted

    return render_template('profile.html',
                           user=user,
                           solved_problems_count=solved_problems_count,
                           total_submissions=total_submissions,
                           recent_submissions=recent_submissions)

@profile.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    user = current_user
    if request.method == 'POST':
        user.college = request.form.get('college', '').strip() # Use '' as default for new fields
        user.bio = request.form.get('bio', '').strip()
        user.interests = request.form.get('interests', '').strip() # Changed from preferred_languages to interests

        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.view_profile'))

    return render_template('edit_profile.html', user=user)