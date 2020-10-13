# Used to parse websockets data
import json

# Webserver code
from flask import (Flask, render_template, request, jsonify)

# Flask websockets
from flask_socketio import (SocketIO, send, emit)

from threading import Timer

# Initialize app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# Inialize websockets
socketio = SocketIO(app, cors_allowed_origins='*')


def roll_call():
    global roll_users
    global users
    roll_users = []
    print("Calling roll...")
    socketio.send({"type": "roll_call"}, broadcast=True)
    t = Timer(5, update_users_from_roll)
    t.start()


def update_users_from_roll():
    global users
    global roll_users
    users = roll_users
    found_host = False
    for user in users:
        if user["role"] == "host":
            found_host = True
    if found_host == False:
        users = []
        chat_history = []
        socketio.send({"type": "host_left"}, broadcast=True)
    else:
        socketio.send({"type": "user_data", "data": users}, broadcast=True)


# users will store an array of information about each user - their username and their role as a host or a guest
# chat-history will store the chat history to send to a new user when they join
users = []
chat_history = []
roll_users = []


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video-player')
def videojs_websockets_combined():
    return render_template("video-player.html")


# This is called when the client pings the server to find out if there is already a host
# (if there isn't one, it will auto-select the "Host" button
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
    elif message["type"] == "roll_response":
        roll_users.append({"role": message["role"], "username": message["name"]})


@socketio.on('connect')
def test_connect():
    send({"type": "connection_status", "value": True})


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')
    roll_call()


if __name__ == '__main__':
    # socketio.run(app)
    socketio.run(app, host='play.dti.illinois.edu', port=443)
