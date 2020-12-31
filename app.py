# region Imports
# Used to parse response data
import json

# Used to generate secret key
import random
import string

# Webserver code
from flask import (Flask, render_template, request, jsonify)

# Flask websockets
from flask_socketio import (SocketIO, send, emit)

# Used to time roll-call responses
from threading import Timer
# endregion

# region Initialization
# Initialize app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

# Initialize websockets
socketio = SocketIO(app, cors_allowed_origins='*')
# endregion

# region Define variables
# Stores an array of information about each user - their username and their role as a host or a guest
users = []

# Stores the chat history to send to a new user when they join
chat_history = []

# Used when calling roll to keep track of user responses
roll_users = []

# The URL of the YouTube video
url = ""

# The secret key to be shared with the host
secret_key = ""
#endregion


# region Roll Call
# Called when a client disconnects
def roll_call():
    global roll_users
    global users

    # Clear roll_users
    roll_users = []

    # Log
    print("Calling roll...")

    # Sends a message to the clients requesting a roll response
    socketio.send({"type": "roll_call"}, broadcast=True)

    # Wait 10 seconds
    t = Timer(10, update_users_from_roll)
    t.start()


# Called 10 seconds after client disconnection
def update_users_from_roll():
    global users
    global roll_users
    global secret_key

    found_host = False

    # Iterates over all user responses and looks for a host
    for user in roll_users:
        if user["role"] == "host":
            found_host = True

    # If no host, reset and send message to clients
    if not found_host:
        reset()
        socketio.send({"type": "host_left"}, broadcast=True)

    # If there was a host, send updated user data to clients
    else:
        socketio.send({"type": "user_data", "data": users}, broadcast=True)
# endregion


# Resets all data to the original state
def reset():
    global users
    global chat_history
    global roll_users
    global url
    global secret_key
    users = []
    chat_history = []
    roll_users = []
    url = ""
    secret_key = ""


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video-join-page')
def video_join_page():
    return render_template("video-join-page.html")


@app.route('/video-player')
def videojs_websockets_combined():
    return render_template("video-player.html")


# This is called when the client pings the server to find out if there is already a host
# If there isn't one, the client will auto-select the "Host" button
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


# region Websockets Message Handler
@socketio.on('message')
def handle_message(message):
    global users
    global chat_history
    global secret_key
    global url

    # Log
    print('Received message: ' + str(message))

    # region Guest Join Requests
    if message["type"] == "join" and message["role"] == "guest":
        print("Recieved join request")
        if len(message["name"]) > 20:
            send({"type": "join_request_response", "value": False, "reason": "username_too_long"})
        elif "<" in message["name"] or ">" in message["name"] or "(" in message["name"] or ")" in message["name"]:
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
                    send({"type": "change_video_url", "url": url})
                    send({"type": "guest_joined", "name": message["name"]}, broadcast=True)
                    users.append({"role": "guest", "username": message["name"]})
                    send({"type": "user_data", "data": users}, broadcast=True)
    # endregion Join Requests

    # region Host Join Requests
    elif message["type"] == "join" and message["role"] == "host":
        host_exists = True
        for user in users:
            if user["role"] == "host":
                host_exists = False
        if host_exists == False:
            send({"type": "host_request_response", "value": False, "reason": "host_already_exists"})
        elif "<" in message["name"] or ">" in message["name"] or "(" in message["name"] or ")" in message["name"]:
            send({"type": "host_request_response", "value": False, "reason": "username_special_characters"})
        elif len(message["name"]) > 20:
            send({"type": "host_request_response", "value": False, "reason": "username_too_long"})
        else:
            success_joining = True
            for user in users:
                if user["username"] == message["name"]:
                    success_joining = False
            if success_joining == False:
                send({"type": "host_request_response", "value": False, "reason": "username_not_unique"})
            else:
                secret_key = ''.join((random.choice(string.ascii_letters + string.digits) for i in range(25)))
                send({"type": "host_request_response", "value": True, "secret_key": secret_key})
                users.append({"role": "host", "username": message["name"]})
                url = message["url"]
                send({"type": "user_data", "data": users}, broadcast=True)
                send({"type": "change_video_url", "url": url}, broadcast=True)
    # endregion

    # region Guest Leaving
    elif message["type"] == "leave" and message["role"] == "guest":
        for i in range(len(users)):
            if users[i]["username"] == message["name"]:
                del users[i]
        send({"type": "user_data", "data": users}, broadcast=True)
    # endregion

    # region Host Leaving
    elif message["type"] == "leave" and message["role"] == "host":
        reset()
        send({"type": "host_left"}, broadcast=True)
    # endregion

    # region Host Video Data
    elif message["type"] == "host_data":
        if (message["secret_key"] == secret_key):
            send({"type": "player_data", "data": message["data"]}, broadcast=True)
    # endregion

    # region Guest Video Data
    elif message["type"] == "guest_data":
        send({"type": "guest_data", "action": message["action"], "timestamp": message["timestamp"]}, broadcast=True)
    # endregion

    # region User Kick Requests
    elif message["type"] == "kick_user":
        if message["secret_key"] == secret_key:
            send({"type": "kick_user", "user": message["user"]}, broadcast=True)
    # endregion

    # region Changing Video URL
    elif message["type"] == "change_video_url":
        if message["secret_key"] == secret_key:
            url = message["url"]
            send({"type": "change_video_url", "url": url}, broadcast=True)
    # endregion

    # region Chat Messages
    elif message["type"] == "chat":
        chat_history.append(message)
        send(message, broadcast=True)
    # endregion

    # region Roll Call Responses
    elif message["type"] == "roll_response":
        roll_users.append({"role": message["role"], "username": message["name"]})
    # endregion

    # region Chat Message Removal
    elif message["type"] == "remove_chat_message":
        if message["secret_key"] == secret_key:
            send({"type": "remove_chat_message", "message_index": message["message_index"]}, broadcast=True)
            chat_history.pop(message["message_index"])
    # endregion
# endregion

@socketio.on('connect')
def connection():
    send({"type": "connection_status", "value": True})


@socketio.on('disconnect')
def disconnection():
    print('Client disconnected')
    roll_call()


# Run app
if __name__ == '__main__':
    socketio.run(app, host='play.dti.illinois.edu', port=443)
