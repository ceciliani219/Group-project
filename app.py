from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import re  # Used for regular expression validation
import secrets  # Used for secure random key generation

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generates a secure random secret key

# Simulated user storage (a real database should be used)
# Format: {'username': {'password': hashed_password, 'email': user_email}}
users = {}

# Simulated room data
rooms = [
    {'id': 1, 'name': 'Breakout Room A', 'capacity': 4},
    {'id': 2, 'name': 'Breakout Room B', 'capacity': 6},
    {'id': 3, 'name': 'Breakout Room C', 'capacity': 8},
]

# Simulated booking records storage (a real database should be used)
bookings = []

@app.route('/')
def index():
    return render_template('index.html', rooms=rooms)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate username: only letters and numbers, length 1-10
        if not re.match(r'^[a-zA-Z0-9]{1,10}$', username):
            flash('Username must be 1-10 characters long and contain only letters and numbers.')
            return redirect(url_for('register'))

        # Validate email format
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            flash('Invalid email format.')
            return redirect(url_for('register'))

        # Validate password: 8-16 characters, at least one uppercase letter, only letters and numbers
        if not re.match(r'^(?=.*[A-Z])[A-Za-z0-9]{8,16}$', password):
            flash('Password must be 8-16 characters long, contain at least one uppercase letter, and include only letters and numbers.')
            return redirect(url_for('register'))

        if username in users:
            flash('Username already exists! Please choose another.')
            return redirect(url_for('register'))

        # Hash the password and store user information
        hashed_pw = generate_password_hash(password)
        users[username] = {'password': hashed_pw, 'email': email}
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = users.get(username)
        if user and check_password_hash(user['password'], password):
            session['username'] = username
            flash('Login successful!')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password!')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        new_password = request.form.get('new_password')

        # Validate if user exists and email matches
        if username not in users or users[username]['email'] != email:
            flash('Invalid username or email.')
            return redirect(url_for('forgot_password'))

        # Update password
        hashed_pw = generate_password_hash(new_password)
        users[username]['password'] = hashed_pw
        flash('Password has been reset. Please login.')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')

@app.route('/book/<int:room_id>', methods=['GET', 'POST'])
def book(room_id):
    if 'username' not in session:
        flash('Please login to book a room.')
        return redirect(url_for('login'))

    room = next((r for r in rooms if r['id'] == room_id), None)
    if not room:
        flash('Room not found!')
        return redirect(url_for('index'))

    today = datetime.now().date()
    current_time = datetime.now().strftime("%H:%M")

    if request.method == 'POST':
        booking_date = request.form.get('booking_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        try:
            booking_date_obj = datetime.strptime(booking_date, "%Y-%m-%d").date()
            start_time_obj = datetime.strptime(start_time, "%H:%M").time()
            end_time_obj = datetime.strptime(end_time, "%H:%M").time()
        except ValueError:
            flash("Invalid date or time format.")
            return redirect(url_for('book', room_id=room_id))

        # Prevent booking for past dates
        if booking_date_obj < today:
            flash('You cannot book a room for a past date.')
            return redirect(url_for('book', room_id=room_id))

        # Prevent booking for past hours on the current date
        if booking_date_obj == today and start_time <= current_time:
            flash('You cannot book a time that has already passed today.')
            return redirect(url_for('book', room_id=room_id))

        # Ensure end time is later than start time
        if start_time_obj >= end_time_obj:
            flash('End time must be later than start time.')
            return redirect(url_for('book', room_id=room_id))

        # Limit booking duration to a maximum of 2 hours
        max_duration = timedelta(hours=2)
        # Combine today's date with the times for a proper duration comparison
        if datetime.combine(today, end_time_obj) - datetime.combine(today, start_time_obj) > max_duration:
            flash('Booking duration cannot exceed 2 hours.')
            return redirect(url_for('book', room_id=room_id))

        # Conflict detection: Check if the same room is already booked during the requested time slot,
        # regardless of the booking user.
        for existing in bookings:
            if (
                existing['room_id'] == room_id and
                existing['booking_date'] == booking_date and
                not (end_time_obj <= datetime.strptime(existing['start_time'], "%H:%M").time() or 
                     start_time_obj >= datetime.strptime(existing['end_time'], "%H:%M").time())
            ):
                flash('This room is already booked for the selected time slot. Please choose a different time.')
                return redirect(url_for('book', room_id=room_id))

        # Store booking information if no conflicts are found
        booking = {
            'room_id': room_id,
            'room_name': room['name'],
            'username': session['username'],
            'booking_date': booking_date,
            'start_time': start_time,
            'end_time': end_time
        }
        bookings.append(booking)
        flash(f'Booking confirmed from {start_time} to {end_time}!')
        return redirect(url_for('booking_result', booking_index=len(bookings) - 1))

    return render_template('book.html', room=room, today=today)

@app.route('/booking_result/<int:booking_index>')
def booking_result(booking_index):
    if booking_index < 0 or booking_index >= len(bookings):
        flash('Booking not found!')
        return redirect(url_for('index'))
    booking = bookings[booking_index]
    return render_template('booking_result.html', booking=booking)

@app.route('/my_bookings')
def my_bookings():
    if 'username' not in session:
        flash('Please login to view your bookings.')
        return redirect(url_for('login'))
    user_bookings = [b for b in bookings if b['username'] == session['username']]
    return render_template('my_bookings.html', bookings=user_bookings)

if __name__ == '__main__':
    app.run(debug=True)

