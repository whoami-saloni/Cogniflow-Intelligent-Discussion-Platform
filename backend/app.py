# Flask App Entry Point
# StackIt - A Minimal Q&A Forum Platform

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
from models import db, init_db

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stackit.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ----------------------------- MODELS -----------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('questions', lazy=True))

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_accepted = db.Column(db.Boolean, default=False)
    user = db.relationship('User', backref=db.backref('answers', lazy=True))
    question = db.relationship('Question', backref=db.backref('answers', lazy=True))

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey('answer.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    vote_type = db.Column(db.String(10))  # 'up' or 'down'

# ----------------------------- ROUTES -----------------------------

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    new_user = User(username=data['username'], email=data['email'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'})

@app.route('/questions', methods=['GET', 'POST'])
def questions():
    if request.method == 'POST':
        data = request.get_json()
        new_question = Question(
            title=data['title'],
            description=data['description'],
            user_id=data['user_id']
        )
        db.session.add(new_question)
        db.session.commit()
        return jsonify({'message': 'Question added'})
    else:
        all_q = Question.query.order_by(Question.created_at.desc()).all()
        return jsonify([{
            'id': q.id,
            'title': q.title,
            'description': q.description,
            'user': q.user.username,
            'created_at': q.created_at.isoformat()
        } for q in all_q])

@app.route('/questions/<int:qid>/answers', methods=['POST'])
def add_answer(qid):
    data = request.get_json()
    new_answer = Answer(
        content=data['content'],
        question_id=qid,
        user_id=data['user_id']
    )
    db.session.add(new_answer)
    db.session.commit()
    return jsonify({'message': 'Answer submitted'})

@app.route('/answers/<int:aid>/vote', methods=['POST'])
def vote(aid):
    data = request.get_json()
    vote = Vote(answer_id=aid, user_id=data['user_id'], vote_type=data['type'])
    db.session.add(vote)
    db.session.commit()
    return jsonify({'message': 'Vote recorded'})

@app.route('/questions/<int:qid>/accept/<int:aid>', methods=['POST'])
def accept_answer(qid, aid):
    answer = Answer.query.get_or_404(aid)
    answer.is_accepted = True
    db.session.commit()
    return jsonify({'message': 'Answer marked as accepted'})

# ----------------------------- INIT & RUN -----------------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # safely within app context

    app.run(debug=True)

