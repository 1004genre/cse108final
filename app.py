from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Topic, Question, Answer, Vote
from forms import RegistrationForm, LoginForm, QuestionForm, AnswerForm
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_tables():
    db.create_all()
    # Add default topics if not exist
    if not Topic.query.first():
        topics = ['Python', 'Java', 'JavaScript', 'C++', 'Web Development', 'Data Science', 'General']
        for name in topics:
            db.session.add(Topic(name=name))
        db.session.commit()

@app.route('/')
def home():
    topic_id = request.args.get('topic', type=int)
    if topic_id:
        questions = Question.query.filter_by(topic_id=topic_id).order_by(Question.created_at.desc()).all()
    else:
        questions = Question.query.order_by(Question.created_at.desc()).all()
    topics = Topic.query.all()
    return render_template('home.html', questions=questions, topics=topics, selected_topic=topic_id)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('home'))
        flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/ask', methods=['GET', 'POST'])
@login_required
def ask():
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(title=form.title.data, content=form.content.data,
                            user_id=current_user.id, topic_id=form.topic.data)
        db.session.add(question)
        db.session.commit()
        flash('Question posted!', 'success')
        return redirect(url_for('question', question_id=question.id))
    return render_template('ask.html', form=form)

@app.route('/question/<int:question_id>')
def question(question_id):
    question = Question.query.get_or_404(question_id)
    answers = Answer.query.filter_by(question_id=question_id).order_by(Answer.created_at).all()
    answer_form = AnswerForm()
    return render_template('question.html', question=question, answers=answers, form=answer_form)

@app.route('/answer/<int:question_id>', methods=['POST'])
@login_required
def answer(question_id):
    form = AnswerForm()
    if form.validate_on_submit():
        answer = Answer(content=form.content.data, user_id=current_user.id, question_id=question_id)
        db.session.add(answer)
        db.session.commit()
        flash('Answer posted!', 'success')
    return redirect(url_for('question', question_id=question_id))

@app.route('/vote/<int:answer_id>/<int:vote_type>')
@login_required
def vote(answer_id, vote_type):
    if vote_type not in [1, -1]:
        abort(400)
    existing_vote = Vote.query.filter_by(user_id=current_user.id, answer_id=answer_id).first()
    if existing_vote:
        if existing_vote.vote_type == vote_type:
            db.session.delete(existing_vote)
        else:
            existing_vote.vote_type = vote_type
    else:
        vote = Vote(user_id=current_user.id, answer_id=answer_id, vote_type=vote_type)
        db.session.add(vote)
    db.session.commit()
    return redirect(request.referrer or url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        create_tables()
    app.run(debug=True)