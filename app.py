import json
from flask import (Flask, render_template, request, jsonify)
from flask_socketio import (SocketIO, send, emit)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='http://127.0.0.1:5000')

users = []
chat_history = []

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video-player')
def videojs_websockets_combined():
    return render_template("video-player.html")


@app.route('/current-host-check')
def current_host_check():
    host_exists = False
    for user in users:
        if user["role"] == "host":
            host_exists = True
    if host_exists:
        return "true"
    else:
        return "false"


@socketio.on('message')
def handle_message(message):
    global users
    global chat_history

    print('Received message: ' + str(message))
    if message["type"] == "join" and message["role"] == "guest":
        print("Recieved join request")
        if len(message["name"]) > 20:
            send({"type": "join_request_response", "value": False, "reason": "username_too_long"})
        elif "<" in message["name"] or ">" in message["name"]:
            send({"type": "join_request_response", "value": False, "reason": "username_special_characters"})
        elif message["name"] == "":
            send({"type": "join_request_response", "value": False, "reason": "username_blank"})
        else:
            success_joining = True
            for user in users:
                if user["username"] == message["name"]:
                    success_joining = False
            if success_joining == False:
                send({"type": "join_request_response", "value": False, "reason": "username_not_unique"})
            else:
                success_joining = False
                for user in users:
                    if user["role"] == "host":
                        success_joining = True
                if success_joining == False:
                    send({"type": "join_request_response", "value": False, "reason": "no_host"})
                else:
                    send({"type": "join_request_response", "value": True})
                    send({"type": "chat_history", "data": chat_history})
                    send({"type": "guest_joined", "name": message["name"]}, broadcast=True)
                    users.append({"role": "guest", "username": message["name"]})
                    send({"type": "user_data", "data": users}, broadcast=True)
    elif message["type"] == "join" and message["role"] == "host":
        success_joining = True
        for user in users:
            if user["role"] == "host":
                success_joining = False
        if success_joining == False:
            send({"type": "host_request_response", "value": False, "reason": "host_already_exists"})
        else:
            success_joining = True
            for user in users:
                if user["username"] == message["name"]:
                    success_joining = False
            if success_joining == False:
                send({"type": "host_request_response", "value": False, "reason": "username_not_unique"})
            else:
                send({"type": "host_request_response", "value": True})
                users.append({"role": "host", "username": message["name"]})
                send({"type": "user_data", "data": users}, broadcast=True)
    elif message["type"] == "leave" and message["role"] == "guest":
        for i in range(len(users)):
            if users[i]["username"] == message["name"]:
                del users[i]
        send({"type": "user_data", "data": users}, broadcast=True)
    elif message["type"] == "leave" and message["role"] == "host":
        users = []
        chat_history = []
        send({"type": "host_left"}, broadcast=True)
    elif message["type"] == "host_data":
        send({"type": "player_data", "data": message["data"]}, broadcast=True)
    elif message["type"] == "guest_data":
        send({"type": "guest_data", "action": message["action"], "timestamp": message["timestamp"]}, broadcast=True)
    elif message["type"] == "kick_user":
        send(message, broadcast=True)
    elif message["type"] == "chat":
        chat_history.append(message)
        send(message, broadcast=True)


@socketio.on('connect')
def test_connect():
    send({"type": "connection_status", "value": True})


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app)
