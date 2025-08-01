# models.py
from extensions import db
from flask_login import UserMixin
from sqlalchemy.dialects.sqlite import JSON # Import JSON type for SQLite
from datetime import datetime # Import datetime for timestamps

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    submissions = db.relationship('Submission', backref='user', lazy=True)
    quiz_attempts = db.relationship('QuizAttempt', backref='user', lazy=True) # Added from standard setup
    posts = db.relationship('Post', backref='author', lazy=True) # <<< ADD THIS LINE! <<<

    # --- New/Updated Profile Fields ---
    college = db.Column(db.String(100), nullable=True, default="N/A")
    bio = db.Column(db.Text, nullable=True, default="No bio yet.")
    # Changed from preferred_languages to interests
    interests = db.Column(db.String(200), nullable=True, default="Mathematics") # e.g., "Algebra, Geometry, Calculus"
    solved_problems_count = db.Column(db.Integer, default=0) # To track problems solved
    total_problems_attempted = db.Column(db.Integer, default=0) # To track total attempts
    score = db.Column(db.Integer, default=0) # New: To track user's cumulative score for leaderboard

    def __repr__(self):
        return f"<User {self.username}>"

class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    difficulty_level = db.Column(db.Integer, nullable=False, default=1) # 1=Easy, 2=Medium, 3=Hard (used previously)
    answer = db.Column(db.String(100), nullable=False) # For simple direct answer problems
    submissions = db.relationship('Submission', backref='problem', lazy=True)

    def __repr__(self):
        return f"<Problem {self.title}>"

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problem.id'), nullable=False)
    submitted_answer = db.Column(db.String(100), nullable=False) # Store the user's direct answer
    result = db.Column(db.String(100), nullable=False) # e.g., "Accepted", "Wrong Answer", "Error"
    timestamp = db.Column(db.DateTime, default=datetime.utcnow) # Use datetime.utcnow for timezone-aware timestamps

    def __repr__(self):
        return f"<Submission {self.id} by User {self.user_id} for Problem {self.problem_id}>"

# --- Models for "Explore" (Videos) ---
class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    youtube_id = db.Column(db.String(50), nullable=False, unique=True) # Unique YouTube video ID
    topic = db.Column(db.String(50), nullable=False)
    class_level = db.Column(db.String(20), nullable=False) # e.g., 'Class 10', 'Class 12'
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Video {self.title} ({self.youtube_id})>"

# --- Models for "Quiz" ---
class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    topic = db.Column(db.String(50), nullable=False)
    class_level = db.Column(db.String(20), nullable=False)
    pass_mark = db.Column(db.Integer, nullable=False, default=5) # Passing marks (e.g., 5 out of 10)
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade="all, delete-orphan") # Cascade delete questions

    def __repr__(self):
        return f"<Quiz {self.title}>"

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    options = db.relationship('Option', backref='question', lazy=True, cascade="all, delete-orphan") # Cascade delete options

    def __repr__(self):
        return f"<Question {self.text[:50]}...>"

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    text = db.Column(db.String(200), nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f"<Option {self.text[:50]}...> (Correct: {self.is_correct})"

class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    passed = db.Column(db.Boolean, nullable=False)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<QuizAttempt User:{self.user_id} Quiz:{self.quiz_id} Score:{self.score}/{self.total_questions}>"

# --- Models for "Discuss/Reviews" (Forum Posts) ---
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(250), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Post {self.title[:50]}...>"