# region Imports
# Used to parse response data
import json

# Used to generate secret key
import random
import string

# Used for logging
import datetime
import os

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
sio = SocketIO(app, cors_allowed_origins='*')
# endregion

# region Define variables
# Stores a dictionary of information about each user - their username and their role as a host or a guest
users = {}
host_sid = ""

# Stores the chat history to send to a new user when they join
chat_history = []

# Used when calling roll to keep track of user responses
roll_users = []

# The URL of the YouTube video
url = ""

# The secret key to be shared with the host
secret_key = ""

changing_host = False

if not os.path.exists('logs'):
    os.makedirs('logs')

# The log file name
LOG_FILE_NAME = datetime.datetime.now().strftime("./logs/log_%G%m%d_%H%M%S.log")
# endregion


# Logs data to the console and the log file
def log(message):
    log_string = '[' + datetime.datetime.now().strftime("%H:%M:%S") + ']: ' + message + "\n"
    print(log_string)
    with open(LOG_FILE_NAME, 'a') as log_file:
        log_file.write(log_string)


# Resets all data to the original state
def reset():
    global users
    global chat_history
    global roll_users
    global url
    global secret_key
    users = {}
    chat_history = []
    roll_users = []
    url = ""
    secret_key = ""


@app.route('/')
def index():
    log("Sending rendered page '/' to user with IP " + request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
    return render_template('index.html')


@app.route('/video-join-page')
def video_join_page():
    log("Sending rendered page '/video-join-page' to user with IP " + request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
    return render_template("video-join-page.html")


@app.route('/video-player')
def video_player():
    log("Sending rendered page '/video-player' to user with IP " + request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
    return render_template("video-player.html")


# This is called when the client pings the server to find out if there is already a host
# If there isn't one, the client will auto-select the "Host" button
@app.route('/current-host-check')
def current_host_check():
    log("Sending non-rendered page '/current-host-check' to user with IP " + request.environ.get('HTTP_X_REAL_IP', request.remote_addr))
    host_exists = False
    for user in users:
        if user["role"] == "host":
            host_exists = True
    if host_exists:
        return "true"
    else:
        return "false"


# region Websockets Message Handler
@sio.on('message')
def handle_message(message):
    global users
    global host_sid
    global chat_history
    global secret_key
    global url
    global changing_host

    ip = request.remote_addr

    # Log
    log('Received message from user with IP address ' + ip + ": " + str(message) + " and SID " + request.sid)

    # region Guest Join Requests
    if message["type"] == "join" and message["role"] == "guest":
        log("Received join request from username " + message["name"] + "with IP address " + ip)
        if len(message["name"]) > 20:
            send({"type": "join_request_response", "value": False, "reason": "username_too_long"})
            log("Denied join request: username too long")
        elif "<" in message["name"] or ">" in message["name"] or "(" in message["name"] or ")" in message["name"]:
            send({"type": "join_request_response", "value": False, "reason": "username_special_characters"})
            log("Denied join request: username contained special characters that are not allowed")
        elif message["name"] == "":
            send({"type": "join_request_response", "value": False, "reason": "username_blank"})
            log("Denied join request: username was blank")
        else:
            success_joining = True
            for user in users:
                if users[user]["username"] == message["name"]:
                    success_joining = False

            if changing_host == True:
                success_joining = True

            if success_joining == False:
                send({"type": "join_request_response", "value": False, "reason": "username_not_unique"})
                log("Denied join request: username was already taken")
            else:
                success_joining = False
                for user in users:
                    if users[user]["role"] == "host":
                        success_joining = True

                if changing_host == True:
                    success_joining = True

                if success_joining == False:
                    send({"type": "join_request_response", "value": False, "reason": "no_host"})
                    log("Denied join request: there is not a host in this session")
                else:
                    send({"type": "join_request_response", "value": True})
                    send({"type": "chat_history", "data": chat_history})
                    send({"type": "change_video_url", "url": url})
                    send({"type": "guest_joined", "name": message["name"]}, broadcast=True)
                    users[request.sid] = {"role": "guest", "username": message["name"]}
                    send({"type": "user_data", "data": users}, broadcast=True)
                    log("Approved join request from username " + message["name"])
    # endregion Join Requests

    # region Host Join Requests
    elif message["type"] == "join" and message["role"] == "host":
        log("Received host request from username " + message["name"])

        host_exists = True
        if host_sid == "":
            host_exists = False

        if host_exists:
            send({"type": "host_request_response", "value": False, "reason": "host_already_exists"})
            log("Denied host request: there is already a host in this session")
        elif "<" in message["name"] or ">" in message["name"] or "(" in message["name"] or ")" in message["name"]:
            send({"type": "host_request_response", "value": False, "reason": "username_special_characters"})
            log("Denied host request: username contained disallowed special characters")
        elif len(message["name"]) > 20:
            send({"type": "host_request_response", "value": False, "reason": "username_too_long"})
            log("Denied host request: username too long")
        else:
            success_joining = True
            for user in users:
                if users[user]["username"] == message["name"]:
                    success_joining = False

            if changing_host == True:
                success_joining = True

            if success_joining == False:
                send({"type": "host_request_response", "value": False, "reason": "username_not_unique"})
                log("Denied host request: username was not unique")
            else:
                secret_key = ''.join((random.choice(string.ascii_letters + string.digits) for i in range(25)))
                host_sid = request.sid
                send({"type": "host_request_response", "value": True, "secret_key": secret_key})
                users[request.sid] = {"role": "host", "username": message["name"]}
                url = message["url"]
                send({"type": "user_data", "data": users}, broadcast=True)
                send({"type": "change_video_url", "url": url}, broadcast=True)
                log("Approved host request from username " + message["name"])
                changing_host = False
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
            log("Kicked user " + message["user"])
    # endregion

    # region Promotion Requests
    elif message["type"] == "promote_user":
        if message["secret_key"] == secret_key:
            changing_host = True

            send({"type": "promote_user", "user": message["user"], "video_state": message["video_state"]}, broadcast=True)
            log("Promoted user " + message["user"] + " to host")

            for i in range(len(users)):
                if users[i]["username"] == message["host_username"]:
                    del users[i]
            send({"type": "user_data", "data": users}, broadcast=True)
    # endregion

    # region Changing Video URL
    elif message["type"] == "change_video_url":
        if message["secret_key"] == secret_key:
            url = message["url"]
            send({"type": "change_video_url", "url": url}, broadcast=True)
            log("Changed video URL to " + message["url"])
    # endregion

    # region Chat Messages
    elif message["type"] == "chat":
        chat_history.append(message)
        send(message, broadcast=True)
        log("Received chat message from username "+message["username"]+" and IP address "+ip+": "+message["message"])
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
            log("Host removed chat message with content: " + message["message_content"])
    # endregion
# endregion


@sio.on('connect')
def connection():
    log("WebSockets client with SID " + request.sid + " connected.")
    users[request.sid] = {"username": "", "role": ""}
    send({"type": "connection_status", "value": True})


@sio.on('disconnect')
def disconnection():
    log("WebSockets client with SID " + request.sid + " disconnected.")

    if (users[request.sid]["role"] == "host"):
        reset()
        send({"type": "host_left"}, broadcast=True)
        log("The host left the session")
    else:
        log("Guest with username " + users[request.sid]["username"] + "and SID " + request.sid + " left the session")
        del users[request.sid]
        send({"type": "user_data", "data": users}, broadcast=True)


log("Initializing app...")


# Run app
if __name__ == '__main__':
    # sio.run(app, host='play.dti.illinois.edu', port=443)
    sio.run(app, debug=True)
