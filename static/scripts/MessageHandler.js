// Handles messages sent from the server to the host
function HostMessageHandler(event) {
    switch (event["type"]) {
        // If a new guest joined, send them the data of the current state
        case "guest_joined":
            SetData();
            break;

        // Handles responses from the server about a previously sent host request
        case "host_request_response":
            // Hides the loading message
            document.getElementById("session-loading").style.display = "none";
            document.getElementById("session-loading-indicator").style.display = "none";

            // If the request was approved
            if (event["value"] == true) {
                HostRequestApproved(event);
            }

            // If the request was denied
            else {
                HostRequestDenied(event);
            }

            break;

        // If the message contains the user list, update that
        case "user_data":
            UpdateUserData(event);
            break;

        // If a guest paused/played/skipped the video, apply that data.
        case "guest_data":
            if (event["action"] == "play")
                myVideo.play();
            else if (event["action"] == "pause")
                myVideo.pause();
            else if (event["action"] == "seek")
                myVideo.currentTime(event["timestamp"]);

            break;

        // If a chat message was sent, update the chat box
        case "chat":
            UpdateChat(event);
            break;

        // Respond to a roll call
        case "roll_call":
            socket.send({"type": "roll_response", "role": HOST_ROLE, "name": username});
            break;

        case "remove_chat_message":
            document.getElementById('chat-box').remove(event["message_index"]);
            break;

        case "promote_user":
            window.location = "video-player?username=" + username + "&role=1";
    }
}

// Handles messages sent from the server to the guest
function GuestMessageHandler(event) {
    switch(event["type"]) {
        // If the host left, leave the session
        case "host_left":
            HostLeft();
            break;

        case "change_video_url":
            myVideo.src({type: 'video/youtube', src: event["url"]});
            break;

        case "remove_chat_message":
            document.getElementById('chat-box').remove(event["message_index"]);
            break;

        // Handle receiving user data
        case "user_data":
            UpdateUserData(event);
            break;

        // Update the video player with data sent from the host
        case "player_data":
            UpdatePlayer(JSON.parse(event["data"]));
            break;

        // Handle being kicked
        case "kick_user":
            if (username == event["user"]) {
                KickSelf();
            }
            break;

        // Handle receiving chat messages
        case "chat":
            UpdateChat(event);
            break;

        // Shows chat history to a user that joined a session late
        case "chat_history":
            event["data"].forEach(message => UpdateChat(message));
            break;

        // Respond to a roll call
        case "roll_call":
            socket.send({"type": "roll_response", "role": GUEST_ROLE, "name": username});
            break;

        // Handles responses from the server about a previously sent join request
        case "guest_request_response":
            // Hides the loading message
            document.getElementById("session-loading").style.display = "none";
            document.getElementById("session-loading-indicator").style.display = "none";

            // If the request was denied
            if (event["value"] == false) {
                JoinRequestDenied(event);
            }
            // If the request was approved
            else {
                JoinRequestApproved(event);
            }
            break;

        case "promote_user":
            if (event["user"] == username) {
                socket.send({"type":"leave", "role": GUEST_ROLE, "name": username});
                window.location = "video-player?username=" + username + "&role=0&url=" + encodeURIComponent(myVideo.src()) + "&PlayerTimestamp=" + event["video_state"]["PlayerTimestamp"] + "&Paused=" + event["video_state"]["Paused"];
            }
    }
}

// Called when a request to join the session was approved
function JoinRequestApproved(event) {
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

// Called when a request to join the session was denied
function JoinRequestDenied(event) {
    // Close the websocket
    socket.close();

    // Show the error message
    if (event["reason"] == "username_not_unique") {
        document.getElementById("error-display").innerHTML = "<br><br>Sorry, that username is already taken.<br><br>";
        document.getElementById("error-display").style.display = "initial";
        document.getElementById("return_after_error_button").style.display = "initial";
    }
    else if (event["reason"] == "no_host") {
        document.getElementById("error-display").innerHTML = "<br><br>There is no host in this session. Please either join as the host or have someone else host the session.<br><br>";
        document.getElementById("error-display").style.display = "initial";
        document.getElementById("return_after_error_button").style.display = "initial";
    }
    else if (event["reason"] == "username_too_long") {
        document.getElementById("error-display").innerHTML = "<br><br>Sorry, your username must be less than 20 characters.<br><br>";
        document.getElementById("error-display").style.display = "initial";
        document.getElementById("return_after_error_button").style.display = "initial";
    }
    else if (event["reason"] == "username_special_characters") {
        document.getElementById("error-display").innerHTML = "<br><br>Sorry, your username cannot have the characters <, >, (, or ).<br><br>";
        document.getElementById("error-display").style.display = "initial";
        document.getElementById("return_after_error_button").style.display = "initial";
    }
    else if (event["reason"] == "username_blank") {
        document.getElementById("error-display").innerHTML = "<br><br>Sorry, your username cannot be blank.<br><br>";
        document.getElementById("error-display").style.display = "initial";
        document.getElementById("return_after_error_button").style.display = "initial";
    }
}

// Called when a request to host a session was approved
function HostRequestApproved(event) {
     // Shows the video player
    document.getElementById("video-container").style.display = "initial";

    // Shows the user list
    document.getElementById("users-list").style.display = "inline-block";

    // Shows the chat box
    document.getElementById("chat-div").style.display = "inline-block";

    // Shows the video controls
    document.getElementById("video-controls-div").style.display = "inline-block";

    // Shows the warning telling the host not to close the tab
    document.getElementById("host-notice").style.display = "initial";

    // Shows the buttons allowing the host to kick/promote users
    document.getElementById("host-user-control-buttons").style.display = "initial";
    document.getElementById("host-chat-control-buttons").style.display = "initial";
    document.getElementById("chat-box").style.height = "60%";
    document.getElementById("users-list-child").style.height = "65%";

    myVideo.src({type: 'video/youtube', src: url});

    myVideo.play();
    setTimeout(function() {
        myVideo.currentTime(initialTimestamp);
        if (initialPaused) {
            myVideo.pause();
        }
        SetData();
    }, 2000);

    // Sends data to the server whenever the host pauses/resumes/skips the video
    myVideo.on("play", SetData);
    myVideo.on("pause", SetData);
    myVideo.on("seeked", SetData);

    myVideo.play();

    if (initialPaused != undefined && initialTimestamp != undefined) {
        if (initialPaused == true) {
            myVideo.pause();
        } else {
            myVideo.play();
        }

        myVideo.currentTime(initialTimestamp);
    }

   // Sends current data to the server
    SetData();

    // Sends data to the server every 10 seconds
    var intervalID = window.setInterval(SetData, 10000);
}

// Called when a request to host a session was denied
function HostRequestDenied(event) {
    // Close the websocket
    socket.close();

    // Re-show the form
    document.getElementById("form").style.display = "initial";

    // Show the error message
    if (event["reason"] == "host_already_exists") {
        document.getElementById("error-display").innerHTML = "<br><br>Sorry, somebody is already hosting this session. Please join as a guest or try again later.<br><br>";
        document.getElementById("error-display").style.display = "initial";
        document.getElementById("return_after_error_button").style.display = "initial";
    }
    else if (event["reason"] == "username_not_unique") {
        document.getElementById("error-display").innerHTML = "<br><br>Sorry, that username is already taken.<br><br>";
        document.getElementById("error-display").style.display = "initial";
        document.getElementById("return_after_error_button").style.display = "initial";
    }
    else if (event["reason"] == "username_special_characters") {
        document.getElementById("error-display").innerHTML = "<br><br>Sorry, your username cannot have the characters <, >, (, or ).<br><br>";
        document.getElementById("error-display").style.display = "initial";
        document.getElementById("return_after_error_button").style.display = "initial";
    }
    else if (event["reason"] == "username_too_long") {
        document.getElementById("error-display").innerHTML = "<br><br>Sorry, your username must be less than 25 characters.<br><br>";
        document.getElementById("error-display").style.display = "initial";
        document.getElementById("return_after_error_button").style.display = "initial";
    }
}

// Called when you get kicked
function KickSelf() {
    document.getElementById("form").style.display = "initial";
    document.getElementById("video-container").style.display = "none";
    myVideo.pause();
    document.getElementById("session-ended").style.display = "initial";
    document.getElementById("session-ended").innerHTML = "You were kicked from the session.<br><br>";
    document.getElementById("return_after_error_button").style.display = "initial";
    document.getElementById("users-list").style.display = "none";
    document.getElementById("chat-div").style.display = "none";
    socket.send({"type":"leave", "role": GUEST_ROLE, "name": username});
    socket.close();
}

// Called when the host leaves the session - resets the page
function HostLeft() {
    // Hide the video player
    document.getElementById("video-container").style.display = "none";

    // Stop the video playback
    myVideo.pause();

    // Show the message saying the session ended
    document.getElementById("session-ended").innerHTML = "The session was closed by the host.<br><br>";
    document.getElementById("session-ended").style.display = "initial";
    document.getElementById("return_after_error_button").style.display = "initial";

    // Hide the chat
    document.getElementById("chat-div").style.display = "none";

    // Hide the user list
    document.getElementById("users-list").style.display = "none";

    // Close the websocket connection
    socket.close();
}