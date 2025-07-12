# 🧠 Cogniflow - Intelligent Discussion Platform for Developers and Researchers

Cogniflow is a smart, AI-enhanced Discussion platform designed for developers, data scientists, and researchers. Inspired by platforms like Stack Overflow, it goes a step further by integrating Natural Language Processing (NLP) features such as **sentiment analysis**, **named entity recognition**, and **auto-tag generation** to enhance the Q&A experience.

---
##  Problem Statement

**StackIt – A Minimal Q&A Forum Platform**

Build a user-friendly Q&A platform that allows users to post questions with rich text formatting, answer with voting, tagging, and a real-time notification system for enhanced community learning.

---

## 👩‍💻 Team Member

- **Saloni Sahal**  
  M.Tech CSE, University of Kalyani  
  📧 salonisahal15@gmail.com  
  🔗 [GitHub](https://github.com/whoami-saloni)

---

## 🚀 Features

### 🧠 Intelligent NLP
- **Sentiment Analysis** of questions using TextBlob.
- **NER-based Tag Generation** using spaCy for meaningful auto-tagging.
- **Search Bar** with keyword support to discover relevant questions.

### 📬 User Interactions
- Register/Login system with password hashing.
- Ask questions, post answers, and vote on content.
- Accept answers with notification to responders.

### 📌 Admin Dashboard
- View and manage all users and questions.
- Delete inappropriate or duplicate questions.
- Track recent activity across the community.

### 🔔 Notifications
- Real-time alerts when your question is answered or your answer is accepted.

---



## ⚙️ Tech Stack

| Component     | Technology                |
|--------------|---------------------------|
| Backend       | Flask, SQLAlchemy          |
| Frontend      | Jinja2, HTML/CSS (Tailwind), Quill.js |
| NLP/ML        | spaCy (NER), TextBlob (Sentiment) |
| Database      | SQLite (can scale to PostgreSQL) |
| Others        | Flask-CORS, Werkzeug Security |

---

## 🧪 Installation & Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/cogniflow.git
cd cogniflow

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model for NER
python -m spacy download en_core_web_sm

# Run the application
python app.py

