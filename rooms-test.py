from flask import (
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
    Flask
)
from flask_socketio import (
    SocketIO,
    send,
    emit,
    disconnect,
    join_room,
    leave_room
)
import json

app = Flask(__name__)
sio = SocketIO(app, cors_allowed_origins='*')


@app.route('/')
def index():
    return render_template("rooms-test.html")


@sio.on('connect')
def sio_connect():
    print("Websockets user connected")
    print("Query data is: " + request.args.get("room"))
    join_room(request.args.get("room"))


@sio.on('disconnect')
def sio_disconnect():
    print("Websockets user disconnected")


@sio.on('message')
def sio_message(message):
    print("Received message: " + json.dumps(message))


if __name__ == '__main__':
    sio.run(app, debug=True)