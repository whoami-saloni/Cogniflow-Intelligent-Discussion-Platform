# Flask routes with pagination, filters, and basic CSS support for StackIt

from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, User, Question, Answer, Vote
from datetime import datetime
from sqlalchemy import or_
import math

app = Flask(__name__)
app.secret_key = 'supersecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stackit.db'
db.init_app(app)

# ---------------------- ROUTES ----------------------

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    tag_filter = request.args.get('tag', '')
    page = int(request.args.get('page', 1))
    per_page = 5

    query = Question.query
    if search_query:
        query = query.filter(or_(
            Question.title.ilike(f"%{search_query}%"),
            Question.description.ilike(f"%{search_query}%")
        ))
    if tag_filter:
        query = query.filter(Question.tags.ilike(f"%{tag_filter}%"))

    total_questions = query.count()
    questions = query.order_by(Question.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    total_pages = math.ceil(total_questions / per_page)

    return render_template('index.html', questions=questions, page=page, total_pages=total_pages)

@app.route('/ask', methods=['GET', 'POST'])
def ask():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        tags = request.form['tags']
        user_id = 1  # demo user
        question = Question(title=title, description=description, tags=tags, user_id=user_id)
        db.session.add(question)
        db.session.commit()
        flash('Question submitted!')
        return redirect(url_for('index'))
    return render_template('ask.html')

@app.route('/questions/<int:qid>', methods=['GET', 'POST'])
def question_detail(qid):
    question = Question.query.get_or_404(qid)
    if request.method == 'POST':
        content = request.form['content']
        answer = Answer(content=content, question_id=qid, user_id=1)
        db.session.add(answer)
        db.session.commit()
        flash('Answer added!')
        return redirect(url_for('question_detail', qid=qid))

    return render_template('question_detail.html', question=question)

@app.route('/answers/<int:aid>/vote', methods=['POST'])
def vote_answer(aid):
    vote_type = request.form['vote']
    vote = Vote(answer_id=aid, user_id=1, vote_type=vote_type)
    db.session.add(vote)
    db.session.commit()
    flash('Vote recorded!')
    return redirect(request.referrer)

@app.route('/questions/<int:qid>/accept/<int:aid>', methods=['POST'])
def accept_answer(qid, aid):
    answer = Answer.query.get_or_404(aid)
    answer.is_accepted = True
    db.session.commit()
    flash('Answer accepted!')
    return redirect(url_for('question_detail', qid=qid))




# ---------------------- INIT ----------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)