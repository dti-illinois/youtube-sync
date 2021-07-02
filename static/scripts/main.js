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
    var errors = "";

    if (!(new RegExp("^(?:https?:)?(?:\\/\\/)?(?:youtu\\.be\\/|(?:www\\.|m\\.)?youtube\\.com\\/(?:watch|v|embed)(?:\\.php)?(?:\\?.*v=|\\/))([a-zA-Z0-9\\_-]{7,15})(?:[\\?&][a-zA-Z0-9\\_-]+=[a-zA-Z0-9\\_-]+)*(?:[&\\/\\#].*)?$", "g").test(url))) {
        encounteredErrors = true;
        errors += "<br> - Video link is not a valid YouTube URL";
        document.getElementById("createSession-videoURL").classList.add("is-invalid");
    }
    if (!(new RegExp("^[a-zA-Z0-9_.-]*$", "g").test(name))) {
        encounteredErrors = true;
        errors += "<br> - Username contains invalid characters";
        document.getElementById("createSession-username").classList.add("is-invalid");
    }
    if (name.length < 1 || name.length > 20) {
        encounteredErrors = true;
        errors += "<br> - Username must be between 1 and 20 characters long";
        document.getElementById("createSession-username").classList.add("is-invalid");
    }

    if (encounteredErrors) {
        document.getElementById("createSession-errorMessage").style.display = "initial";
        document.getElementById("createSession-errorMessage").innerHTML = "Errors were encountered when creating your session:" + errors;
    }
    else {
        document.getElementById("createSessionSpinner").style.display = "initial";
    }

    //$('#modalCreateSession').hide();
    //$('.modal-backdrop').hide();
}

function JoinSession() {
    $('#modalJoinSession').hide();
    $('.modal-backdrop').hide();
}