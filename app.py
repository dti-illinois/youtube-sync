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
from flask_socketio import (SocketIO, send, emit, disconnect)

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

# region Shibboleth
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
# endregion


def ValidateSessionID(sessionID):
    # TODO: proper validation
    return (len(sessionID) == 5)


@app.route('/')
def index():
    if current_user.is_authenticated:
        user = current_user.id
        log("Sending rendered page '/'", request)
        return render_template("index.html")
    else:
        return redirect(url_for("login"))


@app.route('/play/<session_id>')
def video(session_id):
    if current_user.is_authenticated:
        user = current_user.id
        log("Sending rendered page '/play/" + session_id + "'", request)
        if (ValidateSessionID(session_id) == True):
            return render_template("index.html", sessionID=session_id)
        else:
            return render_template("index.html")
    else:
        return redirect(url_for("login"))
 

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(app.config["ISSUER_URL"] + "/idp/profile/Logout")


@sio.on('connect')
def WebSocketsConnect():
    log("WebSockets client connected.", request)
    send({"type": "connection_status", "value": True})


@sio.on('disconnect')
def WebSocketsDisconnect():
    log("WebSockets client disconnected.", request)


# Run app
if __name__ == '__main__':
    log("Initializing app...")
    sio.run(app, debug=True, use_reloader=False)
