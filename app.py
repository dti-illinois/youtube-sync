import json
from flask import (Flask, render_template, request, jsonify)
from flask_socketio import (SocketIO, send, emit)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='http://127.0.0.1:5000')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/guest-youtube')
def guest_youtube():
    return render_template('guest-youtube.html')


@app.route('/host-youtube')
def host_youtube():
    return render_template('host-youtube.html')


@app.route('/guest-videojs')
def guest_videojs():
    return render_template('guest-videojs.html')


@app.route('/host-videojs')
def host_videojs():
    return render_template('host-videojs.html')


@app.route('/host-processor', methods=['POST'])
def get_data():
    if request.method == 'POST':
        print("Writing data to file...")
        with open("data.json", "wb") as fo:
            fo.write(request.get_data())
        return '', 200


@app.route('/guest-processor')
def set_data():
    with open('data.json', 'r') as dataFile:
        return dataFile.read()


@app.route('/video-test')
def video_test():
    return render_template("video-test.html")


@app.route('/videojs-freemode')
def videojs_freemode():
    return render_template("videojs-freemode.html")


@app.route('/websockets-test')
def websockets_test():
    return render_template("websockets-test.html")


@socketio.on('message')
def handle_message(message):
    print('Received message: ' + str(message))


@socketio.on('connect')
def test_connect():
    send({"type": "connection_status", "value": True})


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app)
