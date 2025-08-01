from flask import Blueprint, render_template
from flask_login import login_required
from models import User # Import the User model
from extensions import db

leaderboard = Blueprint('leaderboard', __name__)

@leaderboard.route('/leaderboard')
@login_required
def show_leaderboard():
    # Fetch all users, ordered by their score in descending order
    # You can limit the number of users displayed, e.g., .limit(10)
    top_users = User.query.order_by(User.score.desc()).all()
    return render_template('leaderboard.html', users=top_users)
