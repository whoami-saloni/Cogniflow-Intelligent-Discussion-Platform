
import requests

# POST - Register user
res = requests.post('http://127.0.0.1:5000/register', json={
    'username': 'saloni2',
    'email': 'saloni2@example.com'
})
print("Register Response:", res.json())

# POST - Create a question
res = requests.post('http://127.0.0.1:5000/questions', json={
    'title': 'What is Flask?',
    'description': 'Please explain Flask in simple terms.',
    'user_id': 1  # You may need to confirm this user ID exists
})
print("Add Question Response:", res.json())

# GET - Fetch all questions again
res = requests.get('http://127.0.0.1:5000/questions')
print("Questions Response:", res.json())
