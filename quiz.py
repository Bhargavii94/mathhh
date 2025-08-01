# quiz.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Quiz, Question, Option, QuizAttempt
from extensions import db

quiz = Blueprint('quiz', __name__)

@quiz.route('/quizzes')
@login_required
def quiz_selection():
    # Fetch all unique topics and class levels for quiz filtering
    quiz_topics = db.session.query(Quiz.topic).distinct().all()
    quiz_class_levels = db.session.query(Quiz.class_level).distinct().all()

    quiz_topics = sorted([t[0] for t in quiz_topics])
    quiz_class_levels = sorted([c[0] for c in quiz_class_levels])

    selected_topic = request.args.get('topic')
    selected_class_level = request.args.get('class_level')

    query = Quiz.query

    if selected_topic and selected_topic != 'All Topics':
        query = query.filter_by(topic=selected_topic)
    if selected_class_level and selected_class_level != 'All Classes':
        query = query.filter_by(class_level=selected_class_level)

    available_quizzes = query.order_by(Quiz.title.asc()).all()

    # Fetch user's latest attempt for each quiz to display score/status
    user_latest_attempts = {}
    for q in available_quizzes:
        latest_attempt = QuizAttempt.query.filter_by(user_id=current_user.id, quiz_id=q.id)\
                                        .order_by(QuizAttempt.attempted_at.desc()).first()
        user_latest_attempts[q.id] = latest_attempt

    return render_template('quiz_selection.html',
                           quizzes=available_quizzes,
                           topics=quiz_topics,
                           class_levels=quiz_class_levels,
                           selected_topic=selected_topic,
                           selected_class_level=selected_class_level,
                           user_latest_attempts=user_latest_attempts)

@quiz.route('/quiz/<int:quiz_id>/start', methods=['GET', 'POST'])
@login_required
def start_quiz(quiz_id):
    current_quiz = Quiz.query.get_or_404(quiz_id)
    questions = Question.query.filter_by(quiz_id=quiz_id).order_by(Question.id.asc()).all()

    if not questions:
        flash("This quiz has no questions yet!", 'warning')
        return redirect(url_for('quiz.quiz_selection'))

    if request.method == 'POST':
        score = 0
        total_questions = len(questions)
        for q in questions:
            # Get the submitted option ID for this question
            submitted_option_id = request.form.get(f'question_{q.id}')
            if submitted_option_id:
                # Find the option that was submitted
                selected_option = Option.query.get(int(submitted_option_id))
                if selected_option and selected_option.is_correct:
                    score += 1

        passed = score >= current_quiz.pass_mark
        new_attempt = QuizAttempt(
            user_id=current_user.id,
            quiz_id=quiz_id,
            score=score,
            total_questions=total_questions,
            passed=passed
        )
        db.session.add(new_attempt)
        db.session.commit()

        return redirect(url_for('quiz.quiz_result', attempt_id=new_attempt.id))

    return render_template('start_quiz.html', quiz=current_quiz, questions=questions)


@quiz.route('/quiz/result/<int:attempt_id>')
@login_required
def quiz_result(attempt_id):
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    # Ensure the user is viewing their own attempt
    if attempt.user_id != current_user.id:
        flash("You are not authorized to view this quiz attempt.", 'danger')
        return redirect(url_for('quiz.quiz_selection'))

    quiz_taken = Quiz.query.get(attempt.quiz_id)
    return render_template('quiz_result.html', attempt=attempt, quiz=quiz_taken)