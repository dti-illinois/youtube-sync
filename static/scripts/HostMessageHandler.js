function HostMessageHandler(message) {
    console.log("Received websockets message: " + JSON.stringify(message));

    if (message["type"] == "host_request_response") {
        // Request approved
        if (message["value"] == true) {
            $('#modalCreateSession').hide();
            $('.modal-backdrop').hide();
            videoJS.src({type: 'video/youtube', src: videoURL});
        }
        // Request denied
        else {
            document.getElementById("createSessionSpinner").style.display = "none";
            document.getElementById("createSession-username").disabled = false;
            document.getElementById("createSession-videoURL").disabled = false;
            document.getElementById("createSession-button").disabled = false;

            document.getElementById("createSession-errorMessage").style.display = "initial";
            document.getElementById("createSession-errorMessage").innerHTML = "An error occurred while creating your session.";
        }
    }
}