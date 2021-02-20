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
def log(message, webRequest = None):
    global users

    if (webRequest is None):
        log_string = "[" + datetime.datetime.now().strftime("%H:%M:%S") + "]: " + message + "\n"
    else:
        ip_string = ""
        sid_string = ""
        username_string = "]: "

        try:
            if (webRequest.remote_addr is not None):
                ip_string = "[" + webRequest.remote_addr
            if (webRequest.sid is not None):
                sid_string = ", " + webRequest.sid + ""
                username_string = ", " + users[webRequest.sid]["username"] + "]: "
        except:
            pass

        log_string = "[" + datetime.datetime.now().strftime(
            "%H:%M:%S") + "] " + ip_string + sid_string + username_string + message + "\n"
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
    return render_template("video-join-page.html")


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


# Takes a webRequest object and checks if the SID of the sender matches the SID of the session host
# If yes, returns true. If no, returns false and makes a report of the infraction in the log file
def CheckIfHost(webRequest, message):
    if (webRequest.sid == host_sid):
        return True
    else:
        log("Received the following request: " + message + "\n\tDenying request because user falsely claimed to be the host.", request)
        return False


# Validates the username for special characters, length, and more
# Returns true/false and logs the reason why requests were denied
def ValidateUsername(username, role):
    logMessage = "Received " + role + " request with requested username '" + username + "'. "

    # Verify username is not greater than 20 characters
    if (len(username) > 20):
        log(logMessage + "Denied for reason: username too long", request)
        return { "value": False, "reason": "username_too_long" }

    # Check if username contains disallowed characters
    elif ("<" in username or ">" in username or "(" in username or ")" in username):
        log(logMessage + "Denied for reason: username contained special characters that are not allowed", request)
        return { "value": False, "reason": "username_special_characters" }

    # Check if username is blank
    elif (username == ""):
        log(logMessage + "Denied for reason: username was blank", request)
        return { "value": False, "reason": "username_blank" }

    # Check if username was already taken
    else:
        success_joining = True
        if (not changing_host):
            for user in users:
                if users[user]["username"] == username:
                    success_joining = False

        if (not success_joining):
            log(logMessage + "Denied for reason: username was already taken", request)
            return { "value": False, "reason": "username_not_unique" }
        else:
            log(logMessage + "Request approved.", request)
            return { "value": True }


# region Websockets Message Handler
@sio.on('message')
def handle_message(message):
    global users
    global host_sid
    global chat_history
    global url
    global changing_host

    # region Guest Join Requests
    if message["type"] == "join" and message["role"] == "guest":
        if (host_sid == "" and not changing_host):
            send({"type": "guest_request_response", "value": False, "reason": "no_host"})
            log("Received join request with requested username '" + message["name"] + "'. Denied for reason: there is not a host in this session", request)

        # Validate username
        else:
            usernameValidation = ValidateUsername(message["name"], "guest")

            if (usernameValidation["value"] == True):
                # Alert the user of the success
                send({"type": "guest_request_response", "value": True})

                # Send the user the previous chat history
                send({"type": "chat_history", "data": chat_history})

                # Send the user the video URL
                send({"type": "change_video_url", "url": url})

                # Alert the host that a new guest has joined - the host will send the current video state to the guest
                send({"type": "guest_joined", "name": message["name"]}, broadcast=True)

                # Set user data for this new guest
                users[request.sid] = {"role": "guest", "username": message["name"]}

                # Send the current user data to all clients
                send({"type": "user_data", "data": users}, broadcast=True)
            else:
                send({"type": "host_request_response", "value": False, "reason": usernameValidation["reason"]})
    # endregion Join Requests

    # region Host Join Requests
    elif message["type"] == "join" and message["role"] == "host":

        # Check if there is already an existing host user
        if (host_sid != ""):
            send({"type": "host_request_response", "value": False, "reason": "host_already_exists"})
            log("Received host request with requested username '" + message["name"] + "'. Denied for reason: there is already a host in this session", request)
        # Validate username
        else:
            usernameValidation = ValidateUsername(message["name"], "host")
            if (usernameValidation["value"] == True):
                # Alert the user of the success
                send({"type": "host_request_response", "value": True})

                # Save the host's SID
                host_sid = request.sid

                # Set user data for this new host
                users[request.sid] = {"role": "host", "username": message["name"]}

                # Save the video URL
                url = message["url"]

                # Send the host the current user data
                send({"type": "user_data", "data": users}, broadcast=True)

                # Send the host the video URL
                send({"type": "change_video_url", "url": url}, broadcast=True)

                # End the 'changing host' state (if applicable)
                changing_host = False
            else:
                send({"type": "host_request_response", "value": False, "reason": usernameValidation["reason"]})
    # endregion

    # region Host Video Data
    elif message["type"] == "host_data":
        if (CheckIfHost(request, message)):
            send({"type": "player_data", "data": message["data"]}, broadcast=True)
            log("Received host video data.", request)
    # endregion

    # region Guest Video Data
    elif message["type"] == "guest_data":
        send({"type": "guest_data", "action": message["action"], "timestamp": message["timestamp"]}, broadcast=True)
        log("Received guest video data.", request)
    # endregion

    # region User Kick Requests
    elif message["type"] == "kick_user":
        if (CheckIfHost(request, message)):
            send({"type": "kick_user", "user": message["user"]}, broadcast=True)
            log("The host kicked user: " + message["user"], request)
    # endregion

    # region Promotion Requests
    elif message["type"] == "promote_user":
        if (CheckIfHost(request, message)):
            changing_host = True

            send({"type": "promote_user", "user": message["user"], "video_state": message["video_state"]}, broadcast=True)
            log("Promoted user " + message["user"] + " to host", request)

            del users[host_sid]
            host_sid = ""

            send({"type": "user_data", "data": users}, broadcast=True)
    # endregion

    # region Changing Video URL
    elif message["type"] == "change_video_url":
        if (CheckIfHost(request, message)):
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
        if (CheckIfHost(request, message)):
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


# Run app
if __name__ == '__main__':
    # sio.run(app, host='play.dti.illinois.edu', port=443)
    log("Initializing app...")
    sio.run(app, debug=True)
