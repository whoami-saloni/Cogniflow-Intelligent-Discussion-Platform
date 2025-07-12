# Flask App Entry Point
# StackIt - A Minimal Q&A Forum Platform

from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from textblob import TextBlob
import spacy
nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stackit.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecret'

db = SQLAlchemy(app)

# ----------------------------- MODELS -----------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('questions', lazy=True))
    sentiment = db.Column(db.String(20), default="neutral")


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_accepted = db.Column(db.Boolean, default=False)
    user = db.relationship('User', backref=db.backref('answers', lazy=True))
    question = db.relationship('Question', backref=db.backref('answers', lazy=True))
    votes = db.relationship('Vote', backref='answer', lazy=True)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    vote_type = db.Column(db.String(10))  # 'up' or 'down'

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

# ----------------------------- AUTH ROUTES -----------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!')
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html', now=datetime.now)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html', now=datetime.now)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('index'))

@app.context_processor
def inject_notifications():
    if 'user_id' not in session:
        return dict(unread_count=0, notifications=[])
    user_id = session['user_id']
    unread = Notification.query.filter_by(user_id=user_id, is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    return dict(
        unread_count=len(unread),
        notifications=[{'message': n.message, 'created_at': n.created_at} for n in unread]
    )

# ----------------------------- MAIN ROUTES -----------------------------

@app.route('/', methods=['GET'])
def index():
    query = request.args.get('q')
    if query:
        questions = Question.query.filter(
            Question.title.ilike(f'%{query}%') |
            Question.description.ilike(f'%{query}%') |
            Question.tags.ilike(f'%{query}%')
        ).order_by(Question.created_at.desc()).all()
    else:
        questions = Question.query.order_by(Question.created_at.desc()).all()

    return render_template('index.html', questions=questions, username=session.get('username'), now=datetime.now, search_query=query or '')
   

@app.route('/ask', methods=['GET', 'POST'])
def ask_page():
    if 'user_id' not in session:
        flash('Please log in to ask a question.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.form
        description = data['description']
        sentiment = get_sentiment(description)
        auto_tags = generate_tags_from_description(description)

        new_question = Question(
            title=data['title'],
            description=description,
            user_id=session['user_id'],
            tags=auto_tags,
            sentiment=sentiment
        )
        db.session.add(new_question)
        db.session.commit()
        flash('Question submitted!')
        return redirect(url_for('index'))

    return render_template('ask.html', now=datetime.now)

@app.route('/questions/<int:qid>', methods=['GET', 'POST'])
def question_detail(qid):
    question = Question.query.get_or_404(qid)

    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please log in to answer questions.')
            return redirect(url_for('login'))
        content = request.form['content']
        answer = Answer(content=content, question_id=qid, user_id=session['user_id'])
        db.session.add(answer)

        # Add notification
        if question.user_id != session['user_id']:
            note = Notification(user_id=question.user_id, message=f"{session['username']} answered your question.")
            db.session.add(note)

        db.session.commit()
        flash('Answer added!')
        return redirect(url_for('question_detail', qid=qid))

    answers = question.answers

    vote_counts = {}
    for ans in answers:
        upvotes = sum(1 for v in ans.votes if v.vote_type == 'up')
        downvotes = sum(1 for v in ans.votes if v.vote_type == 'down')
        vote_counts[ans.id] = {'up': upvotes, 'down': downvotes}

    is_admin = False
    if 'user_id' in session:
        user = db.session.get(User, session['user_id'])
        is_admin = user.is_admin if user else False

    return render_template(
        'question_detail.html',
        question=question,
        answers=answers,
        vote_counts=vote_counts,
        username=session.get('username'),
        now=datetime.now,
        is_admin=is_admin
    )

@app.route('/answers/<int:aid>/vote', methods=['POST'])
def vote(aid):
    if 'user_id' not in session:
        flash('Please log in to vote.')
        return redirect(url_for('login'))
    data = request.form
    vote = Vote(answer_id=aid, user_id=session['user_id'], vote_type=data['type'])
    db.session.add(vote)
    db.session.commit()
    flash('Vote recorded!')
    return redirect(request.referrer)

def get_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # [-1.0, 1.0]
    if polarity > 0.1:
        return 'positive'
    elif polarity < -0.1:
        return 'negative'
    else:
        return 'neutral'

@app.route('/questions/<int:qid>/accept/<int:aid>', methods=['POST'])
def accept_answer(qid, aid):
    if 'user_id' not in session:
        flash('Login required to accept answers.')
        return redirect(url_for('login'))
    answer = Answer.query.get_or_404(aid)
    answer.is_accepted = True

    # Add notification to answer owner
    if answer.user_id != session['user_id']:
        note = Notification(user_id=answer.user_id, message=f"Your answer was accepted on '{answer.question.title}'")
        db.session.add(note)

    db.session.commit()
    flash('Answer accepted!')
    return redirect(url_for('question_detail', qid=qid))

@app.route('/admin')
def admin_dashboard():
    if not session.get('user_id'):
        flash("Login required")
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user or not user.is_admin:
        flash("Admin access only")
        return redirect(url_for('index'))
    users = User.query.all()
    questions = Question.query.order_by(Question.created_at.desc()).all()
    return render_template('admin_dashboard.html', users=users, questions=questions, username=session.get('username'))


@app.route('/admin/delete-question/<int:qid>', methods=['POST'])
def delete_question(qid):
    if not session.get('user_id'):
        flash("Login required")
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    if not user or not user.is_admin:
        flash("Admin access only")
        return redirect(url_for('index'))
    question = Question.query.get_or_404(qid)
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted successfully")
    return redirect(url_for('admin_dashboard'))

def generate_tags_from_description(description):
    doc = nlp(description)
    tags = set()

    for ent in doc.ents:
        if ent.label_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT', 'WORK_OF_ART', 'LANGUAGE']:
            tags.add(ent.text.lower())

    return ', '.join(tags)


# ----------------------------- INIT & RUN -----------------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Create admin only if not exists
        from werkzeug.security import generate_password_hash
        if not User.query.filter_by(email='admin@example.com').first():
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Admin user created: admin@example.com / admin123")
        else:
            print("ℹ️ Admin user already exists.")

    app.run(debug=True)


