// Role of the user.
// 0 = host, 1 = guest
var role = 1;

var username, url;

// Called when the user clicks the join/start button, this function happens regardless of if they are a host or a guest
function session_begin() {
    // Shows the loading message
    document.getElementById("session-loading").style.display = "initial";

    // Checks which radio button is selected and makes the user a host if desired
    if (document.getElementById("host_radio").checked == true) {
        role = 0;
        url = document.getElementById('url_input').value;

        // Pings the server to send the video URL
        $.ajax({
            type: "POST" ,
            url: "/host-url-send",
            data: url,
            success: function(data) {
                finish_session_begin();
            },
            error: function(data) {
                if (data.responseText != undefined) {
                    alert("Error: " + data.responseText);
                }
            }
        });
    }
    else {
        finish_session_begin();
    }
}

function finish_session_begin() {
    // Sets the username variable
    username = document.getElementById("username_input").value;

    // Hides the "session closed by the host" message
    document.getElementById("session-ended").style.display = "none";

    // Hides the error message (if an error was previously shown)
    document.getElementById("error-display").style.display = "none";

    var url_args = "";
    if (role == 0) {
        url_args = "&url=" + url;
    }

    window.location = "video-player?username=" + username + "&role=" + role + url_args;
}

function initVideo() {
    if (document.getElementById("host_radio").checked == true) {
        HostBoxChecked();
    }

    // Prevents the user from putting <, >, (, and ) in the username box
    document.getElementById("username_input").addEventListener("keypress", function(e) {
        if (e.which == 60 || e.which == 62 || e.which == 40 || e.which == 41) {
            e.preventDefault();
        }
    });


    // Lets the user press enter to join/start a session
    document.getElementById("username_input").onkeypress = function(e) {
        if (e.which == 13) {
            session_begin();
        }
    }

    // Pings the server to check if there already is a host
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            if (this.responseText == "false") {
                document.getElementById("host_radio").checked = true;
                document.getElementById("guest_radio").checked = false;
                HostBoxChecked();
            }
        }
    }
    xmlhttp.open("GET", "/current-host-check", true);
    xmlhttp.send();
}

function HostBoxChecked() {
    document.getElementById('btnStartSession').innerHTML = 'Create Session';
    document.getElementById('url_input').style.display = 'initial';
    role = 0;

    if (document.getElementById('url_input').value == '') {
        document.getElementById('btnStartSession').disabled = true;
    }
}

function GuestBoxChecked() {
    document.getElementById('btnStartSession').innerHTML = 'Join Session';
    document.getElementById('url_input').style.display = 'none';
    role = 1;

    if (document.getElementById('username_input').value != '') {
        document.getElementById('btnStartSession').disabled = false;
    }
}