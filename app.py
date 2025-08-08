from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from forms import RegisterForm, LoginForm, SubredditForm, PostForm, CommentForm
from models import db, User, Subreddit, Post, Comment, Vote

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.cli.command('init-db')
def init_db():
    with app.app_context():
        db.create_all()
        print('✅ Database initialized.')

@app.route('/')
def home():
    sort = request.args.get('sort', 'hot')
    q = Post.query
    if sort == 'new':
        posts = q.order_by(Post.created_at.desc()).all()
    else:  # hot = highest score
        posts = sorted(q.all(), key=lambda p: p.score, reverse=True)
    return render_template('index.html', posts=posts, sort=sort)

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already taken.', 'warning')
            return redirect(url_for('register'))
        user = User(
            username=form.username.data,
            password_hash=generate_password_hash(form.password.data)
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user, remember=True)
            flash('Welcome back!', 'success')
            return redirect(url_for('home'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/r/new', methods=['GET','POST'])
@login_required
def create_subreddit():
    form = SubredditForm()
    if form.validate_on_submit():
        if Subreddit.query.filter_by(name=form.name.data).first():
            flash('Subreddit name already exists.', 'warning')
            return redirect(url_for('create_subreddit'))
        sr = Subreddit(name=form.name.data, description=form.description.data, creator_id=current_user.id)
        db.session.add(sr)
        db.session.commit()
        flash('Subreddit created.', 'success')
        return redirect(url_for('home'))
    return render_template('create_subreddit.html', form=form)

@app.route('/r/<string:name>')
def view_subreddit(name):
    sr = Subreddit.query.filter_by(name=name).first_or_404()
    posts = sorted(sr.posts, key=lambda p: p.score, reverse=True)
    return render_template('index.html', posts=posts, subreddit=sr, sort='hot')

@app.route('/post/new', methods=['GET','POST'])
@login_required
def create_post():
    form = PostForm()
    form.subreddit.choices = [(s.id, f"r/{s.name}") for s in Subreddit.query.order_by(Subreddit.name).all()]
    if form.validate_on_submit():
        sr = Subreddit.query.get(form.subreddit.data)
        if not sr:
            flash('Invalid subreddit.', 'danger')
            return redirect(url_for('create_post'))
        post = Post(title=form.title.data, body=form.body.data, subreddit_id=sr.id, author_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash('Post created.', 'success')
        return redirect(url_for('post_detail', post_id=post.id))
    return render_template('create_post.html', form=form)

@app.route('/post/<int:post_id>', methods=['GET','POST'])
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            abort(403)
        c = Comment(body=form.body.data, author_id=current_user.id, post_id=post.id)
        db.session.add(c)
        db.session.commit()
        return redirect(url_for('post_detail', post_id=post.id))
    return render_template('post_detail.html', post=post, form=form)

@app.route('/vote/post/<int:post_id>/<string:direction>', methods=['POST'])
@login_required
def vote_post(post_id, direction):
    post = Post.query.get_or_404(post_id)
    value = 1 if direction == 'up' else -1
    vote = Vote.query.filter_by(user_id=current_user.id, post_id=post.id, comment_id=None).first()
    if vote and vote.value == value:
        db.session.delete(vote)
    elif vote:
        vote.value = value
    else:
        db.session.add(Vote(user_id=current_user.id, post_id=post.id, value=value))
    db.session.commit()
    return redirect(request.referrer or url_for('post_detail', post_id=post.id))

@app.route('/vote/comment/<int:comment_id>/<string:direction>', methods=['POST'])
@login_required
def vote_comment(comment_id, direction):
    comment = Comment.query.get_or_404(comment_id)
    value = 1 if direction == 'up' else -1
    vote = Vote.query.filter_by(user_id=current_user.id, comment_id=comment.id, post_id=None).first()
    if vote and vote.value == value:
        db.session.delete(vote)
    elif vote:
        vote.value = value
    else:
        db.session.add(Vote(user_id=current_user.id, comment_id=comment.id, value=value))
    db.session.commit()
    return redirect(request.referrer or url_for('post_detail', post_id=comment.post_id))

if __name__ == '__main__':
    app.run(debug=True)
