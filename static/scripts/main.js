function initVideo() {
    if (invalidURL) {
        $('#modalInvalidURL').modal({backdrop: 'static', keyboard: false});
    }
    else if (sessionID != "") {
        $('#modalJoinSession').modal({backdrop: 'static', keyboard: false});
    }
    else {
        $('#modalCreateSession').modal({backdrop: 'static', keyboard: false});
    }
}

function CreateSession() {
    var name = document.getElementById("createSession-username").value;
    var url = document.getElementById("createSession-videoURL").value;

    // Reset error messages
    document.getElementById("createSession-errorMessage").style.display = "none";
    document.getElementById("createSession-username").classList.remove("is-invalid");
    document.getElementById("createSession-videoURL").classList.remove("is-invalid");

    var encounteredErrors = false;

    if (!ValidateText(name, "username")) {
        document.getElementById("createSession-errorMessage").style.display = "initial";
        document.getElementById("createSession-errorMessage").innerHTML = "Please enter a valid username and video URL.";
        document.getElementById("createSession-username").classList.add("is-invalid");
        encounteredErrors = true;
    }
    if (!ValidateText(url, "url")) {
        document.getElementById("createSession-errorMessage").style.display = "initial";
        document.getElementById("createSession-errorMessage").innerHTML = "Please enter a valid username and video URL.";
        document.getElementById("createSession-videoURL").classList.add("is-invalid");
        encounteredErrors = true;
    }

    if (!encounteredErrors) {
        document.getElementById("createSessionSpinner").style.display = "initial";
    }

    //$('#modalCreateSession').hide();
    //$('.modal-backdrop').hide();
}

function JoinSession() {
    $('#modalJoinSession').hide();
    $('.modal-backdrop').hide();
}

function ValidateText(text, type) {
    if (type == "username") {
        return (text != "");
    }
    else if (type == "url") {
        return (text != "");
    }
}