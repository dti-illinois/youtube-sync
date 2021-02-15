# region Imports
# Used for logging
import datetime
import os

# Webserver code
from flask import (Flask, render_template, request)

# Flask websockets
from flask_socketio import (SocketIO, send, emit)
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

changing_host = False

if not os.path.exists('logs'):
    os.makedirs('logs')

# The log file name
LOG_FILE_NAME = datetime.datetime.now().strftime("./logs/log_%G%m%d_%H%M%S.log")
# endregion


# Logs data to the console and the log file
def log(message, webRequest):
    global users

    ip_string = ""
    sid_string = ""
    username_string = "]: "

    try:
        if (webRequest is not None):
            if (webRequest.remote_addr is not None):
                ip_string = "[" + webRequest.remote_addr
            if (webRequest.sid is not None):
                sid_string = ", " + webRequest.sid + ""
                if (users[webRequest.sid]["username"] is not "" and users[webRequest]["username"] is not None):
                    username_string = ", " + users[webRequest.sid]["username"] + "]: "
    except:
        pass

    log_string = "[" + datetime.datetime.now().strftime("%H:%M:%S") + "] " + ip_string + sid_string + username_string + message + "\n"
    print(log_string)
    with open(LOG_FILE_NAME, 'a') as log_file:
        log_file.write(log_string)


# Resets all data to the original state
def reset():
    global users
    global host_sid
    global chat_history
    global roll_users
    global url

    users = {}
    host_sid = ""
    chat_history = []
    roll_users = []
    url = ""


@app.route('/')
def index():
    log("Sending rendered page '/'", request)
    return render_template('index.html')


@app.route('/video-join-page')
def video_join_page():
    log("Sending rendered page '/video-join-page'", request)
    return render_template("video-join-page.html")


@app.route('/video-player')
def video_player():
    log("Sending rendered page '/video-player'", request)
    return render_template("video-player.html")


# This is called when the client pings the server to find out if there is already a host
# If there isn't one, the client will auto-select the "Host" button
@app.route('/current-host-check')
def current_host_check():
    log("Sending non-rendered page '/current-host-check'", request)
    host_exists = False
    for sid in users:
        if users[sid]["role"] == "host":
            host_exists = True
    if host_exists:
        return "true"
    else:
        return "false"


def CheckIfHost(webRequest):
    if (webRequest.sid == host_sid):
        return True
    else:
        log("Denying request because user falsely claimed to be the host.", request)
        return False


# region Websockets Message Handler
@sio.on('message')
def handle_message(message):
    global users
    global host_sid
    global chat_history
    global url
    global changing_host

    ip = request.remote_addr

    # Log
    log("Received message: " + str(message), request)

    # region Guest Join Requests
    if message["type"] == "join" and message["role"] == "guest":
        log("Received join request from username " + message["name"] + "with IP address " + ip, request)
        if (len(message["name"]) > 20):
            send({"type": "join_request_response", "value": False, "reason": "username_too_long"})
            log("Denied join request: username too long", request)
        elif ("<" in message["name"] or ">" in message["name"] or "(" in message["name"] or ")" in message["name"]):
            send({"type": "join_request_response", "value": False, "reason": "username_special_characters"})
            log("Denied join request: username contained special characters that are not allowed", request)
        elif (message["name"] == ""):
            send({"type": "join_request_response", "value": False, "reason": "username_blank"})
            log("Denied join request: username was blank", request)
        else:
            success_joining = True
            for user in users:
                if users[user]["username"] == message["name"]:
                    success_joining = False

            if (changing_host):
                success_joining = True

            if (not success_joining):
                send({"type": "join_request_response", "value": False, "reason": "username_not_unique"})
                log("Denied join request: username was already taken", request)
            else:
                success_joining = False
                for user in users:
                    if users[user]["role"] == "host":
                        success_joining = True

                if changing_host == True:
                    success_joining = True

                if success_joining == False:
                    send({"type": "join_request_response", "value": False, "reason": "no_host"})
                    log("Denied join request: there is not a host in this session", request)
                else:
                    send({"type": "join_request_response", "value": True})
                    send({"type": "chat_history", "data": chat_history})
                    send({"type": "change_video_url", "url": url})
                    send({"type": "guest_joined", "name": message["name"]}, broadcast=True)
                    users[request.sid] = {"role": "guest", "username": message["name"]}
                    send({"type": "user_data", "data": users}, broadcast=True)
                    log("Approved join request from username " + message["name"], request)
    # endregion Join Requests

    # region Host Join Requests
    elif message["type"] == "join" and message["role"] == "host":
        log("Received host request from username " + message["name"], request)

        host_exists = True
        if host_sid == "":
            host_exists = False

        if host_exists:
            send({"type": "host_request_response", "value": False, "reason": "host_already_exists"})
            log("Denied host request: there is already a host in this session", request)
        elif "<" in message["name"] or ">" in message["name"] or "(" in message["name"] or ")" in message["name"]:
            send({"type": "host_request_response", "value": False, "reason": "username_special_characters"})
            log("Denied host request: username contained disallowed special characters", request)
        elif len(message["name"]) > 20:
            send({"type": "host_request_response", "value": False, "reason": "username_too_long"})
            log("Denied host request: username too long", request)
        else:
            success_joining = True
            for user in users:
                if users[user]["username"] == message["name"]:
                    success_joining = False

            if (changing_host):
                success_joining = True

            if (not success_joining):
                send({"type": "host_request_response", "value": False, "reason": "username_not_unique"})
                log("Denied host request: username was not unique", request)
            else:
                host_sid = request.sid
                send({"type": "host_request_response", "value": True})
                users[request.sid] = {"role": "host", "username": message["name"]}
                url = message["url"]
                send({"type": "user_data", "data": users}, broadcast=True)
                send({"type": "change_video_url", "url": url}, broadcast=True)
                log("Approved host request from username " + message["name"], request)
                changing_host = False
    # endregion

    # region Host Video Data
    elif message["type"] == "host_data":
        if (CheckIfHost(request)):
            send({"type": "player_data", "data": message["data"]}, broadcast=True)
    # endregion

    # region Guest Video Data
    elif message["type"] == "guest_data":
        send({"type": "guest_data", "action": message["action"], "timestamp": message["timestamp"]}, broadcast=True)
    # endregion

    # region User Kick Requests
    elif message["type"] == "kick_user":
        if (CheckIfHost(request)):
            send({"type": "kick_user", "user": message["user"]}, broadcast=True)
            log("Kicked user " + message["user"], request)
    # endregion

    # region Promotion Requests
    elif message["type"] == "promote_user":
        if (CheckIfHost(request)):
            changing_host = True

            send({"type": "promote_user", "user": message["user"], "video_state": message["video_state"]}, broadcast=True)
            log("Promoted user " + message["user"] + " to host", request)

            del users[host_sid]
            host_sid = ""

            send({"type": "user_data", "data": users}, broadcast=True)
    # endregion

    # region Changing Video URL
    elif message["type"] == "change_video_url":
        if (CheckIfHost(request)):
            url = message["url"]
            send({"type": "change_video_url", "url": url}, broadcast=True)
            log("Changed video URL to " + message["url"], request)
    # endregion

    # region Chat Messages
    elif message["type"] == "chat":
        chat_history.append(message)
        send(message, broadcast=True)
        log("Received chat message: " + message["message"], request)
    # endregion

    # region Chat Message Removal
    elif message["type"] == "remove_chat_message":
        if (CheckIfHost(request)):
            send({"type": "remove_chat_message", "message_index": message["message_index"]}, broadcast=True)
            chat_history.pop(message["message_index"])
            log("Host removed chat message: " + message["message_content"], request)
    # endregion
# endregion


@sio.on('connect')
def connection():
    log("WebSockets client connected.", request)
    users[request.sid] = {"username": "", "role": ""}
    send({"type": "connection_status", "value": True})


@sio.on('disconnect')
def disconnection():
    log("WebSockets client disconnected.", request)

    if users[request.sid]["role"] == "host":
        if not changing_host:
            reset()
            send({"type": "host_left"}, broadcast=True)
            log("The host left the session", request)
    else:
        log("Guest left the session", request)
        del users[request.sid]
        send({"type": "user_data", "data": users}, broadcast=True)


log("Initializing app...", None)


# Run app
if __name__ == '__main__':
    # sio.run(app, host='play.dti.illinois.edu', port=443)
    sio.run(app, debug=True)
