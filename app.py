from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import re  # 用于正则验证

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 请替换为安全的密钥

# 模拟用户存储（实际应使用数据库）
# 格式：{'username': {'password': hashed_password, 'email': user_email}}
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
        email = request.form.get('email')
        password = request.form.get('password')

        # 验证用户名：仅允许字母和数字，长度 1-10
        if not re.match(r'^[a-zA-Z0-9]{1,10}$', username):
            flash('Username must be 1-10 characters long and contain only letters and numbers.')
            return redirect(url_for('register'))

        # 验证邮箱格式
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            flash('Invalid email format.')
            return redirect(url_for('register'))

        # 验证密码：8-16个字符，至少一个大写字母，只允许字母和数字
        if not re.match(r'^(?=.*[A-Z])[A-Za-z0-9]{8,16}$', password):
            flash('Password must be 8-16 characters long, contain at least one uppercase letter, and include only letters and numbers.')
            return redirect(url_for('register'))

        if username in users:
            flash('Username already exists! Please choose another.')
            return redirect(url_for('register'))

        # 哈希处理密码并存储用户信息
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
    session.clear()  # 清除所有 session 数据
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        new_password = request.form.get('new_password')

        # 验证用户是否存在且邮箱匹配
        if username not in users or users[username]['email'] != email:
            flash('Invalid username or email.')
            return redirect(url_for('forgot_password'))

        # 更新密码
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

    if request.method == 'POST':
        booking_date = request.form.get('booking_date')
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')

        try:
            start_time_obj = datetime.strptime(start_time, "%H:%M")
            end_time_obj = datetime.strptime(end_time, "%H:%M")
        except ValueError:
            flash("Invalid time format. Please use HH:MM format.")
            return redirect(url_for('book', room_id=room_id))

        # 确保结束时间晚于开始时间
        if start_time_obj >= end_time_obj:
            flash('End time must be later than start time.')
            return redirect(url_for('book', room_id=room_id))

        # 限制预约时长不超过2小时
        max_duration = timedelta(hours=2)
        if end_time_obj - start_time_obj > max_duration:
            flash('Booking duration cannot exceed 2 hours.')
            return redirect(url_for('book', room_id=room_id))

        # 冲突检测：检查同一房间、同一天是否已有重叠预约
        for existing in bookings:
            if (
                existing['room_id'] == room_id and
                existing['booking_date'] == booking_date and
                not (end_time_obj <= datetime.strptime(existing['start_time'], "%H:%M") or 
                     start_time_obj >= datetime.strptime(existing['end_time'], "%H:%M"))
            ):
                flash('This room is already booked for the selected time slot. Please choose a different time.')
                return redirect(url_for('book', room_id=room_id))

        # 存储预约信息
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
