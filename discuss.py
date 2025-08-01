# discuss.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Post, User # Import User to get username for display
from extensions import db
from datetime import datetime # Import datetime

discuss = Blueprint('discuss', __name__)

@discuss.route('/discuss')
@login_required
def forum_home():
    # Fetch all posts, ordered by creation date (newest first)
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('discuss_forum.html', posts=posts)

@discuss.route('/discuss/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    if request.method == 'POST':
        title = request.form['title'].strip()
        content = request.form['content'].strip()

        if not title or not content:
            flash('Title and content cannot be empty.', 'warning')
            return render_template('new_post.html')

        new_forum_post = Post(user_id=current_user.id, title=title, content=content, created_at=datetime.utcnow())
        db.session.add(new_forum_post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('discuss.forum_home'))

    return render_template('new_post.html')

@discuss.route('/discuss/<int:post_id>')
@login_required
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    # If you later add comments, you would fetch them here
    return render_template('post_detail.html', post=post)

# Optional: Add route to delete post (only for author or admin)
@discuss.route('/discuss/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        flash("You are not authorized to delete this post.", 'danger')
        return redirect(url_for('discuss.forum_home'))

    db.session.delete(post)
    db.session.commit()
    flash("Post deleted successfully!", 'info')
    return redirect(url_for('discuss.forum_home'))