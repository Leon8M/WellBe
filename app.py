'''This is the WellBe app. Users can add and monitor their journal entries and goals'''
from flask import Flask, Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from models import User, JournalEntry, Goal, db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
app.config['SECRET_KEY'] = 'ThisIsA$tr0ngS3cretK&yF0rMyFl@skApp'

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

'''
Login manager
''' 
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

'''Root route redirects to login page'''
@app.route('/')
def index():
    return redirect('/login')

'''Route to register page. Takes user name and a password that is hashed; and sends to database'''
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            error_message = 'Username already exists!'
            return render_template('register.html', error=error_message)

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, hashed_password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

'''Route for login'''
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user is None:
            error_message = 'Invalid username or password'
            return render_template('login.html', error=error_message)

        if not check_password_hash(user.hashed_password, password):
            error_message = 'Invalid username or password'
            return render_template('login.html', error=error_message)

        login_user(user)
        return redirect(url_for('home'))

    return render_template('login.html')

'''This is the home page route. Obtains journal entries and goals from database and displys them'''
@app.route('/home')
@login_required
def home():
    user = current_user
    journal_entries = JournalEntry.query.filter_by(user_id=user.id).order_by(JournalEntry.date.desc()).all()
    goals = Goal.query.filter_by(user_id=user.id).all()
    return render_template('home.html', user=user, journal_entries=journal_entries, goals=goals)

'''This helps user log out of the app'''
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

'''This is the journal route used to add journal entries'''
@app.route('/journal', methods=['POST'])
@login_required
def add_journal_entry():
    if request.method == 'POST':
        content = request.form['content']
        new_entry = JournalEntry(user_id=current_user.id, date=datetime.now(), content=content)
        db.session.add(new_entry)
        db.session.commit()
        return redirect(url_for('home'))

'''This journal route helps with obtaining journal entries from database'''
@app.route('/journal/<date>', methods=['GET'])
@login_required
def get_journal_entries(date):
    date = datetime.strptime(date, '%Y-%m-%d').date()
    entries = JournalEntry.query.filter_by(user_id=current_user.id, date=date).all()
    return jsonify([entry.serialize() for entry in entries])

'''This is the goals route for adding goals'''
@app.route('/goals', methods=['POST'])
@login_required
def add_goal():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        new_goal = Goal(user_id=current_user.id, title=title, description=description)
        db.session.add(new_goal)
        db.session.commit()
        return redirect(url_for('home'))

'''This route is used to get goals from dtatabase'''
@app.route('/goals', methods=['GET'])
@login_required
def get_goals():
    goals = Goal.query.filter_by(user_id=current_user.id).all()
    return jsonify([goal.serialize() for goal in goals])

'''For updating goals'''
@app.route('/goals/<goal_id>', methods=['PUT'])
@login_required
def update_goal(goal_id):
    if request.method == 'PUT':
        data = request.get_json()  # Parse JSON data from request body
        if data:
            goal = Goal.query.get(goal_id)
            if goal:
                # Update goal attributes from JSON data
                goal.title = data.get('title', goal.title)
                goal.description = data.get('description', goal.description)
                goal.completed = data.get('completed', goal.completed)
                db.session.commit()
                return jsonify({'message': 'Goal updated successfully'})
            else:
                return jsonify({'error': 'Goal not found'})
        else:
            return jsonify({'error': 'Invalid request data'})

'''For deleting goals'''
@app.route('/goals/<goal_id>', methods=['DELETE'])
@login_required
def delete_goal(goal_id):
    if request.method == 'DELETE':
        goal = Goal.query.get(goal_id)
        if goal:
            db.session.delete(goal)
            db.session.commit()
            return jsonify({'message': 'Goal deleted successfully'})
        else:
            return jsonify({'error': 'Goal not found'})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
