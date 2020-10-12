//#region Creating variables
    // Role of the user.
    // 0 = host, 1 = guest
    var role = 1;

    // username = the user's username
    // myVideo = the video player object
    // socket = the websocket object
    // updatingPlayer - used to prevent infinite loops
    var username, myVideo, socket, updatingPlayer;
//#endregion

// Reports disconnection to the server before the tab is fully closed
function ReportDisconnection() {
    if (role == 0)
        socket.send({"type":"leave", "role":"host", "name": username});
    else
        socket.send({"type":"leave", "role":"guest", "name": username});
}

// Called when the user clicks the join/start button, this function happens regardless of if they are a host or a guest
function session_begin() {
    // Checks which radio button is selected and makes the user a host if desired
    if (document.getElementById("host_radio").checked == true) {
        role = 0;
    }

    // Sets the username variable
    username = document.getElementById("username_input").value;

    // Connects to websockets
    socket = io.connect();

    // Hides the form element
    document.getElementById("form").style.display = "none";

    // Reports disconnection to the server before the tab is fully closed
    window.addEventListener("beforeunload", ReportDisconnection);
    window.addEventListener("unload", ReportDisconnection);

    // Hides the "session closed by the host" message
    document.getElementById("session-ended").style.display = "none";

    // Hides the error message (if an error was previously shown)
    document.getElementById("error-display").style.display = "none";

    // If the user is a host
    if (role == 0) {
        StartSession();
    }
    // If the user is a guest
    else {
        JoinSession();
    }
}

// Called when the host creates a new session
function StartSession() {
    // Shows the loading message
    document.getElementById("creating-session").style.display = "initial";

    // Tells the webserver the host's username
    socket.send({"type":"join","role":"host","name":username});

    // Handle recieving messages from the server
    socket.addEventListener('message', HostMessageHandler);
}

// Handles messages sent from the server to the host
function HostMessageHandler(event) {
    // If a new guest joined, send them the data of the current state
    if (event["type"] == "guest_joined") {
        SetData();
    }
    // Handles responses from the server about a previously sent host request
    else if (event["type"] == "host_request_response") {
        // Hides the loading message
        document.getElementById("creating-session").style.display = "none";

        // If the request was denied
        if (event["value"] == false) {
            // Close the websocket
            socket.close();

            // Re-show the form
            document.getElementById("form").style.display = "initial";

            // Show the error message
            if (event["reason"] == "host_already_exists") {
                document.getElementById("error-display").innerHTML = "<br><br>Sorry, somebody is already hosting this session. Please join as a guest or try again later.<br><br>";
                document.getElementById("error-display").style.display = "initial";
            }
            else if (event["reason"] == "username_not_unique") {
                document.getElementById("error-display").innerHTML = "<br><br>Sorry, that username is already taken.<br><br>";
                document.getElementById("error-display").style.display = "initial";
            }
        }
        // If the request was approved
        else {
             // Shows the video player
            document.getElementById("video-container").style.display = "initial";

            // Shows the user list
            document.getElementById("users-list").style.display = "inline-block";

            // Shows the chat box
            document.getElementById("chat-div").style.display = "inline-block";

            // Shows the warning telling the host not to close the tab
            document.getElementById("host-notice").style.display = "initial";

            // Shows the buttons allowing the host to kick/promote users
            document.getElementById("host-user-control-buttons").style.display = "initial";

            // Sends data to the server whenever the host pauses/resumes/skips the video
            myVideo.on("play", SetData);
            myVideo.on("pause", SetData);
            myVideo.on("seeked", SetData);

           // Sends current data to the server
            SetData();

            // Sends data to the server every 10 seconds
            var intervalID = window.setInterval(SetData, 10000);
        }
    }
    // If the message contains the user list, update that
    else if (event["type"] == "user_data") {
        UpdateUserData(event);
    }
    // If a guest paused/played/skipped the video, apply that data.
    else if (event["type"] == "guest_data") {
        if (event["action"] == "play")
            myVideo.play();
        else if (event["action"] == "pause")
            myVideo.pause();
        else if (event["action"] == "seek")
            myVideo.currentTime(event["timestamp"]);
    }
    // If a chat message was sent, update the chat box
    else if (event["type"] == "chat") {
        UpdateChat(event);
    }
}

// Called when a guest joins a session
function JoinSession() {
    // Shows the loading message
    document.getElementById("joining-session").style.display = "initial";

    // Sends a join request to the server
    socket.send({"type":"join","role":"guest","name":username});

    // Handles recieving messages from the server
    socket.addEventListener('message', GuestMessageHandler);
}

// Handles messages sent from the server to the guest
function GuestMessageHandler(event) {
    // If the host left, leave the session
    if (event["type"] == "host_left") {
        // Re-show the join form
        document.getElementById("form").style.display = "initial";

        // Hide the video player
        document.getElementById("video-container").style.display = "none";

        // Stop the video playback
        myVideo.pause();

        // Show the message saying the session ended
        document.getElementById("session-ended").innerHTML = "The session was closed by the host.<br><br>";
        document.getElementById("session-ended").style.display = "initial";

        // Hide the chat
        document.getElementById("chat-div").style.display = "none";

        // Hide the user list
        document.getElementById("users-list").style.display = "none";

        // Close the websocket connection
        socket.close();
    }
    // Handle recieivng user data
    else if (event["type"] == "user_data") {
        UpdateUserData(event);
    }
    // Update the video player with data sent from the host
    else if (event["type"] == "player_data") {
        UpdatePlayer(JSON.parse(event["data"]));
    }
    // Handle being kicked
    else if (event["type"] == "kick_user") {
        if (username == event["user"]) {
            document.getElementById("form").style.display = "initial";
            document.getElementById("video-container").style.display = "none";
            myVideo.pause();
            document.getElementById("session-ended").style.display = "initial";
            document.getElementById("session-ended").innerHTML = "You were kicked from the session.<br><br>";
            document.getElementById("users-list").style.display = "none";
            document.getElementById("chat-div").style.display = "none";
            socket.send({"type":"leave", "role":"guest", "name": username});
            socket.close();
        }
    }
    // Handle recieving chat messages
    else if (event["type"] == "chat") {
        UpdateChat(event);
    }
    // Shows chat history to a user that joined a session late
    else if (event["type"] == "chat_history") {
        event["data"].forEach(message => UpdateChat(message));
    }
    // Handles responses from the server about a previously sent join request
    else if (event["type"] == "join_request_response") {
        // Hides the loading message
        document.getElementById("joining-session").style.display = "none";

        // If the request was denied
        if (event["value"] == false) {
            // Close the websocket
            socket.close();

            // Re-show the form
            document.getElementById("form").style.display = "initial";

            // Show the error message
            if (event["reason"] == "username_not_unique") {
                document.getElementById("error-display").innerHTML = "<br><br>Sorry, that username is already taken.<br><br>";
                document.getElementById("error-display").style.display = "initial";
            }
            else if (event["reason"] == "no_host") {
                document.getElementById("error-display").innerHTML = "<br><br>There is no host in this session. Please either join as the host or have someone else host the session.<br><br>";
                document.getElementById("error-display").style.display = "initial";
            }
            else if (event["reason"] == "username_too_long") {
                document.getElementById("error-display").innerHTML = "<br><br>Sorry, your username must be less than 20 characters.<br><br>";
                document.getElementById("error-display").style.display = "initial";
            }
            else if (event["reason"] == "username_special_characters") {
                document.getElementById("error-display").innerHTML = "<br><br>Sorry, your username cannot have the characters < or >.<br><br>";
                document.getElementById("error-display").style.display = "initial";
            }
            else if (event["reason"] == "username_blank") {
                document.getElementById("error-display").innerHTML = "<br><br>Sorry, your username cannot be blank.<br><br>";
                document.getElementById("error-display").style.display = "initial";
            }
        }
        // If the request was approved
        else {
            // Show the video player
            document.getElementById("video-container").style.display = "initial";

            // Show the user list
            document.getElementById("users-list").style.display = "inline-block";

            // Show the chat box
            document.getElementById("chat-div").style.display = "inline-block";

            // Sets up event handlers for pausing/playing/skipping
            myVideo.on("play", function () {
            if (updatingPlayer == false)
                    socket.send({"type":"guest_data", "action": "play", "timestamp": 0})
            });
            myVideo.on("pause", function () {
                if (updatingPlayer == false)
                    socket.send({"type":"guest_data", "action": "pause", "timestamp": 0})
            });
            myVideo.on("seeked", function () {
                if (updatingPlayer == false)
                    socket.send({"type":"guest_data", "action": "seek", "timestamp": myVideo.currentTime()})
            });
        }
    }
}

// Called by the guest and host; adds the given message to the chat
function UpdateChat(event) {
    // Emblem, used to make any messages sent by the host be bolded
    var emblem = "";
    if (event["role"] == 0) {
        emblem = " style='font-weight: bold;'"
    }

    // Adds the message to the chat box
    document.getElementById("chat-box").innerHTML += ("<br><option" + emblem + " class='username-object' value='" + event["message"] + "'>" + event["message"] + "</option>");

    // Scrolls to the bottom of the chat
    document.getElementById("chat-box").scrollTop = document.getElementById("chat-box").scrollHeight;
}

// Updates the user list
function UpdateUserData(event) {
    var userData = event["data"];

    // Removes all shown users
    document.getElementById("users-list-child").innerHTML = "";

    // Adds each user back to the list
    userData.forEach(function(element) {
        var host_style = "";
        var suffix = "";
        if (element["role"] == "host") {
            host_style = " style='font-weight: bold;'";
            suffix = " (Host)";
        }
        document.getElementById("users-list-child").innerHTML += ("<br><option" + host_style + " class='username-object' value='" + element["username"] + "'> - " + element["username"] + suffix + "</option>");
    });
}

// Called on page load
function initVideo() {
    // Gets a pointer to the video.js object
    myVideo = videojs('my-video');

    // Prevents the user from putting < and > in the username box
    document.getElementById("username_input").onkeypress = function(e) {
        if (e.which == 60 || e.which == 62) {
            e.preventDefault();
        }
    }

    // Lets the user press enter to join/start a session
    document.getElementById("username_input").onkeypress = function(e) {
        if (e.which == 13) {
            session_begin();
        }
    }

    // Lets the user press enter to send a chat message
    document.getElementById("chat-type").onkeypress = function(e) {
        if (e.which == 13) {
            sendChatMessage();
        }
    }

    // Pings the server to check if there already is a host
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            if (this.responseText == "false") {
                document.getElementById("host_radio").checked = true;
                document.getElementById("guest_radio").checked = false;
            }
        }
    }
    xmlhttp.open("GET", "/current-host-check", true);
    xmlhttp.send();
}

// Sends data to the server to be sent to guest users
function SetData() {
    // Creates a JSON string with the data
    var dataToSet = JSON.stringify({
        PlayerTimestamp: myVideo.currentTime(),
        Paused: myVideo.paused()
    });

    socket.send({"type":"host_data","action":"set","data":dataToSet});
}

// Sends a chat message
function sendChatMessage() {
    socket.send({'type':'chat', 'message': username + ': ' + document.getElementById('chat-type').value, 'role': role});
    document.getElementById('chat-type').value = '';
}

// Updates the video player with the specified data
function UpdatePlayer(PlayerData) {
    updatingPlayer = true;
    setTimeout(function() {updatingPlayer = false}, 1000);
    myVideo.currentTime(PlayerData["PlayerTimestamp"]);

    if (PlayerData["Paused"] == true) {
        myVideo.pause();
    } else {
        myVideo.play();
    }
}
