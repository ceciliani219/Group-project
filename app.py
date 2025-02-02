from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# 模拟的房间数据（实际项目中可从数据库读取）
rooms = [
    {'id': 1, 'name': 'Breakout Room A', 'capacity': 4},
    {'id': 2, 'name': 'Breakout Room B', 'capacity': 6},
    {'id': 3, 'name': 'Breakout Room C', 'capacity': 8},
]

# 用于存储预约信息（仅在内存中，服务器重启后数据会丢失）
bookings = []

@app.route("/")
def index():
    """
    主页，显示所有可预约的 Breakout Room。
    """
    return render_template("index.html", rooms=rooms)

@app.route("/book/<int:room_id>", methods=["GET", "POST"])
def book(room_id):
    """
    预约页面，用户可以为指定的房间填写预约信息。
    """
    # 根据 room_id 查找房间
    room = next((room for room in rooms if room["id"] == room_id), None)
    if room is None:
        return "Room not found", 404

    if request.method == "POST":
        # 获取表单提交的数据
        user_name = request.form.get("user_name")
        booking_date = request.form.get("booking_date")
        booking_time = request.form.get("booking_time")

        # 构造一个预约记录（实际中需要检查预约是否冲突等）
        booking = {
            "room_id": room_id,
            "room_name": room["name"],
            "user_name": user_name,
            "booking_date": booking_date,
            "booking_time": booking_time
        }
        bookings.append(booking)
        return render_template("booking_result.html", booking=booking)

    return render_template("book.html", room=room)

@app.route("/bookings")
def list_bookings():
    """
    显示所有预约记录（仅供演示）。
    """
    return render_template("bookings.html", bookings=bookings)

if __name__ == "__main__":
    app.run(debug=True)
