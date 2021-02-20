//#region Creating variables
    // username = the user's username
    // myVideo = the video player object
    // socket = the websocket object
    // updatingPlayer - used to prevent infinite loops
    // role - 0 = host, 1 = guest
    var username, myVideo, socket, updatingPlayer, role, url, initialTimestamp, initialPaused;
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
    // Connects to websockets
    socket = io.connect("http://127.0.0.1:5000");

    // Reports disconnection to the server before the tab is fully closed
    window.addEventListener("beforeunload", ReportDisconnection);
    window.addEventListener("unload", ReportDisconnection);

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
    socket.send({
        "type": "join",
        "role": "host",
        "name": username,
        "url": url
    });

    // Handle recieving messages from the server
    socket.addEventListener('message', HostMessageHandler);
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

// Called by the guest and host; adds the given message to the chat
function UpdateChat(event) {
    // Emblem, used to make any messages sent by the host be bolded
    var emblem = "";
    if (event["role"] == 0) {
        emblem = " style='font-weight: bold;'"
    }

    // Adds the message to the chat box
    document.getElementById("chat-box").innerHTML += ("<br><option" + emblem + " class='username-object'>[" + event["username"] + "] " + event["message"] + "</option>");

    // Scrolls to the bottom of the chat
    document.getElementById("chat-box").scrollTop = document.getElementById("chat-box").scrollHeight;
}

// Updates the user list
function UpdateUserData(event) {
    var userData = event["data"];

    console.log(userData);

    // Removes all shown users
    document.getElementById("users-list-child").innerHTML = "";

    for (let sid in userData) {
        var host_style = "";
        var suffix = "";

        if (userData[sid]["role"] == "host") {
            host_style = " style='font-weight: bold;'";
            suffix += " (Host)";
        }

        if (userData[sid]["username"] == username) {
            suffix += " (You)";
        }

        document.getElementById("users-list-child").innerHTML += ("<br><option" + host_style + " class='username-object' value='" + userData[sid]["username"] + "'> - " + userData[sid]["username"] + suffix + "</option>");
    }
}

// Called on page load
function initVideo() {
    username = getParams()["username"];
    role = getParams()["role"];

    // Gets a pointer to the video.js object
    myVideo = videojs('my-video');

    // Lets the user press enter to send a chat message
    document.getElementById("chat-type").onkeypress = function(e) {
        if (e.which == 13) {
            sendChatMessage();
        }
    }

    if (role == 0) {
        url = getParams()["url"];
        initialTimestamp = getParams()["PlayerTimestamp"];
        initialPaused = (getParams()["Paused"] == "true");

        myVideo.src({type: 'video/youtube', src: url});

        myVideo.play();
        myVideo.on("loadedmetadata", function() {
            myVideo.currentTime(initialTimestamp);
        });

        if (initialPaused) {
            myVideo.pause();
        }
    }

    session_begin();
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
    socket.send({'type':'chat', 'username': username, 'message': document.getElementById('chat-type').value, 'role': role});
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

function KickUser() {
    var selectedUser = document.getElementById('users-list-child').options[document.getElementById('users-list-child').selectedIndex].value;

    if (selectedUser != username) {
        socket.send({
            'type': 'kick_user',
            'user': selectedUser
        });
    }
    else {
        alert("Error: You cannot kick yourself");
    }
}

function PromoteToHost() {
    var selectedUser = document.getElementById('users-list-child').options[document.getElementById('users-list-child').selectedIndex].value;

    if (selectedUser != username) {
        socket.send({
            'type': 'promote_user',
            'user': selectedUser,
            'host_username': username,
            'video_state': {
                'PlayerTimestamp': myVideo.currentTime(),
                'Paused': myVideo.paused()
            }
        });
    }
    else {
        alert("Error: You cannot promote yourself to host");
    }
}

function ChangeVideoURL() {
    var newUrl = document.getElementById("new-url-type").value;
    myVideo.src({type: 'video/youtube', src: newUrl});
    socket.send({
        'type': 'change_video_url',
        'url': newUrl
    });
}

function RemoveChatMessage() {
    if (confirm("Are you sure you want to remove the selected chat message?")) {
        socket.send({
            'type': 'remove_chat_message',
            'message_index': document.getElementById('chat-box').selectedIndex,
            'message_content': document.getElementById('chat-box')[document.getElementById('chat-box').selectedIndex].innerHTML
        });
    }
}