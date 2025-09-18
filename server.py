from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
import uuid
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this in production
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)  # Ensure data directory exists

# Predefined users (username: {password, is_admin, profile})
users = {
    "asad": {"password": "asad369", "is_admin": True, "profile": {"bio": "Admin user", "avatar": "default.png"}},
    "daniello": {"password": "rtf567", "is_admin": False, "profile": {"bio": "Regular user", "avatar": "default.png"}},
    "shalil": {"password": "urq987", "is_admin": False, "profile": {"bio": "Regular user", "avatar": "default.png"}},
    "roham": {"password": "yrc751", "is_admin": False, "profile": {"bio": "Regular user", "avatar": "default.png"}},
    "nazari": {"password": "kae422", "is_admin": False, "profile": {"bio": "Regular user", "avatar": "default.png"}},
    "90ee": {"password": "yez612", "is_admin": False, "profile": {"bio": "Regular user", "avatar": "default.png"}},
    "prime": {"password": "hhq091", "is_admin": False, "profile": {"bio": "Regular user", "avatar": "default.png"}},
    "mommen": {"password": "ggr789", "is_admin": False, "profile": {"bio": "Regular user", "avatar": "default.png"}},
    "erfan": {"password": "hwo935", "is_admin": False, "profile": {"bio": "Regular user", "avatar": "default.png"}},
    "mahiar": {"password": "wer098", "is_admin": False, "profile": {"bio": "Regular user", "avatar": "default.png"}}
}

# Data storage files
POLLS_FILE = 'data/polls.json'
NEWS_FILE = 'data/news.json'
MESSAGES_FILE = 'data/messages.json'

def load_json(file_path):
    # Create file with empty list if it doesn't exist
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            json.dump([], f)
        return []
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        # If file is corrupted or doesn't exist, create a new one
        with open(file_path, 'w') as f:
            json.dump([], f)
        return []

def save_json(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session['username'] != 'asad':
            flash("Admin access required")
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'username' in session:
        news = load_json(NEWS_FILE)
        return render_template('index.html', username=session['username'], 
                               is_admin=session.get('is_admin', False), news=news)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username]['password'] == password:
            session['username'] = username
            session['is_admin'] = users[username]['is_admin']
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_panel():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_user':
            new_username = request.form.get('new_username')
            new_password = request.form.get('new_password')
            
            if new_username and new_password:
                users[new_username] = {
                    "password": new_password,
                    "is_admin": False,
                    "profile": {"bio": "New user", "avatar": "default.png"}
                }
                flash(f"User {new_username} added")
        
        elif action == 'delete_user':
            user_to_delete = request.form.get('user_to_delete')
            if user_to_delete in users and user_to_delete != 'asad':
                del users[user_to_delete]
                flash(f"User {user_to_delete} deleted")
        
        elif action == 'change_password':
            user = request.form.get('user_to_change')
            new_password = request.form.get('new_password_value')
            
            if user in users and new_password:
                users[user]['password'] = new_password
                flash(f"Password for {user} changed")
    
    return render_template('admin.html', users=users, username=session['username'])

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'POST':
        bio = request.form.get('bio', '')
        avatar = request.files.get('avatar')
        
        users[session['username']]['profile']['bio'] = bio
        
        if avatar and avatar.filename:
            filename = secure_filename(avatar.filename)
            ext = filename.rsplit('.', 1)[1].lower()
            new_filename = f"{session['username']}_{uuid.uuid4().hex[:8]}.{ext}"
            avatar.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
            users[session['username']]['profile']['avatar'] = new_filename
        
        flash('Profile updated successfully')
    
    return render_template('account.html', 
                          username=session['username'],
                          profile=users[session['username']]['profile'])

@app.route('/user/<username>')
@login_required
def user_profile(username):
    if username in users:
        return render_template('profile.html', 
                              profile_user=username, 
                              profile_data=users[username]['profile'],
                              current_user=session['username'])
    else:
        flash('User not found')
        return redirect(url_for('index'))

@app.route('/news', methods=['GET', 'POST'])
@login_required
def news():
    news_items = load_json(NEWS_FILE)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_news':
            title = request.form.get('title')
            content = request.form.get('content')
            
            if title and content:
                new_item = {
                    'id': str(uuid.uuid4()),
                    'title': title,
                    'content': content,
                    'author': session['username'],
                    'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                news_items.append(new_item)
                save_json(news_items, NEWS_FILE)
                flash('News article added')
        
        elif action == 'delete_news':
            news_id = request.form.get('news_id')
            if session['username'] == 'asad':  # Admin can delete any
                news_items = [item for item in news_items if item['id'] != news_id]
            else:  # Users can only delete their own
                news_items = [item for item in news_items if not (item['id'] == news_id and item['author'] == session['username'])]
            
            save_json(news_items, NEWS_FILE)
            flash('News article deleted')
    
    return render_template('news.html', news=news_items, username=session['username'])

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    messages = load_json(MESSAGES_FILE)
    
    if request.method == 'POST':
        message_content = request.form.get('message')
        if message_content:
            # Process mentions and hashtags
            processed_content = process_text(message_content)
            
            new_message = {
                'id': str(uuid.uuid4()),
                'content': processed_content,
                'author': session['username'],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            messages.append(new_message)
            save_json(messages, MESSAGES_FILE)
    
    return render_template('chat.html', messages=messages, username=session['username'])

@app.route('/polls', methods=['GET', 'POST'])
@login_required
def polls():
    polls = load_json(POLLS_FILE)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create_poll':
            poll_name = request.form.get('poll_name')
            if poll_name:
                new_poll = {
                    'id': str(uuid.uuid4()),
                    'name': poll_name,
                    'creator': session['username'],
                    'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'votes_agree': [],
                    'votes_disagree': []
                }
                polls.append(new_poll)
                save_json(polls, POLLS_FILE)
                flash('Poll created')
        
        elif action == 'vote':
            poll_id = request.form.get('poll_id')
            vote_type = request.form.get('vote_type')
            
            for poll in polls:
                if poll['id'] == poll_id:
                    # Remove previous votes from this user
                    if session['username'] in poll['votes_agree']:
                        poll['votes_agree'].remove(session['username'])
                    if session['username'] in poll['votes_disagree']:
                        poll['votes_disagree'].remove(session['username'])
                    
                    # Add new vote
                    if vote_type == 'agree':
                        poll['votes_agree'].append(session['username'])
                    elif vote_type == 'disagree':
                        poll['votes_disagree'].append(session['username'])
                    
                    save_json(polls, POLLS_FILE)
                    break
    
    return render_template('polls.html', polls=polls, username=session['username'])

def process_text(text):
    # Process mentions (@username)
    words = text.split()
    processed_words = []
    for word in words:
        if word.startswith('@'):
            username = word[1:]
            if username in users:
                processed_words.append(f'<a href="/user/{username}" class="mention">@{username}</a>')
            else:
                processed_words.append(word)
        elif word.startswith('#'):
            parts = word.split('_', 1)
            if len(parts) > 1 and parts[0] in ['#agree', '#disagree']:
                poll_name = parts[1]
                processed_words.append(f'<a href="/polls" class="hashtag">{word}</a>')
            else:
                processed_words.append(f'<span class="hashtag">{word}</span>')
        else:
            processed_words.append(word)
    
    return ' '.join(processed_words)

# API endpoint for file uploads in chat
@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file:
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"{session['username']}_{uuid.uuid4().hex[:8]}.{ext}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
        
        # Add message about the upload
        messages = load_json(MESSAGES_FILE)
        new_message = {
            'id': str(uuid.uuid4()),
            'content': f'<a href="/static/uploads/{new_filename}" target="_blank">Uploaded file: {filename}</a>',
            'author': session['username'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        messages.append(new_message)
        save_json(messages, MESSAGES_FILE)
        
        return jsonify({'success': True, 'filename': new_filename})

if __name__ == '__main__':
    app.run(debug=True)
