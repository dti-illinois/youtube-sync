# region Imports
# Webserver code
from flask import (
    jsonify,
    redirect, 
    render_template, 
    request, 
    session,
    url_for,
    Flask 
)

# Flask websockets
from flask_socketio import (SocketIO, send, emit)

# Shibboleth OIDC login
from oic import rndstr
from oic.oic import Client
from oic.oic.message import (
    AuthorizationResponse, 
    ClaimsRequest, 
    Claims,
    RegistrationResponse
)
from oic.utils.authn.client import CLIENT_AUTHN_METHOD
from oic.utils.http_util import Redirect
from flask_login import (
    current_user,
    login_user,
    login_required,
    logout_user,
    LoginManager
)
from user import User

from logger import log
from validation import ValidateUsername

import json
# endregion

# region Initialization
# Initialize app
app = Flask(__name__)

# OIDC setting
app.config.from_pyfile('config.py', silent=True)

# set secret key for session
app.secret_key = app.config["SESSION_SECRET"]

# create oidc client
client = Client(client_authn_method=CLIENT_AUTHN_METHOD)

# get authentication provider details by hitting the issuer URL
provider_info = client.provider_config(app.config["ISSUER_URL"])

# store registration details
info = {
     "client_id": app.config["CLIENT_ID"],
     "client_secret": app.config["CLIENT_SECRET"],
     "redirect_uris": app.config["REDIRECT_URIS"]
}
client_reg = RegistrationResponse(**info)
client.store_registration_info(client_reg)
client.redirect_uris = app.config["REDIRECT_URIS"]

# LOGIN management setting
login_manager = LoginManager()
login_manager.init_app(app)

# Initialize websockets
sio = SocketIO(app, cors_allowed_origins='*')
# endregion

# region Define variables
# Stores a dictionary of information about each user - their username and their role as a host or a guest
users = {}

# The SID of the host user
host_sid = ""

# Stores the chat history to send to a new user when they join
chat_history = []

# The URL of the YouTube video
url = ""

changing_host = False

HOST_ROLE = 0
GUEST_ROLE = 1
# endregion


@login_manager.user_loader
def load_user(netid):
    return User.get(netid)


@app.route('/login')
def login():
    session['state'] = rndstr()
    session['nonce'] = rndstr()

    # setup claim request
    claims_request = ClaimsRequest(
         userinfo = Claims(uiucedu_uin={"essential": True})
    )
    args = {
         "client_id": client.client_id,
         "response_type": "code",
         "scope": app.config["SCOPES"],
         "nonce": session["nonce"],
         "redirect_uri": app.config["REDIRECT_URIS"][0],
         "state": session["state"],
         "claims": claims_request
    }

    auth_req = client.construct_AuthorizationRequest(request_args=args)
    login_url = auth_req.request(client.authorization_endpoint)

    return Redirect(login_url)


@app.route('/callback')
def callback():
    response = request.environ["QUERY_STRING"]
    authentication_response = client.parse_response(AuthorizationResponse, info=response, sformat="urlencoded")
    code = authentication_response["code"]
    assert authentication_response["state"] == session["state"]
    args = {
         "code": code
    }
    token_response = client.do_access_token_request(state=authentication_response["state"], request_args=args,authn_method="client_secret_basic")
    user_info = client.do_user_info_request(state=authentication_response["state"])

    user = User(netid=user_info["preferred_username"])
    login_user(user)

    return redirect(url_for("index"))


# Resets all data to the original state
def Reset():
    global users
    global host_sid
    global chat_history
    global url

    users = {}
    host_sid = ""
    chat_history = []
    url = ""


@app.route('/')
def index():
    if current_user.is_authenticated:
        user = current_user.id
        log("Sending rendered page '/'", request)
        return render_template("video-join-page.html")
    else:
        return redirect(url_for("login"))
 

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(app.config["ISSUER_URL"] + "/idp/profile/Logout")


@app.route('/video-join-page')
def VideoJoinPage():
    log("Sending rendered page '/video-join-page'", request)
    return render_template("video-join-page.html")


@app.route('/video-player')
def VideoPlayer():
    log("Sending rendered page '/video-player'", request)
    return render_template("video-player.html")


# This is called when the client pings the server to find out if there is already a host
# If there isn't one, the client will auto-select the "Host" button
@app.route('/current-host-check')
def CurrentHostCheck():
    log("Sending non-rendered page '/current-host-check'", request)
    host_exists = False
    for sid in users:
        if users[sid]["role"] == HOST_ROLE:
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
        log("Received the following request: " + json.dumps(message) + "\n\tDenying request because user falsely claimed to be the host.", request)
        return False


# region Websockets Message Handler
@sio.on('message')
def HandleMessage(message):
    global users
    global host_sid
    global chat_history
    global url
    global changing_host

    # region Guest Join Requests
    if message["type"] == "join" and message["role"] == GUEST_ROLE:
        print("Received guest request...")

        if (host_sid == "" and not changing_host):
            send({"type": "guest_request_response", "value": False, "reason": "no_host"})
            log("Received join request with requested username '" + message["name"] + "'. Denied for reason: there is not a host in this session", request)

        # Validate username
        else:
            usernameValidation = ValidateUsername(message["name"], GUEST_ROLE, users, changing_host, request)

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
                users[request.sid] = {"role": GUEST_ROLE, "username": message["name"]}

                # Send the current user data to all clients
                send({"type": "user_data", "data": users}, broadcast=True)
            else:
                send({"type": "guest_request_response", "value": False, "reason": usernameValidation["reason"]})
    # endregion Join Requests

    # region Host Join Requests
    elif message["type"] == "join" and message["role"] == HOST_ROLE:
        # Check if there is already an existing host user
        if (host_sid != ""):
            send({"type": "host_request_response", "value": False, "reason": "host_already_exists"})
            log("Received host request with requested username '" + message["name"] + "'. Denied for reason: there is already a host in this session", request)
        # Validate username
        else:
            usernameValidation = ValidateUsername(message["name"], HOST_ROLE, users, changing_host, request)
            if (usernameValidation["value"] == True):
                # Alert the user of the success
                send({"type": "host_request_response", "value": True})

                # Save the host's SID
                host_sid = request.sid

                # Set user data for this new host
                users[request.sid] = {"role": HOST_ROLE, "username": message["name"]}

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
def WebSocketsConnect():
    log("WebSockets client connected.", request)
    users[request.sid] = {"username": "", "role": ""}
    send({"type": "connection_status", "value": True})


@sio.on('disconnect')
def WebSocketsDisconnect():
    log("WebSockets client disconnected.", request)

    if users[request.sid]["role"] == HOST_ROLE:
        if not changing_host:
            send({"type": "host_left"}, broadcast=True)
            log("The host left the session", request)
            Reset()
    else:
        log("Guest left the session", request)
        del users[request.sid]
        send({"type": "user_data", "data": users}, broadcast=True)


# Run app
if __name__ == '__main__':
    # sio.run(app, host='play.dti.illinois.edu', port=443)
    log("Initializing app...")
    sio.run(app, debug=True)
