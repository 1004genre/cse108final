from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///college_forum.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    major = db.Column(db.String(100))
    year = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    questions = db.relationship('Question', backref='author', lazy=True)
    answers = db.relationship('Answer', backref='author', lazy=True)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    questions = db.relationship('Question', backref='topic', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    answers = db.relationship('Answer', backref='question', lazy=True, cascade='all, delete-orphan')

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    votes = db.relationship('Vote', backref='answer', lazy=True, cascade='all, delete-orphan')

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'), nullable=False)
    vote_type = db.Column(db.String(10), nullable=False)

# Routes
@app.route('/')
def index():
    topics = Topic.query.all()
    topic_filter = request.args.get('topic')
    
    if topic_filter:
        questions = Question.query.filter_by(topic_id=topic_filter).order_by(Question.created_at.desc()).all()
    else:
        questions = Question.query.order_by(Question.created_at.desc()).all()
    
    return render_template('index.html', questions=questions, topics=topics, current_topic=topic_filter)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        major = request.form.get('major', '')
        year = request.form.get('year', '')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return redirect(url_for('signup'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('signup'))
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        new_user = User(username=username, email=email, password_hash=hashed_password, major=major, year=year)
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/ask', methods=['GET', 'POST'])
def ask_question():
    if 'user_id' not in session:
        flash('Please log in to ask a question!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        topic_id = request.form['topic_id']
        
        new_question = Question(title=title, content=content, user_id=session['user_id'], topic_id=topic_id)
        db.session.add(new_question)
        db.session.commit()
        
        flash('Question posted successfully!', 'success')
        return redirect(url_for('view_question', question_id=new_question.id))
    
    topics = Topic.query.all()
    return render_template('ask_question.html', topics=topics)

@app.route('/question/<int:question_id>', methods=['GET', 'POST'])
def view_question(question_id):
    question = Question.query.get_or_404(question_id)
    
    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please log in to answer!', 'error')
            return redirect(url_for('login'))
        
        content = request.form['content']
        new_answer = Answer(content=content, user_id=session['user_id'], question_id=question_id)
        db.session.add(new_answer)
        db.session.commit()
        
        flash('Answer posted successfully!', 'success')
        return redirect(url_for('view_question', question_id=question_id))
    
    answers = Answer.query.filter_by(question_id=question_id).order_by(Answer.upvotes.desc()).all()
    return render_template('question.html', question=question, answers=answers)

@app.route('/vote/<int:answer_id>/<vote_type>')
def vote(answer_id, vote_type):
    if 'user_id' not in session:
        flash('Please log in to vote!', 'error')
        return redirect(url_for('login'))
    
    answer = Answer.query.get_or_404(answer_id)
    user_id = session['user_id']
    
    existing_vote = Vote.query.filter_by(user_id=user_id, answer_id=answer_id).first()
    
    if existing_vote:
        if existing_vote.vote_type == 'upvote':
            answer.upvotes -= 1
        else:
            answer.downvotes -= 1
        
        if existing_vote.vote_type == vote_type:
            db.session.delete(existing_vote)
        else:
            existing_vote.vote_type = vote_type
            if vote_type == 'upvote':
                answer.upvotes += 1
            else:
                answer.downvotes += 1
    else:
        new_vote = Vote(user_id=user_id, answer_id=answer_id, vote_type=vote_type)
        db.session.add(new_vote)
        
        if vote_type == 'upvote':
            answer.upvotes += 1
        else:
            answer.downvotes += 1
    
    db.session.commit()
    return redirect(url_for('view_question', question_id=answer.question_id))

@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    questions = Question.query.filter_by(user_id=user.id).order_by(Question.created_at.desc()).all()
    answers = Answer.query.filter_by(user_id=user.id).order_by(Answer.created_at.desc()).all()
    return render_template('profile.html', user=user, questions=questions, answers=answers)

def init_db():
    with app.app_context():
        db.create_all()
        
        if Topic.query.count() == 0:
            default_topics = [
                Topic(name='Computer Science', description='Programming, algorithms, data structures'),
                Topic(name='Mathematics', description='Calculus, algebra, statistics'),
                Topic(name='Physics', description='Mechanics, electromagnetism, quantum'),
                Topic(name='Chemistry', description='Organic, inorganic, biochemistry'),
                Topic(name='Biology', description='Cell biology, genetics, ecology'),
                Topic(name='Engineering', description='Electrical, mechanical, civil'),
                Topic(name='Business', description='Accounting, finance, marketing'),
                Topic(name='General', description='Other topics and general questions')
            ]
            db.session.add_all(default_topics)
            db.session.commit()
            print("Database initialized with default topics!")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)