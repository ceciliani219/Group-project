from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 请替换为安全的密钥

# 模拟用户存储（实际应使用数据库）
users = {}

# 模拟房间数据
rooms = [
    {'id': 1, 'name': 'Breakout Room A', 'capacity': 4},
    {'id': 2, 'name': 'Breakout Room B', 'capacity': 6},
    {'id': 3, 'name': 'Breakout Room C', 'capacity': 8},
]

# 模拟预约记录存储（实际应使用数据库）
bookings = []

@app.route('/')
def index():
    return render_template('index.html', rooms=rooms)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users:
            flash('Username already exists! Please choose another.')
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(password)
        users[username] = {'password': hashed_pw}
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
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/book/<int:room_id>', methods=['GET', 'POST'])
def book(room_id):
    if 'username' not in session:
        flash('Please login to book a room.')
        return redirect(url_for('login'))
    room = next((r for r in rooms if r['id'] == room_id), None)
    if not room:
        flash('Room not found!')
        return redirect(url_for('index'))
    if request.method == 'POST':
        booking_date = request.form.get('booking_date')
        booking_time = request.form.get('booking_time')
        booking = {
            'room_id': room_id,
            'room_name': room['name'],
            'username': session['username'],
            'booking_date': booking_date,
            'booking_time': booking_time
        }
        bookings.append(booking)
        flash('Booking confirmed!')
        return redirect(url_for('booking_result', booking_index=len(bookings) - 1))
    return render_template('book.html', room=room)

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
